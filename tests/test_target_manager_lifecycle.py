"""Unit tests for TargetManager lifecycle: update_from_yolo, update_from_night, age_targets.

Covers target creation, update, focus-mode filtering, overlap suppression,
aging counters, TTL expiry, and active_id cleanup on target death.
Runs without cv2, ultralytics, or hardware.

Usage:
    PYTHONPATH=src python3 -m unittest -v tests.test_target_manager_lifecycle
"""

import unittest

from uav_tracker.config import Config
from uav_tracker.runtime.base import Detection
from uav_tracker.tracking.target_manager import TargetManager, TrackedTarget


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cfg(**overrides) -> Config:
    return Config(**overrides)


def _det(
    tid: int,
    cx: float = 100.0,
    cy: float = 100.0,
    *,
    w: float = 40.0,
    h: float = 30.0,
    conf: float = 0.70,
    cls_id: int = 0,
    source: str = 'yolo',
) -> Detection:
    x1, y1 = int(cx - w / 2), int(cy - h / 2)
    x2, y2 = int(cx + w / 2), int(cy + h / 2)
    return Detection(bbox=(x1, y1, x2, y2), conf=conf, cls_id=cls_id,
                     cx=cx, cy=cy, source=source, track_id=tid)


def _night(
    cx: float = 200.0,
    cy: float = 150.0,
    *,
    w: float = 20.0,
    h: float = 20.0,
    conf: float = 0.0,
    cls_id: int = -1,
) -> dict:
    x1, y1 = int(cx - w / 2), int(cy - h / 2)
    x2, y2 = int(cx + w / 2), int(cy + h / 2)
    return {'bbox': (x1, y1, x2, y2), 'cx': cx, 'cy': cy, 'conf': conf, 'cls_id': cls_id}


def _inject(mgr: TargetManager, tid: int, *, cx: float = 100.0, cy: float = 100.0,
            w: float = 40.0, h: float = 30.0, source: str = 'yolo',
            hit_streak: int = 1, lost_frames: int = 0,
            drone_score: float = 0.65, conf: float = 0.7) -> TrackedTarget:
    """Directly insert a TrackedTarget into mgr.targets without going through update_from_yolo."""
    x1, y1 = int(cx - w / 2), int(cy - h / 2)
    x2, y2 = int(cx + w / 2), int(cy + h / 2)
    bbox = (x1, y1, x2, y2)
    t = TrackedTarget(
        track_id=tid, bbox=bbox, raw_bbox=bbox,
        cx=cx, cy=cy, conf=conf, cls_id=0,
        drone_score=drone_score, hit_streak=hit_streak,
        lost_frames=lost_frames, source=source,
    )
    mgr.targets[tid] = t
    return t


# ---------------------------------------------------------------------------
# update_from_yolo — basic creation and update
# ---------------------------------------------------------------------------

