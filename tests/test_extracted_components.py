"""Unit tests for A08 extracted components.

Tests BudgetController, ContinuityTracker, and TrackingStateMachine.
All tests run without cv2, ultralytics, or hardware.

Usage:
    PYTHONPATH=src python3 -m unittest -v tests.test_extracted_components
"""

import unittest

from uav_tracker.config import Config
from uav_tracker.budget_controller import BudgetController
from uav_tracker.continuity_tracker import ContinuityTracker
from uav_tracker.tracking.lock_event_tracker import LockEventTracker
from uav_tracker.tracking_state_machine import TrackingStateMachine


def _cfg(**overrides) -> Config:
    return Config(**overrides)


# ---------------------------------------------------------------------------
# BudgetController
# ---------------------------------------------------------------------------

class TestBudgetControllerInit(unittest.TestCase):
    def test_initial_state(self):
        bc = BudgetController(_cfg())
        self.assertEqual(bc.level, 0)
        self.assertAlmostEqual(bc.load_ema, 1.0)
        self.assertEqual(bc.last_frame_ms, 0.0)

    def test_budget_disabled_level_stays_zero(self):
        cfg = _cfg(BUDGET_ENABLED=False)
        bc = BudgetController(cfg)
        for _ in range(10):
            bc.update({'global': 100.0, 'lock': 0, 'local': 0, 'roi': 0, 'night': 0, 'draw': 0})
        self.assertEqual(bc.level, 0)
        self.assertAlmostEqual(bc.load_ema, 1.0)


class TestBudgetControllerLevelAdaptation(unittest.TestCase):
    def _high_load(self, bc, n=20):
        """Feed high load frames to push level up."""
        for _ in range(n):
            bc.update({'global': 9999.0, 'lock': 0, 'local': 0, 'roi': 0, 'night': 0, 'draw': 0})

    def _low_load(self, bc, n=30):
        """Feed low load frames to pull level down."""
        for _ in range(n):
            bc.update({'global': 0.1, 'lock': 0, 'local': 0, 'roi': 0, 'night': 0, 'draw': 0})

    def test_level_rises_under_high_load(self):
        cfg = _cfg(BUDGET_ENABLED=True, BUDGET_TARGET_FPS=30.0, BUDGET_LEVEL_MAX=3,
                   BUDGET_HIGH_LOAD=0.9, BUDGET_LOW_LOAD=0.5)
        bc = BudgetController(cfg)
        self._high_load(bc)
        self.assertGreater(bc.level, 0)

    def test_level_drops_under_low_load(self):
        cfg = _cfg(BUDGET_ENABLED=True, BUDGET_TARGET_FPS=30.0, BUDGET_LEVEL_MAX=3,
                   BUDGET_HIGH_LOAD=0.9, BUDGET_LOW_LOAD=0.5)
        bc = BudgetController(cfg)
        self._high_load(bc)
        peak_level = bc.level
        self.assertGreater(peak_level, 0)
        self._low_load(bc, n=100)  # EMA α=0.14, needs many frames to decay
        self.assertLess(bc.level, peak_level)

    def test_level_capped_at_max(self):
        cfg = _cfg(BUDGET_ENABLED=True, BUDGET_TARGET_FPS=30.0, BUDGET_LEVEL_MAX=2,
                   BUDGET_HIGH_LOAD=0.9, BUDGET_LOW_LOAD=0.5)
        bc = BudgetController(cfg)
        self._high_load(bc, n=50)
        self.assertLessEqual(bc.level, 2)


class TestBudgetControllerEffectiveIntervals(unittest.TestCase):
    def test_scan_interval_increases_with_level(self):
        cfg = _cfg(BUDGET_ENABLED=True, GLOBAL_SCAN_INTERVAL=5,
                   BUDGET_SCAN_INTERVAL_BOOST_PER_LEVEL=2)
        bc = BudgetController(cfg)
        base = bc.effective_global_scan_interval(0)
        bc.level = 2
        boosted = bc.effective_global_scan_interval(0)
        self.assertEqual(base, 5)
        self.assertEqual(boosted, 9)

    def test_roi_candidates_decrease_with_level(self):
        cfg = _cfg(BUDGET_ENABLED=True, ROI_MAX_CANDIDATES=5, BUDGET_ROI_MIN_CANDIDATES=1)
        bc = BudgetController(cfg)
        bc.level = 3
        result = bc.effective_roi_max_candidates()
        self.assertGreaterEqual(result, 1)
        self.assertLess(result, 5)

    def test_should_run_night_always_at_level0(self):
        bc = BudgetController(_cfg(BUDGET_ENABLED=True))
        bc.level = 0
        for i in range(10):
            self.assertTrue(bc.should_run_night(i))


