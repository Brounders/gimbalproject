"""Unit tests for TargetManager lock/ID policy.

Tests cover contractual state transitions and counters only.
No runtime video or model inference is used.

Run:
    PYTHONPATH=src python3 -m unittest -q tests.test_target_manager_lock_policy
"""

import pathlib
import sys
import unittest
from collections import deque

_SRC = pathlib.Path(__file__).parent.parent / 'src'
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from uav_tracker.config import Config
from uav_tracker.tracking.target_manager import TargetManager, TrackedTarget


def _cfg(**overrides) -> Config:
    """Return a Config with test-specific field overrides."""
    cfg = Config()
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def _inject(
    manager: TargetManager,
    tid: int,
    *,
    hit_streak: int = 1,
    lost_frames: int = 0,
    drone_score: float = 0.70,
    cls_id: int = 0,
    conf: float = 0.80,
    source: str = 'yolo',
    cx: float = 100.0,
    cy: float = 100.0,
) -> TrackedTarget:
    """Inject a TrackedTarget directly into manager.targets for state setup."""
    t = TrackedTarget(
        track_id=tid,
        bbox=(int(cx) - 10, int(cy) - 10, int(cx) + 10, int(cy) + 10),
        raw_bbox=(int(cx) - 10, int(cy) - 10, int(cx) + 10, int(cy) + 10),
        cx=cx,
        cy=cy,
        conf=conf,
        cls_id=cls_id,
        drone_score=drone_score,
        hit_streak=hit_streak,
        lost_frames=lost_frames,
        source=source,
    )
    t.trail = deque([(int(cx), int(cy))], maxlen=30)
    manager.targets[tid] = t
    return t


# ---------------------------------------------------------------------------
# Scenario 1: Lock confirmation hysteresis
# ---------------------------------------------------------------------------

class TestLockConfirmation(unittest.TestCase):

    def test_lock_not_confirmed_with_insufficient_streak(self):
        """has_confirmed_drone_lock must be False when hit_streak < LOCK_CONFIRM_FRAMES."""
        cfg = _cfg(LOCK_CONFIRM_FRAMES=5, LOCK_LOST_GRACE=2, DRONE_LOCK_SCORE_MIN=0.62)
        mgr = TargetManager(cfg)
        _inject(mgr, 1, hit_streak=4, lost_frames=0, drone_score=0.75, cls_id=0)
        mgr.active_id = 1
        self.assertFalse(mgr.has_confirmed_drone_lock())

    def test_lock_confirmed_when_all_criteria_met(self):
        """has_confirmed_drone_lock must be True when streak, score and lost_frames are all within limits."""
        cfg = _cfg(LOCK_CONFIRM_FRAMES=5, LOCK_LOST_GRACE=2, DRONE_LOCK_SCORE_MIN=0.62)
        mgr = TargetManager(cfg)
        _inject(mgr, 1, hit_streak=5, lost_frames=0, drone_score=0.75, cls_id=0)
        mgr.active_id = 1
        self.assertTrue(mgr.has_confirmed_drone_lock())

    def test_lock_not_confirmed_when_lost_frames_exceed_grace(self):
        """has_confirmed_drone_lock must be False when lost_frames > LOCK_LOST_GRACE, even with a strong streak."""
        cfg = _cfg(LOCK_CONFIRM_FRAMES=3, LOCK_LOST_GRACE=2, DRONE_LOCK_SCORE_MIN=0.62)
        mgr = TargetManager(cfg)
        _inject(mgr, 1, hit_streak=10, lost_frames=3, drone_score=0.75, cls_id=0)
        mgr.active_id = 1
        self.assertFalse(mgr.has_confirmed_drone_lock())


# ---------------------------------------------------------------------------
# Scenario 2: Active ID switch cooldown and strict focus lock
# ---------------------------------------------------------------------------