class TestUpdateFromYoloBasic(unittest.TestCase):

    def test_empty_detections_leaves_targets_unchanged(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1)
        seen = mgr.update_from_yolo([])
        self.assertEqual(seen, set())
        self.assertIn(1, mgr.targets)

    def test_new_detection_creates_target(self):
        mgr = TargetManager(_cfg())
        seen = mgr.update_from_yolo([_det(tid=1, cx=100.0, cy=80.0)])
        self.assertIn(1, mgr.targets)
        self.assertIn(1, seen)

    def test_new_target_has_hit_streak_one(self):
        mgr = TargetManager(_cfg())
        mgr.update_from_yolo([_det(tid=1)])
        self.assertEqual(mgr.targets[1].hit_streak, 1)

    def test_new_target_has_zero_lost_frames(self):
        mgr = TargetManager(_cfg())
        mgr.update_from_yolo([_det(tid=1)])
        self.assertEqual(mgr.targets[1].lost_frames, 0)

    def test_new_target_source_is_yolo(self):
        mgr = TargetManager(_cfg())
        mgr.update_from_yolo([_det(tid=1, source='yolo')])
        self.assertEqual(mgr.targets[1].source, 'yolo')

    def test_detection_with_none_track_id_is_skipped(self):
        mgr = TargetManager(_cfg())
        det = _det(tid=1)
        det.track_id = None
        seen = mgr.update_from_yolo([det])
        self.assertEqual(seen, set())
        self.assertEqual(len(mgr.targets), 0)

    def test_existing_target_updates_hit_streak(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, hit_streak=3)
        mgr.update_from_yolo([_det(tid=1)])
        self.assertEqual(mgr.targets[1].hit_streak, 4)

    def test_existing_target_resets_lost_frames(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, lost_frames=5)
        mgr.update_from_yolo([_det(tid=1)])
        self.assertEqual(mgr.targets[1].lost_frames, 0)

    def test_multiple_detections_all_added(self):
        mgr = TargetManager(_cfg())
        dets = [_det(tid=i, cx=float(i * 100)) for i in range(1, 4)]
        seen = mgr.update_from_yolo(dets)
        self.assertEqual(seen, {1, 2, 3})
        self.assertEqual(len(mgr.targets), 3)

    def test_returns_seen_ids_set(self):
        mgr = TargetManager(_cfg())
        seen = mgr.update_from_yolo([_det(tid=7), _det(tid=8, cx=300.0)])
        self.assertIsInstance(seen, set)
        self.assertEqual(seen, {7, 8})

    def test_prefer_class_target_gets_high_drone_score(self):
        """New detection with PREFER_CLASS_ID gets initial drone_score=0.70."""
        cfg = _cfg(PREFER_CLASS_ID=0)
        mgr = TargetManager(cfg)
        mgr.update_from_yolo([_det(tid=1, cls_id=0)])
        self.assertAlmostEqual(mgr.targets[1].drone_score, 0.70)

    def test_non_preferred_class_gets_lower_drone_score(self):
        """New detection with non-preferred class_id gets initial drone_score=0.30."""
        cfg = _cfg(PREFER_CLASS_ID=0)
        mgr = TargetManager(cfg)
        mgr.update_from_yolo([_det(tid=1, cls_id=1)])
        self.assertAlmostEqual(mgr.targets[1].drone_score, 0.30)


# ---------------------------------------------------------------------------
# update_from_yolo — focus mode filtering
# ---------------------------------------------------------------------------

class TestUpdateFromYoloFocusMode(unittest.TestCase):

    def _focused_mgr(self) -> TargetManager:
        """TargetManager in focus mode with active_id=1."""
        mgr = TargetManager(_cfg(LOCK_FOCUS_ONLY=True, LOCK_REACQUIRE_DIST=120))
        _inject(mgr, 1, cx=100.0, cy=100.0, drone_score=0.65)
        mgr.active_id = 1
        mgr._focus_mode = True
        return mgr

    def test_active_box_accepted_in_focus_mode(self):
        """Active target tid is always accepted in focus mode."""
        mgr = self._focused_mgr()
        seen = mgr.update_from_yolo([_det(tid=1, cx=100.0, cy=100.0)])
        self.assertIn(1, seen)

    def test_distant_non_active_box_filtered_in_focus_mode(self):
        """Detection far from active target and not preferred class is filtered."""
        mgr = self._focused_mgr()
        # tid=99 is far away (>LOCK_REACQUIRE_DIST) and non-preferred class
        seen = mgr.update_from_yolo([
            _det(tid=99, cx=5000.0, cy=5000.0, cls_id=99),
        ])
        self.assertNotIn(99, seen)
        self.assertNotIn(99, mgr.targets)

    def test_no_focus_mode_accepts_all_detections(self):
        """With LOCK_FOCUS_ONLY=False, all tids pass through regardless of distance."""
        mgr = TargetManager(_cfg(LOCK_FOCUS_ONLY=False))
        _inject(mgr, 1, cx=100.0, cy=100.0)
        mgr.active_id = 1
        seen = mgr.update_from_yolo([
            _det(tid=1, cx=100.0, cy=100.0),
            _det(tid=2, cx=5000.0, cy=5000.0),
        ])
        self.assertIn(1, seen)
        self.assertIn(2, seen)


# ---------------------------------------------------------------------------
# update_from_night — basic creation
# ---------------------------------------------------------------------------

