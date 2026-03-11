"""Unit tests for TargetManager lock/ID policy and select_active behaviour.

Runs without cv2, ultralytics, or any camera hardware.
Usage:
    PYTHONPATH=src python3 -m unittest -v tests.test_target_manager_lock_policy
"""

import unittest

from uav_tracker.config import Config
from uav_tracker.tracking.target_manager import TargetManager, TrackedTarget


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _cfg(**overrides) -> Config:
    """Return a Config with production defaults, selectively overridden."""
    return Config(**overrides)


def _inject(
    mgr: TargetManager,
    tid: int,
    *,
    source: str = 'yolo',
    hit_streak: int = 1,
    drone_score: float = 0.5,
    conf: float = 0.5,
    cx: float = 100.0,
    cy: float = 100.0,
    cls_id: int = 0,
    lost_frames: int = 0,
) -> TrackedTarget:
    """Inject a TrackedTarget directly into mgr.targets."""
    bbox = (int(cx) - 10, int(cy) - 10, int(cx) + 10, int(cy) + 10)
    t = TrackedTarget(
        track_id=tid,
        bbox=bbox,
        raw_bbox=bbox,
        cx=cx,
        cy=cy,
        conf=conf,
        cls_id=cls_id,
        drone_score=drone_score,
        hit_streak=hit_streak,
        source=source,
        lost_frames=lost_frames,
    )
    mgr.targets[tid] = t
    return t


# ---------------------------------------------------------------------------
# Lock confirmation hysteresis
# ---------------------------------------------------------------------------

class TestLockConfirmation(unittest.TestCase):

    def test_lock_not_confirmed_with_insufficient_streak(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, hit_streak=4, drone_score=0.65, conf=0.8)
        mgr.active_id = 1
        self.assertFalse(mgr.has_confirmed_drone_lock())

    def test_lock_confirmed_when_all_criteria_met(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, hit_streak=5, drone_score=0.65, conf=0.8, lost_frames=0)
        mgr.active_id = 1
        self.assertTrue(mgr.has_confirmed_drone_lock())

    def test_lock_not_confirmed_when_lost_frames_exceed_grace(self):
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, hit_streak=5, drone_score=0.65, conf=0.8, lost_frames=3)
        mgr.active_id = 1
        self.assertFalse(mgr.has_confirmed_drone_lock())


# ---------------------------------------------------------------------------
# Active ID switch policy
# ---------------------------------------------------------------------------

class TestActiveSwitchPolicy(unittest.TestCase):

    def test_id_switch_blocked_in_strict_focus_mode(self):
        mgr = TargetManager(_cfg(ACTIVE_STRICT_LOCK_SWITCH=True, LOCK_FOCUS_ONLY=True))
        _inject(mgr, 1, hit_streak=5, drone_score=0.65, lost_frames=0)
        _inject(mgr, 2, cx=200.0)
        mgr.active_id = 1
        mgr._focus_mode = True
        switched = mgr._set_active_id(2)
        self.assertFalse(switched)
        self.assertEqual(mgr.active_id, 1)

    def test_id_switch_allowed_after_cooldown_expires(self):
        mgr = TargetManager(_cfg(ACTIVE_STRICT_LOCK_SWITCH=False))
        _inject(mgr, 1)
        _inject(mgr, 2, cx=200.0)
        mgr.active_id = 1
        mgr._active_switch_cooldown = 0
        switched = mgr._set_active_id(2)
        self.assertTrue(switched)
        self.assertEqual(mgr.active_id, 2)


# ---------------------------------------------------------------------------
# LOST / age_targets
# ---------------------------------------------------------------------------

class TestLostTransition(unittest.TestCase):

    def test_primary_target_removed_after_yolo_lost_max(self):
        cfg = _cfg()
        mgr = TargetManager(cfg)
        t = _inject(mgr, 1, hit_streak=3, drone_score=0.65)
        mgr.active_id = 1
        # Set lost_frames to threshold; one age_targets() call pushes it over
        t.lost_frames = cfg.YOLO_LOST_MAX
        mgr.age_targets(set())
        self.assertNotIn(1, mgr.targets)
        self.assertIsNone(mgr.active_id)