class TestActiveIdSwitchPolicy(unittest.TestCase):

    def test_id_switch_blocked_in_strict_focus_mode(self):
        """ACTIVE_STRICT_LOCK_SWITCH must block switching to another ID while in focus mode and target is not lost."""
        cfg = _cfg(
            ACTIVE_STRICT_LOCK_SWITCH=True,
            LOCK_FOCUS_ONLY=True,
            ACTIVE_ID_SWITCH_ALLOW_IF_LOST_FRAMES=6,
            ACTIVE_ID_SWITCH_COOLDOWN_FRAMES=0,  # cooldown not the gating factor here
            LOCK_CONFIRM_FRAMES=1,
            LOCK_LOST_GRACE=2,
            DRONE_LOCK_SCORE_MIN=0.62,
        )
        mgr = TargetManager(cfg)
        _inject(mgr, 1, hit_streak=5, lost_frames=0, drone_score=0.75, cls_id=0)
        _inject(mgr, 2, hit_streak=5, lost_frames=0, drone_score=0.75, cls_id=0, cx=300.0, cy=300.0)
        mgr.active_id = 1
        mgr._focus_mode = True

        switched = mgr._set_active_id(2)

        self.assertFalse(switched)
        self.assertEqual(mgr.active_id, 1)

    def test_id_switch_allowed_after_cooldown_expires(self):
        """After cooldown reaches zero and focus mode is off, active ID switch must succeed."""
        cfg = _cfg(
            ACTIVE_STRICT_LOCK_SWITCH=False,
            LOCK_FOCUS_ONLY=False,
            ACTIVE_ID_SWITCH_COOLDOWN_FRAMES=2,
            ACTIVE_ID_SWITCH_ALLOW_IF_LOST_FRAMES=0,
        )
        mgr = TargetManager(cfg)
        _inject(mgr, 1, hit_streak=5, lost_frames=0)
        _inject(mgr, 2, hit_streak=5, lost_frames=0, cx=300.0, cy=300.0)
        mgr.active_id = 1
        mgr._active_switch_cooldown = 2

        # Switch must be blocked while cooldown is active
        self.assertFalse(mgr._set_active_id(2))
        self.assertEqual(mgr.active_id, 1)

        # Expire the cooldown
        mgr.frame_tick()
        mgr.frame_tick()

        # Switch must now succeed
        self.assertTrue(mgr._set_active_id(2))
        self.assertEqual(mgr.active_id, 2)


# ---------------------------------------------------------------------------
# Scenario 3: LOST transition — target expiry clears active_id
# ---------------------------------------------------------------------------

class TestTargetExpiry(unittest.TestCase):

    def test_primary_target_removed_after_yolo_lost_max(self):
        """Primary target must be deleted from targets and active_id cleared after YOLO_LOST_MAX frames without detection."""
        cfg = _cfg(YOLO_LOST_MAX=3)
        mgr = TargetManager(cfg)
        _inject(mgr, 1, hit_streak=10, lost_frames=0)
        mgr.active_id = 1

        for _ in range(4):  # 4 frames with no detections → exceeds YOLO_LOST_MAX=3
            mgr.age_targets(seen_ids=set())

        self.assertNotIn(1, mgr.targets)
        self.assertIsNone(mgr.active_id)


# ---------------------------------------------------------------------------
# Scenario 4: Focus mode hysteresis (enter and exit)
# ---------------------------------------------------------------------------