class TestUpdateFromNightBasic(unittest.TestCase):

    def test_basic_night_det_creates_target(self):
        mgr = TargetManager(_cfg())
        seen = mgr.update_from_night([_night(cx=200.0, cy=150.0)], primary_ids=set())
        self.assertEqual(len(seen), 1)
        tid = next(iter(seen))
        self.assertIn(tid, mgr.targets)

    def test_night_target_gets_aux_id(self):
        """Night targets receive IDs starting from _next_aux_id (>=9000)."""
        mgr = TargetManager(_cfg())
        seen = mgr.update_from_night([_night()], primary_ids=set())
        tid = next(iter(seen))
        self.assertGreaterEqual(tid, 9000)

    def test_night_target_source_is_night(self):
        mgr = TargetManager(_cfg())
        seen = mgr.update_from_night([_night()], primary_ids=set())
        tid = next(iter(seen))
        self.assertEqual(mgr.targets[tid].source, 'night')

    def test_multiple_night_dets_create_multiple_targets(self):
        mgr = TargetManager(_cfg())
        dets = [_night(cx=100.0, cy=100.0), _night(cx=500.0, cy=400.0)]
        seen = mgr.update_from_night(dets, primary_ids=set())
        self.assertEqual(len(seen), 2)

    def test_focus_mode_suppresses_night_updates(self):
        """Night detection is fully suppressed when in focus/lock mode."""
        mgr = TargetManager(_cfg(LOCK_FOCUS_ONLY=True))
        mgr._focus_mode = True
        seen = mgr.update_from_night([_night()], primary_ids=set())
        self.assertEqual(seen, set())
        self.assertEqual(len(mgr.targets), 0)

    def test_nearby_existing_night_track_is_reused(self):
        """Night detection near an existing night target reuses its ID (no new allocation)."""
        mgr = TargetManager(_cfg(NIGHT_TRACK_DIST=80))
        # Pre-existing night target at (200, 150)
        _inject(mgr, 9000, cx=200.0, cy=150.0, source='night')
        mgr._next_aux_id = 9001
        initial_count = len(mgr.targets)
        # Detection within NIGHT_TRACK_DIST
        seen = mgr.update_from_night([_night(cx=210.0, cy=155.0)], primary_ids=set())
        # No new target should have been created
        self.assertEqual(len(mgr.targets), initial_count)
        self.assertIn(9000, seen)

    def test_distant_night_det_gets_new_id(self):
        """Detection far from all existing tracks allocates a new aux ID."""
        mgr = TargetManager(_cfg(NIGHT_TRACK_DIST=40))
        _inject(mgr, 9000, cx=100.0, cy=100.0, source='night')
        mgr._next_aux_id = 9001
        seen = mgr.update_from_night([_night(cx=900.0, cy=900.0)], primary_ids=set())
        # A new id must have been allocated (not 9000)
        self.assertNotIn(9000, seen)
        new_ids = seen - {9000}
        self.assertEqual(len(new_ids), 1)
        new_id = next(iter(new_ids))
        self.assertGreaterEqual(new_id, 9001)


# ---------------------------------------------------------------------------
# update_from_night — overlap suppression
# ---------------------------------------------------------------------------

class TestUpdateFromNightOverlap(unittest.TestCase):

    def test_night_det_overlapping_primary_bbox_is_skipped(self):
        """Night detection that highly overlaps a YOLO primary bbox is discarded."""
        mgr = TargetManager(_cfg())
        # Inject a primary YOLO target with a known bbox
        _inject(mgr, 1, cx=100.0, cy=100.0, w=80.0, h=60.0, source='yolo')
        # Night detection inside the same region (will have IoU > 0.3)
        det = _night(cx=100.0, cy=100.0, w=60.0, h=50.0)
        seen = mgr.update_from_night([det], primary_ids={1})
        self.assertEqual(seen, set())

    def test_night_det_far_from_primary_is_accepted(self):
        """Night detection that does NOT overlap any primary bbox is kept."""
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, cx=100.0, cy=100.0, source='yolo')
        det = _night(cx=600.0, cy=500.0)
        seen = mgr.update_from_night([det], primary_ids={1})
        self.assertEqual(len(seen), 1)


# ---------------------------------------------------------------------------
# age_targets — counters and TTL expiry
# ---------------------------------------------------------------------------

class TestAgeTargetsCounters(unittest.TestCase):

    def test_seen_target_lost_frames_unchanged(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, lost_frames=0)
        mgr.age_targets(seen_ids={1})
        self.assertEqual(mgr.targets[1].lost_frames, 0)

    def test_unseen_target_lost_frames_increments(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, lost_frames=2)
        mgr.age_targets(seen_ids=set())
        self.assertEqual(mgr.targets[1].lost_frames, 3)

    def test_unseen_target_hit_streak_decrements(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, hit_streak=5)
        mgr.age_targets(seen_ids=set())
        self.assertEqual(mgr.targets[1].hit_streak, 4)

    def test_hit_streak_does_not_go_below_zero(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, hit_streak=0)
        mgr.age_targets(seen_ids=set())
        self.assertEqual(mgr.targets[1].hit_streak, 0)

    def test_multiple_unseen_targets_all_age(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, lost_frames=0)
        _inject(mgr, 2, lost_frames=1)
        mgr.age_targets(seen_ids=set())
        self.assertEqual(mgr.targets[1].lost_frames, 1)
        self.assertEqual(mgr.targets[2].lost_frames, 2)

    def test_seen_and_unseen_mixed(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, lost_frames=0)
        _inject(mgr, 2, lost_frames=0)
        mgr.age_targets(seen_ids={1})
        self.assertEqual(mgr.targets[1].lost_frames, 0)  # seen — no change
        self.assertEqual(mgr.targets[2].lost_frames, 1)  # unseen — increments


