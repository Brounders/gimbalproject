"""Coverage finalization tests (T10).

Targets remaining uncovered branches in config.py, tracking_state_machine.py,
and runtime/base.py.  Hardware-free.
"""
import unittest

from uav_tracker.config import Config, RuntimeConfigView
from uav_tracker.tracking.tracking_state_machine import TrackingState, TrackingStateMachine


# ---------------------------------------------------------------------------
# Config.__post_init__ — remaining branches
# ---------------------------------------------------------------------------

class TestConfigValidationRemaining(unittest.TestCase):

    def test_alpha_field_below_zero_raises(self):
        with self.assertRaises(ValueError):
            Config(SMOOTH_ALPHA=-0.1)

    def test_alpha_field_above_one_raises(self):
        with self.assertRaises(ValueError):
            Config(SMOOTH_ALPHA=1.5)

    def test_lock_lost_grace_negative_raises(self):
        with self.assertRaises(ValueError):
            Config(LOCK_LOST_GRACE=-1)

    def test_lock_lost_grace_zero_is_valid(self):
        cfg = Config(LOCK_LOST_GRACE=0)
        self.assertEqual(cfg.LOCK_LOST_GRACE, 0)

    def test_velocity_alpha_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            Config(VELOCITY_ALPHA=2.0)

    def test_confidence_ema_alpha_zero_is_valid(self):
        cfg = Config(CONFIDENCE_EMA_ALPHA=0.0)
        self.assertAlmostEqual(cfg.CONFIDENCE_EMA_ALPHA, 0.0)

    def test_class_ema_alpha_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            Config(CLASS_EMA_ALPHA=-0.5)


# ---------------------------------------------------------------------------
# TrackingStateMachine — LOST → TRACK fast-reacquire path (line 79)
# ---------------------------------------------------------------------------

class TestStateMachineLostToTrackFast(unittest.TestCase):
    """LOST state can transition directly to TRACK when target reappears
    quickly enough (the acquire_frames streak condition on line 79).
    """

    def test_lost_reacquires_after_brief_gap(self):
        cfg = Config(TRACK_STATE_ACQUIRE_FRAMES=2, TRACK_STATE_LOST_FRAMES=4,
                     TRACK_STATE_RESET_FRAMES=20, LOCK_LOST_GRACE=0)
        sm = TrackingStateMachine(cfg)
        # Build up to TRACK
        for _ in range(3):
            sm.update(0)
        self.assertEqual(sm.state, TrackingState.TRACK)
        # One missing frame → LOST not yet triggered (need 4)
        sm.update(None)
        self.assertEqual(sm.state, TrackingState.TRACK)
        # 4 missing frames → LOST
        for _ in range(3):
            sm.update(None)
        self.assertEqual(sm.state, TrackingState.LOST)
        # Reappear for acquire_frames consecutive frames → TRACK directly from LOST
        for _ in range(2):
            sm.update(0)
        self.assertEqual(sm.state, TrackingState.TRACK)

    def test_display_hold_expires_and_applies_downgrade(self):
        """After DISPLAY_STATE_HOLD_FRAMES downgrades, display_state finally syncs."""
        cfg = Config(DISPLAY_STATE_HOLD_FRAMES=2, TRACK_STATE_ACQUIRE_FRAMES=2,
                     TRACK_STATE_LOST_FRAMES=2, TRACK_STATE_RESET_FRAMES=20,
                     LOCK_LOST_GRACE=0)
        sm = TrackingStateMachine(cfg)
        # Get to TRACK
        for _ in range(3):
            sm.update(0)
            sm.update_display()
        self.assertEqual(sm.display_state, TrackingState.TRACK)
        # Drop to LOST
        for _ in range(2):
            sm.update(None)
        sm.update_display()  # hold frame 1 — still TRACK in display
        self.assertEqual(sm.display_state, TrackingState.TRACK)
        sm.update_display()  # hold frame 2 — expires, display drops
        self.assertEqual(sm.display_state, TrackingState.LOST)


# ---------------------------------------------------------------------------
# RuntimeConfigView — all 13 fields round-trip
# ---------------------------------------------------------------------------

class TestRuntimeConfigViewAllFields(unittest.TestCase):

    def test_all_fields_present(self):
        cfg = Config()
        view = RuntimeConfigView.from_config(cfg)
        fields = [
            'CONF_THRESH', 'IMG_SIZE', 'DEVICE', 'ADAPTIVE_SCAN_ENABLED',
            'GLOBAL_SCAN_INTERVAL', 'LOCK_TRACKER_ENABLED', 'LOCK_CONFIRM_FRAMES',
            'NIGHT_ENABLED', 'NIGHT_MOT_THRESH', 'NIGHT_DIFF_THRESH',
            'ROI_ASSIST_ENABLED', 'DRONE_LOCK_SCORE_MIN', 'BUDGET_ENABLED',
        ]
        for f in fields:
            self.assertEqual(getattr(view, f), getattr(cfg, f), msg=f"Field {f} mismatch")


if __name__ == '__main__':
    unittest.main()
