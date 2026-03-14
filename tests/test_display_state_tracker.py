"""Unit tests for display/display_state_tracker.py (A08 Stage 4 extraction).

Validates DisplayStateTracker: confidence EMA, reticle EMA + hold, bbox EMA + hold.
Runs without cv2, ultralytics, or hardware.

Usage:
    PYTHONPATH=src python3 -m unittest -v tests.test_display_state_tracker
"""

import unittest

from uav_tracker.config import Config
from uav_tracker.display.display_state_tracker import DisplayStateTracker
from uav_tracker.tracking.target_manager import TrackedTarget


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cfg(**overrides) -> Config:
    return Config(**overrides)


def _target(
    *,
    cx: float = 200.0,
    cy: float = 150.0,
    w: float = 40.0,
    h: float = 30.0,
    hit_streak: int = 5,
    conf: float = 0.75,
    lost_frames: int = 0,
    vx: float = 0.0,
    vy: float = 0.0,
) -> TrackedTarget:
    x1 = int(cx - w / 2)
    y1 = int(cy - h / 2)
    x2 = int(cx + w / 2)
    y2 = int(cy + h / 2)
    bbox = (x1, y1, x2, y2)
    return TrackedTarget(
        track_id=1,
        bbox=bbox,
        raw_bbox=bbox,
        cx=cx,
        cy=cy,
        conf=conf,
        hit_streak=hit_streak,
        lost_frames=lost_frames,
        vx=vx,
        vy=vy,
    )


# ---------------------------------------------------------------------------
# Confidence EMA
# ---------------------------------------------------------------------------