class TestFocusModeHysteresis(unittest.TestCase):

    def test_focus_mode_enters_only_after_acquire_frames(self):
        """Focus mode must not activate before LOCK_MODE_ACQUIRE_FRAMES consecutive confirmed frames."""
        cfg = _cfg(
            LOCK_FOCUS_ONLY=True,
            LOCK_MODE_ACQUIRE_FRAMES=3,
            LOCK_MODE_RELEASE_FRAMES=6,
            LOCK_CONFIRM_FRAMES=1,
            LOCK_LOST_GRACE=2,
            DRONE_LOCK_SCORE_MIN=0.62,
        )
        mgr = TargetManager(cfg)
        _inject(mgr, 1, hit_streak=5, lost_frames=0, drone_score=0.75, cls_id=0)
        mgr.active_id = 1

        mgr.update_focus_mode()  # frame 1
        self.assertFalse(mgr.is_focus_mode(), 'must not enter after 1 frame')

        mgr.update_focus_mode()  # frame 2
        self.assertFalse(mgr.is_focus_mode(), 'must not enter after 2 frames')

        mgr.update_focus_mode()  # frame 3 — threshold reached
        self.assertTrue(mgr.is_focus_mode(), 'must enter after 3 frames')

    def test_focus_mode_exits_only_after_release_frames(self):
        """Focus mode must persist for LOCK_MODE_RELEASE_FRAMES unconfirmed frames before exiting."""
        cfg = _cfg(
            LOCK_FOCUS_ONLY=True,
            LOCK_MODE_ACQUIRE_FRAMES=1,
            LOCK_MODE_RELEASE_FRAMES=3,
            LOCK_CONFIRM_FRAMES=1,
            LOCK_LOST_GRACE=2,
            DRONE_LOCK_SCORE_MIN=0.62,
        )
        mgr = TargetManager(cfg)
        _inject(mgr, 1, hit_streak=5, lost_frames=0, drone_score=0.75, cls_id=0)
        mgr.active_id = 1

        # Enter focus mode
        mgr.update_focus_mode()
        self.assertTrue(mgr.is_focus_mode())

        # Simulate target loss — lock no longer confirmed
        mgr.targets[1].hit_streak = 0
        mgr.targets[1].lost_frames = 10  # exceeds LOCK_LOST_GRACE

        mgr.update_focus_mode()  # unconfirmed frame 1 — still in focus
        self.assertTrue(mgr.is_focus_mode(), 'must stay in focus on frame 1')

        mgr.update_focus_mode()  # unconfirmed frame 2 — still in focus
        self.assertTrue(mgr.is_focus_mode(), 'must stay in focus on frame 2')

        mgr.update_focus_mode()  # unconfirmed frame 3 — exits focus
        self.assertFalse(mgr.is_focus_mode(), 'must exit focus on frame 3')


# ---------------------------------------------------------------------------
# Scenario 5: select_active() competition policy
# ---------------------------------------------------------------------------