# ---------------------------------------------------------------------------
# Focus mode hysteresis
# ---------------------------------------------------------------------------

class TestFocusModeHysteresis(unittest.TestCase):

    def _confirmed_mgr(self) -> TargetManager:
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, hit_streak=5, drone_score=0.65, lost_frames=0)
        mgr.active_id = 1
        return mgr

    def test_focus_mode_enters_only_after_acquire_frames(self):
        mgr = self._confirmed_mgr()
        # First call: enter_streak=1, needs LOCK_MODE_ACQUIRE_FRAMES=2
        mgr.update_focus_mode()
        self.assertFalse(mgr.is_focus_mode())
        # Second call: enter_streak=2 >= 2 → enters focus
        mgr.update_focus_mode()
        self.assertTrue(mgr.is_focus_mode())

    def test_focus_mode_exits_only_after_release_frames(self):
        mgr = self._confirmed_mgr()
        # Enter focus mode (2 confirmed frames)
        for _ in range(2):
            mgr.update_focus_mode()
        self.assertTrue(mgr.is_focus_mode())
        # Degrade target to non-confirmed
        mgr.targets[1].hit_streak = 0
        # Five non-confirmed calls: exit_streak=5, needs LOCK_MODE_RELEASE_FRAMES=6
        for _ in range(5):
            mgr.update_focus_mode()
        self.assertTrue(mgr.is_focus_mode())
        # Sixth call: exit_streak=6 >= 6 → exits focus
        mgr.update_focus_mode()
        self.assertFalse(mgr.is_focus_mode())


# ---------------------------------------------------------------------------
# select_active policy  (TASK-20260311-004)
# ---------------------------------------------------------------------------

class TestSelectActivePolicy(unittest.TestCase):

    def test_select_active_primary_wins_over_aux(self):
        """Primary target (yolo, drone_score>=DRONE_REACQUIRE_SCORE_MIN) is selected
        over an aux (night) target when no active target is set."""
        mgr = TargetManager(_cfg())
        # Primary: score = 0 + 0.5*1.2 + min(4,3*0.35) + 2.8*0.60 = 3.33
        _inject(mgr, 1, source='yolo', drone_score=0.60, conf=0.5, hit_streak=3)
        # Aux: score = 0 + 0.5*1.2 + min(4,3*0.35) - 0.8 = 0.85
        _inject(mgr, 2, source='night', conf=0.5, hit_streak=3, cx=200.0)
        mgr.active_id = None
        mgr.select_active()
        self.assertEqual(mgr.active_id, 1)

    def test_select_active_early_return_when_active_present(self):
        """select_active() returns immediately without changing active_id when
        an active target already exists in targets."""
        mgr = TargetManager(_cfg())
        _inject(mgr, 1, source='yolo', drone_score=0.60, conf=0.5, hit_streak=3)
        # Target 2 has a strictly better score but must NOT win
        _inject(mgr, 2, source='yolo', drone_score=0.90, conf=0.9, hit_streak=5, cx=200.0)
        mgr.active_id = 1
        mgr.select_active()
        self.assertEqual(mgr.active_id, 1)

    def test_select_active_aux_activates_via_speed_gate(self):
        """An aux (night) target with speed > 1.0 satisfies the activation gate
        and becomes active even without a qualifying drone_score."""
        mgr = TargetManager(_cfg())
        t = _inject(mgr, 1, source='night', conf=0.4, hit_streak=1,
                    drone_score=0.3, cls_id=-1)
        t.speed = 1.5
        mgr.active_id = None
        mgr.select_active()
        self.assertEqual(mgr.active_id, 1)

    def test_select_active_weak_aux_not_activated(self):
        """An aux target with speed<=1.0 and no qualifying drone_score is NOT
        activated — active_id stays None."""
        mgr = TargetManager(_cfg())
        t = _inject(mgr, 1, source='night', conf=0.4, hit_streak=1,
                    drone_score=0.3, cls_id=-1)
        t.speed = 0.5
        mgr.active_id = None
        mgr.select_active()
        self.assertIsNone(mgr.active_id)


if __name__ == '__main__':
    unittest.main()