class TestConfidenceEMA(unittest.TestCase):

    def test_returns_zero_when_no_active(self):
        dst = DisplayStateTracker(_cfg())
        result = dst.update_confidence(None, 0.0, 0.0, 1)
        self.assertEqual(result, 0.0)

    def test_returns_positive_with_good_target(self):
        # frame_counter=1 triggers warmup path (<=3) so display_confidence updates immediately
        dst = DisplayStateTracker(_cfg(LOCK_CONFIRM_FRAMES=5))
        t = _target(hit_streak=5, conf=0.9)
        result = dst.update_confidence(t, 0.0, 0.0, 1)
        self.assertGreater(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_clamped_to_unit_interval(self):
        dst = DisplayStateTracker(_cfg())
        t = _target(hit_streak=100, conf=1.0)
        for i in range(20):
            result = dst.update_confidence(t, 1.0, float(i), i)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_ema_rises_over_frames(self):
        dst = DisplayStateTracker(_cfg(CONFIDENCE_EMA_ALPHA=0.5, CONFIDENCE_DISPLAY_UPDATE_SEC=0.0))
        t = _target(hit_streak=10, conf=0.9)
        first = dst.update_confidence(t, 0.8, 1.0, 1)
        for i in range(2, 20):
            later = dst.update_confidence(t, 0.8, float(i), i)
        self.assertGreater(later, first)

    def test_drops_to_zero_when_target_disappears(self):
        dst = DisplayStateTracker(_cfg(CONFIDENCE_EMA_ALPHA=0.9, CONFIDENCE_DISPLAY_UPDATE_SEC=0.0))
        t = _target(hit_streak=10, conf=0.9)
        for i in range(1, 15):
            dst.update_confidence(t, 0.8, float(i), i)
        # Now feed None — EMA should decay toward 0
        for i in range(15, 50):
            result = dst.update_confidence(None, 0.0, float(i), i)
        self.assertAlmostEqual(result, 0.0, places=2)

    def test_warmup_bypasses_periodic_hold(self):
        """First 3 frames always update display_confidence immediately."""
        dst = DisplayStateTracker(_cfg(CONFIDENCE_DISPLAY_UPDATE_SEC=999.0, CONFIDENCE_EMA_ALPHA=0.5))
        t = _target(hit_streak=5, conf=0.8)
        r1 = dst.update_confidence(t, 0.0, 0.0, 1)
        r2 = dst.update_confidence(t, 0.0, 0.0, 2)
        r3 = dst.update_confidence(t, 0.0, 0.0, 3)
        # All three should return > 0 despite long update period
        self.assertGreater(r1, 0.0)
        self.assertGreater(r2, 0.0)
        self.assertGreater(r3, 0.0)

    def test_lock_score_contributes_to_confidence(self):
        cfg = _cfg(CONFIDENCE_EMA_ALPHA=1.0, CONFIDENCE_DISPLAY_UPDATE_SEC=0.0)
        dst_low = DisplayStateTracker(cfg)
        dst_high = DisplayStateTracker(cfg)
        t = _target(hit_streak=1, conf=0.4)
        low = dst_low.update_confidence(t, 0.0, 1.0, 1)
        high = dst_high.update_confidence(t, 0.9, 1.0, 1)
        self.assertGreater(high, low)


# ---------------------------------------------------------------------------
# Reticle EMA + hold
# ---------------------------------------------------------------------------

class TestReticleEMA(unittest.TestCase):

    def test_returns_none_with_no_target(self):
        dst = DisplayStateTracker(_cfg())
        result = dst.update_reticle(None)
        self.assertIsNone(result)

    def test_returns_integer_coordinates(self):
        dst = DisplayStateTracker(_cfg())
        t = _target(cx=100.0, cy=80.0)
        result = dst.update_reticle(t)
        self.assertIsNotNone(result)
        self.assertIsInstance(result[0], int)
        self.assertIsInstance(result[1], int)

    def test_initial_position_matches_target(self):
        """First update: EMA init sets center exactly."""
        dst = DisplayStateTracker(_cfg(RETICLE_CENTER_ALPHA=1.0))
        t = _target(cx=200.0, cy=150.0)
        result = dst.update_reticle(t)
        self.assertEqual(result, (200, 150))

    def test_ema_smooths_position(self):
        """With alpha < 1, reticle should not jump immediately to new center."""
        dst = DisplayStateTracker(_cfg(RETICLE_CENTER_ALPHA=0.3))
        t_a = _target(cx=100.0, cy=100.0)
        dst.update_reticle(t_a)          # initialize
        t_b = _target(cx=300.0, cy=300.0)
        result = dst.update_reticle(t_b)  # one EMA step
        # Should be between 100 and 300
        self.assertGreater(result[0], 100)
        self.assertLess(result[0], 300)

    def test_holds_position_after_target_disappears(self):
        """Reticle stays for RETICLE_HOLD_FRAMES after target gone."""
        cfg = _cfg(RETICLE_HOLD_FRAMES=3, RETICLE_CENTER_ALPHA=1.0)
        dst = DisplayStateTracker(cfg)
        dst.update_reticle(_target(cx=100.0, cy=50.0))
        # First missing frame — still held
        result = dst.update_reticle(None)
        self.assertIsNotNone(result)

    def test_clears_after_hold_expires(self):
        """After RETICLE_HOLD_FRAMES missing frames, reticle → None."""
        cfg = _cfg(RETICLE_HOLD_FRAMES=2, RETICLE_CENTER_ALPHA=1.0)
        dst = DisplayStateTracker(cfg)
        dst.update_reticle(_target(cx=100.0, cy=50.0))
        dst.update_reticle(None)  # miss 1
        dst.update_reticle(None)  # miss 2 → threshold
        result = dst.update_reticle(None)  # miss 3 → should clear
        self.assertIsNone(result)

    def test_reticle_recovers_after_gap(self):
        """Reticle reinitialises when target reappears after clearing."""
        cfg = _cfg(RETICLE_HOLD_FRAMES=1, RETICLE_CENTER_ALPHA=1.0)
        dst = DisplayStateTracker(cfg)
        dst.update_reticle(_target(cx=100.0, cy=100.0))
        dst.update_reticle(None)
        dst.update_reticle(None)  # cleared
        result = dst.update_reticle(_target(cx=500.0, cy=400.0))
        self.assertEqual(result, (500, 400))


# ---------------------------------------------------------------------------
# Smooth bbox EMA + hold
# ---------------------------------------------------------------------------

class TestSmoothBbox(unittest.TestCase):

    def test_returns_none_with_no_target(self):
        dst = DisplayStateTracker(_cfg())
        result = dst.update_smooth_bbox(None)
        self.assertIsNone(result)

    def test_returns_4_int_tuple_when_active(self):
        dst = DisplayStateTracker(_cfg())
        result = dst.update_smooth_bbox(_target(cx=100.0, cy=80.0, w=40.0, h=30.0))
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        for v in result:
            self.assertIsInstance(v, int)

    def test_initial_bbox_matches_target(self):
        """alpha=1.0: first EMA step snaps to target bbox exactly."""
        cfg = _cfg(SMOOTH_BBOX_ALPHA=1.0, SMOOTH_BBOX_SIZE_ALPHA=1.0)
        dst = DisplayStateTracker(cfg)
        t = _target(cx=100.0, cy=80.0, w=40.0, h=30.0)
        x1, y1, x2, y2 = dst.update_smooth_bbox(t)
        self.assertEqual(x1, 80)   # cx - w/2 = 100-20
        self.assertEqual(y1, 65)   # cy - h/2 = 80-15
        self.assertEqual(x2, 120)  # cx + w/2 = 100+20
        self.assertEqual(y2, 95)   # cy + h/2 = 80+15

    def test_position_ema_smooths_movement(self):
        """Bbox center should not jump instantly to new position."""
        cfg = _cfg(SMOOTH_BBOX_ALPHA=0.3, SMOOTH_BBOX_SIZE_ALPHA=0.3)
        dst = DisplayStateTracker(cfg)
        dst.update_smooth_bbox(_target(cx=100.0, cy=100.0, w=40.0, h=40.0))
        result = dst.update_smooth_bbox(_target(cx=200.0, cy=200.0, w=40.0, h=40.0))
        # x1 should be between (100-20) and (200-20)
        self.assertGreater(result[0], 80)
        self.assertLess(result[0], 180)

    def test_holds_bbox_after_dropout(self):
        """Bbox held for SMOOTH_BBOX_HOLD_FRAMES frames after target gone."""
        cfg = _cfg(SMOOTH_BBOX_HOLD_FRAMES=3)
        dst = DisplayStateTracker(cfg)
        dst.update_smooth_bbox(_target(cx=100.0, cy=80.0, w=40.0, h=30.0))
        result = dst.update_smooth_bbox(None)  # first miss
        self.assertIsNotNone(result)

    def test_bbox_clears_after_hold_expires(self):
        """After hold exhausted, update_smooth_bbox returns None."""
        cfg = _cfg(SMOOTH_BBOX_HOLD_FRAMES=2)
        dst = DisplayStateTracker(cfg)
        dst.update_smooth_bbox(_target())
        dst.update_smooth_bbox(None)  # miss 1
        dst.update_smooth_bbox(None)  # miss 2 → at threshold
        result = dst.update_smooth_bbox(None)  # miss 3 → cleared
        self.assertIsNone(result)

    def test_bbox_reinitialises_after_reappear(self):
        """After bbox cleared, reappearing target reinitialises EMA."""
        cfg = _cfg(SMOOTH_BBOX_HOLD_FRAMES=1,
                   SMOOTH_BBOX_ALPHA=1.0, SMOOTH_BBOX_SIZE_ALPHA=1.0)
        dst = DisplayStateTracker(cfg)
        dst.update_smooth_bbox(_target(cx=50.0, cy=50.0, w=20.0, h=20.0))
        dst.update_smooth_bbox(None)
        dst.update_smooth_bbox(None)  # cleared
        t = _target(cx=300.0, cy=200.0, w=60.0, h=40.0)
        x1, y1, x2, y2 = dst.update_smooth_bbox(t)
        self.assertEqual(x1, 270)  # 300-30
        self.assertEqual(y1, 180)  # 200-20


if __name__ == '__main__':
    unittest.main()