class TestSelectActivePolicy(unittest.TestCase):

    def test_select_active_keeps_active_primary(self):
        """Active primary-цель (yolo) must stay when a stronger primary competitor appears.

        Verifies Phase-1 early-return: if active is already a primary source,
        select_active() returns immediately without re-scoring.
        """
        cfg = _cfg(
            ACTIVE_STRICT_LOCK_SWITCH=True,
            LOCK_FOCUS_ONLY=True,
            DRONE_REACQUIRE_SCORE_MIN=0.48,
            PREFER_CLASS_ID=0,
            NIGHT_CONFIRM=3,
            ACTIVE_ID_SWITCH_COOLDOWN_FRAMES=0,
        )
        mgr = TargetManager(cfg)
        _inject(mgr, 1, source='yolo', hit_streak=8, lost_frames=0, drone_score=0.72, conf=0.85)
        _inject(mgr, 2, source='yolo', hit_streak=12, lost_frames=0, drone_score=0.90, conf=0.95, cx=300.0)
        mgr.targets[2].speed = 2.5  # stronger competitor
        mgr.active_id = 1

        mgr.select_active()

        self.assertEqual(mgr.active_id, 1, 'active primary must not be displaced by a stronger primary')

    def test_select_active_switches_from_aux_to_primary(self):
        """Night/aux active target must be replaced by an eligible primary (yolo) when one appears.

        Verifies Phase-3: active is aux, a primary exists with drone_score >= DRONE_REACQUIRE_SCORE_MIN,
        so select_active() must promote the primary.
        """
        cfg = _cfg(
            ACTIVE_STRICT_LOCK_SWITCH=False,
            LOCK_FOCUS_ONLY=False,
            DRONE_REACQUIRE_SCORE_MIN=0.48,
            PREFER_CLASS_ID=0,
            NIGHT_CONFIRM=3,
            ACTIVE_ID_SWITCH_COOLDOWN_FRAMES=0,
        )
        mgr = TargetManager(cfg)
        _inject(mgr, 1, source='night', hit_streak=5, lost_frames=0, conf=0.35)
        _inject(mgr, 2, source='yolo', hit_streak=6, lost_frames=0, drone_score=0.70, conf=0.82, cx=300.0)
        mgr.targets[2].speed = 0.8  # speed > 0.5 satisfies activation condition
        mgr.active_id = 1

        mgr.select_active()

        self.assertEqual(mgr.active_id, 2, 'aux target must be replaced by primary when primary is eligible')

    def test_select_active_activates_aux_when_no_primary(self):
        """Aux target meeting quality threshold must be activated when no primary exists."""
        cfg = _cfg(
            NIGHT_CONFIRM=3,
            DRONE_REACQUIRE_SCORE_MIN=0.48,
            ACTIVE_STRICT_LOCK_SWITCH=False,
            LOCK_FOCUS_ONLY=False,
        )
        mgr = TargetManager(cfg)
        _inject(mgr, 1, source='night', hit_streak=4, lost_frames=0, conf=0.45)
        mgr.active_id = None

        mgr.select_active()

        self.assertEqual(mgr.active_id, 1, 'qualifying aux target must be activated when there is no primary')

    def test_select_active_rejects_weak_aux(self):
        """Aux target below both conf and speed thresholds must not be activated."""
        cfg = _cfg(
            NIGHT_CONFIRM=3,
            DRONE_REACQUIRE_SCORE_MIN=0.48,
            ACTIVE_STRICT_LOCK_SWITCH=False,
            LOCK_FOCUS_ONLY=False,
        )
        mgr = TargetManager(cfg)
        # conf=0.25 < 0.30 AND speed=1.0 < 1.2 → activation gate fails
        _inject(mgr, 1, source='night', hit_streak=4, lost_frames=0, conf=0.25)
        mgr.targets[1].speed = 1.0
        mgr.active_id = None

        mgr.select_active()

        self.assertIsNone(mgr.active_id, 'weak aux target must not be activated')

    def test_select_active_primary_vs_primary_higher_score_wins(self):
        """When active_id=None and two primary targets compete, the one with higher
        drone_score must become active (Phase-3 best-primary selection by primary_score).

        primary_score formula: speed + conf*1.6 + min(5, hit_streak*0.45) + 3.2*drone_score - lost_frames
        target A (drone_score=0.50): 0 + 0.80*1.6 + 3*0.45 + 3.2*0.50 = 0+1.28+1.35+1.60 = 4.23
        target B (drone_score=0.75): 0 + 0.80*1.6 + 3*0.45 + 3.2*0.75 = 0+1.28+1.35+2.40 = 5.03
        Both satisfy _is_drone_like_target (drone_score >= DRONE_REACQUIRE_SCORE_MIN=0.48),
        so B should win.
        """
        cfg = _cfg(
            DRONE_REACQUIRE_SCORE_MIN=0.48,
            DRONE_LOCK_SCORE_MIN=0.62,
            PREFER_CLASS_ID=0,
            ACTIVE_STRICT_LOCK_SWITCH=False,
            LOCK_FOCUS_ONLY=False,
            NIGHT_CONFIRM=3,
            ACTIVE_ID_SWITCH_COOLDOWN_FRAMES=0,
        )
        mgr = TargetManager(cfg)
        _inject(mgr, 1, source='yolo', hit_streak=3, lost_frames=0, drone_score=0.50, conf=0.80)
        _inject(mgr, 2, source='yolo', hit_streak=3, lost_frames=0, drone_score=0.75, conf=0.80, cx=200.0)
        mgr.active_id = None

        mgr.select_active()

        self.assertEqual(mgr.active_id, 2, 'primary with higher drone_score must win free-switch competition')

    def test_select_active_primary_vs_primary_speed_breaks_tie(self):
        """When two primary targets have equal drone_score but one has higher speed,
        the faster one wins (speed contributes directly to primary_score).
        """
        cfg = _cfg(
            DRONE_REACQUIRE_SCORE_MIN=0.48,
            PREFER_CLASS_ID=0,
            ACTIVE_STRICT_LOCK_SWITCH=False,
            LOCK_FOCUS_ONLY=False,
            NIGHT_CONFIRM=3,
            ACTIVE_ID_SWITCH_COOLDOWN_FRAMES=0,
        )
        mgr = TargetManager(cfg)
        _inject(mgr, 1, source='yolo', hit_streak=3, lost_frames=0, drone_score=0.60, conf=0.80)
        _inject(mgr, 2, source='yolo', hit_streak=3, lost_frames=0, drone_score=0.60, conf=0.80, cx=200.0)
        mgr.targets[2].speed = 1.5   # same drone_score, but faster → higher primary_score
        mgr.active_id = None

        mgr.select_active()

        self.assertEqual(mgr.active_id, 2, 'primary with higher speed must win when drone_score is equal')


if __name__ == '__main__':
    unittest.main()