# ---------------------------------------------------------------------------
# ContinuityTracker
# ---------------------------------------------------------------------------

class TestContinuityTrackerBasic(unittest.TestCase):
    def test_initial_score_no_frames(self):
        ct = ContinuityTracker()
        self.assertEqual(ct.score(), 0.0)

    def test_single_active_frame_score(self):
        ct = ContinuityTracker()
        ct.update(1)
        # 1 frame, no transitions yet → score=1.0 (active, no transitions)
        self.assertEqual(ct.score(), 1.0)

    def test_same_id_streak_score_1(self):
        ct = ContinuityTracker()
        for _ in range(5):
            ct.update(42)
        self.assertAlmostEqual(ct.score(), 1.0)

    def test_id_change_reduces_score(self):
        ct = ContinuityTracker()
        ct.update(1)
        ct.update(2)  # one transition, id changed
        self.assertLess(ct.score(), 1.0)
        self.assertEqual(ct.id_changes, 1)

    def test_presence_rate(self):
        ct = ContinuityTracker()
        ct.update(1)
        ct.update(1)
        ct.update(None)
        ct.update(1)
        # 3 active out of 4 frames
        self.assertAlmostEqual(ct.presence_rate(4), 0.75)

    def test_presence_rate_zero_frames(self):
        ct = ContinuityTracker()
        self.assertEqual(ct.presence_rate(0), 0.0)


class TestContinuityTrackerReacquire(unittest.TestCase):
    def test_median_reacquire_no_gaps(self):
        ct = ContinuityTracker()
        for _ in range(5):
            ct.update(1)
        self.assertEqual(ct.median_reacquire_frames(), 0.0)

    def test_median_reacquire_single_gap(self):
        ct = ContinuityTracker()
        ct.update(1)
        ct.update(None)
        ct.update(None)
        ct.update(None)
        ct.update(1)
        self.assertAlmostEqual(ct.median_reacquire_frames(), 3.0)

    def test_median_reacquire_multiple_gaps(self):
        ct = ContinuityTracker()
        # gap 2, gap 4
        ct.update(1)
        ct.update(None); ct.update(None)
        ct.update(1)
        ct.update(None); ct.update(None); ct.update(None); ct.update(None)
        ct.update(1)
        self.assertAlmostEqual(ct.median_reacquire_frames(), 3.0)


# ---------------------------------------------------------------------------
# TrackingStateMachine
# ---------------------------------------------------------------------------

