"""Unit tests for FocusModeController — focus state machine."""
import unittest

from uav_tracker.config import Config
from uav_tracker.tracking.focus_mode_controller import FocusModeController


def _cfg(**kw) -> Config:
    return Config(**kw)


class TestFocusModeControllerDisabled(unittest.TestCase):
    """LOCK_FOCUS_ONLY=False — update() must always return False, clear streaks."""

    def test_is_active_false_when_disabled(self):
        ctrl = FocusModeController(_cfg(LOCK_FOCUS_ONLY=False))
        self.assertFalse(ctrl.is_active())

    def test_update_returns_false_when_disabled(self):
        ctrl = FocusModeController(_cfg(LOCK_FOCUS_ONLY=False))
        self.assertFalse(ctrl.update(confirmed=True))
        self.assertFalse(ctrl.update(confirmed=False))

    def test_update_resets_streaks_when_disabled(self):
        ctrl = FocusModeController(_cfg(LOCK_FOCUS_ONLY=False))
        ctrl._enter_streak = 5
        ctrl._exit_streak = 3
        ctrl._active = True
        ctrl.update(confirmed=True)
        self.assertFalse(ctrl._active)
        self.assertEqual(ctrl._enter_streak, 0)
        self.assertEqual(ctrl._exit_streak, 0)


class TestFocusModeControllerNightDetector(unittest.TestCase):
    """should_run_night_detector path coverage."""

    def test_night_disabled_returns_false(self):
        ctrl = FocusModeController(_cfg(NIGHT_ENABLED=False))
        self.assertFalse(ctrl.should_run_night_detector(frames_since_primary=0))

    def test_disable_on_lock_while_active_returns_false(self):
        ctrl = FocusModeController(_cfg(
            LOCK_FOCUS_ONLY=True,
            NIGHT_ENABLED=True,
            DISABLE_NIGHT_ON_LOCK=True,
        ))
        ctrl._active = True
        self.assertFalse(ctrl.should_run_night_detector(frames_since_primary=0))

    def test_night_run_when_primary_seen_true_always_runs(self):
        ctrl = FocusModeController(_cfg(
            NIGHT_ENABLED=True,
            DISABLE_NIGHT_ON_LOCK=False,
            NIGHT_RUN_WHEN_PRIMARY_SEEN=True,
        ))
        self.assertTrue(ctrl.should_run_night_detector(frames_since_primary=0))
        self.assertTrue(ctrl.should_run_night_detector(frames_since_primary=999))

    def test_cooldown_suppresses_when_primary_recently_seen(self):
        ctrl = FocusModeController(_cfg(
            NIGHT_ENABLED=True,
            DISABLE_NIGHT_ON_LOCK=False,
            NIGHT_RUN_WHEN_PRIMARY_SEEN=False,
            NIGHT_PRIMARY_COOLDOWN=10,
        ))
        self.assertFalse(ctrl.should_run_night_detector(frames_since_primary=5))

    def test_cooldown_allows_when_primary_not_recently_seen(self):
        ctrl = FocusModeController(_cfg(
            NIGHT_ENABLED=True,
            DISABLE_NIGHT_ON_LOCK=False,
            NIGHT_RUN_WHEN_PRIMARY_SEEN=False,
            NIGHT_PRIMARY_COOLDOWN=10,
        ))
        self.assertTrue(ctrl.should_run_night_detector(frames_since_primary=15))


if __name__ == '__main__':
    unittest.main()