# ---------------------------------------------------------------------------
# age_targets — TTL expiry and deletion
# ---------------------------------------------------------------------------

class TestAgeTargetsExpiry(unittest.TestCase):

    def test_primary_target_deleted_after_yolo_lost_max(self):
        """YOLO target is removed once lost_frames exceeds YOLO_LOST_MAX."""
        cfg = _cfg(YOLO_LOST_MAX=3)
        mgr = TargetManager(cfg)
        _inject(mgr, 1, source='yolo', lost_frames=3)  # already at threshold
        mgr.age_targets(seen_ids=set())  # one more unseen → lost_frames=4 > 3
        self.assertNotIn(1, mgr.targets)

    def test_primary_target_survives_at_yolo_lost_max(self):
        """YOLO target at exactly YOLO_LOST_MAX is not yet deleted."""
        cfg = _cfg(YOLO_LOST_MAX=3)
        mgr = TargetManager(cfg)
        _inject(mgr, 1, source='yolo', lost_frames=2)  # after age → lost_frames=3 = max
        mgr.age_targets(seen_ids=set())
        self.assertIn(1, mgr.targets)

    def test_night_target_deleted_after_night_lost_max(self):
        """Night target uses NIGHT_LOST_MAX (shorter TTL than YOLO)."""
        cfg = _cfg(NIGHT_LOST_MAX=4)
        mgr = TargetManager(cfg)
        _inject(mgr, 9000, source='night', lost_frames=4)
        mgr.age_targets(seen_ids=set())  # lost_frames → 5 > 4
        self.assertNotIn(9000, mgr.targets)

    def test_night_target_uses_night_lost_max_not_yolo(self):
        """Night target must not survive as long as a primary YOLO target."""
        cfg = _cfg(YOLO_LOST_MAX=12, NIGHT_LOST_MAX=4)
        mgr = TargetManager(cfg)
        _inject(mgr, 9000, source='night', lost_frames=4)
        mgr.age_targets(seen_ids=set())
        # Night target should be deleted (lost_frames=5 > NIGHT_LOST_MAX=4)
        self.assertNotIn(9000, mgr.targets)
        # Confirm YOLO target with same count would survive
        mgr2 = TargetManager(cfg)
        _inject(mgr2, 1, source='yolo', lost_frames=4)
        mgr2.age_targets(seen_ids=set())
        self.assertIn(1, mgr2.targets)  # lost_frames=5 <= YOLO_LOST_MAX=12

    def test_active_id_cleared_when_active_target_dies(self):
        """If the active target is deleted by age_targets, active_id must become None."""
        cfg = _cfg(YOLO_LOST_MAX=2)
        mgr = TargetManager(cfg)
        _inject(mgr, 1, source='yolo', lost_frames=2)
        mgr.active_id = 1
        mgr.age_targets(seen_ids=set())
        self.assertNotIn(1, mgr.targets)
        self.assertIsNone(mgr.active_id)

    def test_non_active_target_deleted_does_not_clear_active_id(self):
        """Deleting a non-active target must not affect active_id."""
        cfg = _cfg(YOLO_LOST_MAX=2)
        mgr = TargetManager(cfg)
        _inject(mgr, 1, source='yolo', lost_frames=0)
        _inject(mgr, 2, source='yolo', lost_frames=2)
        mgr.active_id = 1
        mgr.age_targets(seen_ids=set())
        self.assertNotIn(2, mgr.targets)
        self.assertEqual(mgr.active_id, 1)  # must be intact

    def test_multiple_dead_targets_all_removed(self):
        cfg = _cfg(YOLO_LOST_MAX=2)
        mgr = TargetManager(cfg)
        for tid in (1, 2, 3):
            _inject(mgr, tid, source='yolo', lost_frames=2)
        mgr.age_targets(seen_ids=set())
        self.assertEqual(len(mgr.targets), 0)


if __name__ == '__main__':
    unittest.main()