class TestTrackingStateMachineTransitions(unittest.TestCase):
    def _cfg_fast(self):
        """Config with fast transitions for testing."""
        return _cfg(
            TRACK_STATE_ACQUIRE_FRAMES=2,
            TRACK_STATE_LOST_FRAMES=2,
            TRACK_STATE_RESET_FRAMES=4,
            LOCK_LOST_GRACE=1,
        )

    def test_initial_state(self):
        sm = TrackingStateMachine(self._cfg_fast())
        self.assertEqual(sm.state, 'SCAN')
        self.assertEqual(sm.display_state, 'SCAN')

    def test_scan_to_track(self):
        sm = TrackingStateMachine(self._cfg_fast())
        sm.update(0)  # present (lost_frames=0)
        self.assertEqual(sm.state, 'SCAN')
        sm.update(0)  # second presence → TRACK (acquire=2)
        self.assertEqual(sm.state, 'TRACK')

    def test_track_to_lost(self):
        sm = TrackingStateMachine(self._cfg_fast())
        sm.update(0); sm.update(0)  # → TRACK
        sm.update(None)
        self.assertEqual(sm.state, 'TRACK')  # first missing, not yet LOST
        sm.update(None)
        self.assertEqual(sm.state, 'LOST')

    def test_lost_to_scan(self):
        sm = TrackingStateMachine(self._cfg_fast())
        sm.update(0); sm.update(0)  # → TRACK
        sm.update(None); sm.update(None)  # → LOST
        sm.update(None); sm.update(None)  # reset_frames=4, so 4 missing total
        self.assertEqual(sm.state, 'SCAN')

    def test_lost_reacquire_to_track(self):
        sm = TrackingStateMachine(self._cfg_fast())
        sm.update(0); sm.update(0)  # → TRACK
        sm.update(None); sm.update(None)  # → LOST
        # Reacquire: 2 consecutive present frames while in LOST → TRACK
        sm.update(0); sm.update(0)
        self.assertEqual(sm.state, 'TRACK')

    def test_display_state_holds_on_downgrade(self):
        cfg = _cfg(
            TRACK_STATE_ACQUIRE_FRAMES=1,
            TRACK_STATE_LOST_FRAMES=1,
            TRACK_STATE_RESET_FRAMES=10,
            LOCK_LOST_GRACE=0,
            DISPLAY_STATE_HOLD_FRAMES=3,
        )
        sm = TrackingStateMachine(cfg)
        sm.update(0)  # → TRACK
        sm.update_display()
        self.assertEqual(sm.display_state, 'TRACK')
        sm.update(None)  # → LOST (real state)
        sm.update_display()
        # Display should still show TRACK (hold=3)
        self.assertEqual(sm.display_state, 'TRACK')

    def test_display_state_upgrades_immediately(self):
        cfg = _cfg(
            TRACK_STATE_ACQUIRE_FRAMES=1,
            TRACK_STATE_LOST_FRAMES=1,
            TRACK_STATE_RESET_FRAMES=10,
            LOCK_LOST_GRACE=0,
            DISPLAY_STATE_HOLD_FRAMES=5,
        )
        sm = TrackingStateMachine(cfg)
        sm.update(0)  # → TRACK immediately
        sm.update_display()
        # Upgrade SCAN→TRACK applied immediately
        self.assertEqual(sm.display_state, 'TRACK')


# ---------------------------------------------------------------------------
# LockEventTracker
# ---------------------------------------------------------------------------

class TestLockEventTrackerAcquire(unittest.TestCase):
    def test_initial_state(self):
        lt = LockEventTracker()
        self.assertEqual(lt.switch_count, 0)
        self.assertEqual(lt.event_counts['acquired'], 0)

    def test_acquire_event_on_first_focus(self):
        lt = LockEventTracker()
        events = lt.update(focus_mode=True, active_id=1)
        self.assertIn('LOCK_ACQUIRED id=1', events)
        self.assertEqual(lt.event_counts['acquired'], 1)

    def test_reacquire_after_lost(self):
        lt = LockEventTracker()
        lt.update(True, 1)   # acquired
        lt.update(False, None)  # lost
        events = lt.update(True, 1)
        self.assertIn('LOCK_REACQUIRED id=1', events)
        self.assertEqual(lt.event_counts['reacquired'], 1)

    def test_lost_event_on_focus_exit(self):
        lt = LockEventTracker()
        lt.update(True, 1)
        events = lt.update(False, None)
        self.assertIn('LOCK_LOST id=1', events)
        self.assertEqual(lt.event_counts['lost'], 1)

    def test_switch_event_on_id_change(self):
        lt = LockEventTracker()
        lt.update(True, 1)
        events = lt.update(True, 2)
        self.assertIn('LOCK_SWITCH 1->2', events)
        self.assertEqual(lt.switch_count, 1)
        self.assertEqual(lt.event_counts['switch'], 1)

    def test_no_switch_same_id(self):
        lt = LockEventTracker()
        lt.update(True, 1)
        events = lt.update(True, 1)
        self.assertFalse(any('SWITCH' in e for e in events))
        self.assertEqual(lt.switch_count, 0)

    def test_switches_per_min_warmup(self):
        lt = LockEventTracker()
        lt.update(True, 1)
        lt.update(True, 2)  # switch
        # elapsed < 5s → should return 0
        self.assertEqual(lt.switches_per_min(3.0), 0.0)

    def test_switches_per_min_calculation(self):
        lt = LockEventTracker()
        lt.update(True, 1)
        for i in range(2, 7):
            lt.update(True, i)  # 5 switches
        result = lt.switches_per_min(elapsed_sec=60.0)
        self.assertAlmostEqual(result, 5.0, places=1)

    def test_no_event_while_not_in_focus(self):
        lt = LockEventTracker()
        events = lt.update(False, None)
        events += lt.update(False, None)
        self.assertEqual(events, [])


if __name__ == '__main__':
    unittest.main()
