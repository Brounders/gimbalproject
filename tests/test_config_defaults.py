"""TD-003: Prove Config defaults match original magic numbers."""
import unittest
from uav_tracker.config import Config


class TestConfigDefaultValues(unittest.TestCase):
    """Prove Config defaults match original magic numbers."""

    def setUp(self):
        self.cfg = Config()

    # select_active() weights
    def test_select_active_conf_weight(self):
        self.assertEqual(self.cfg.SELECT_ACTIVE_CONF_WEIGHT, 1.2)

    def test_select_active_streak_cap(self):
        self.assertEqual(self.cfg.SELECT_ACTIVE_STREAK_CAP, 4.0)

    def test_select_active_streak_weight(self):
        self.assertEqual(self.cfg.SELECT_ACTIVE_STREAK_WEIGHT, 0.35)

    def test_select_active_lost_penalty(self):
        self.assertEqual(self.cfg.SELECT_ACTIVE_LOST_PENALTY, 0.8)

    def test_select_active_drone_weight(self):
        self.assertEqual(self.cfg.SELECT_ACTIVE_DRONE_WEIGHT, 2.8)

    def test_select_active_min_speed(self):
        self.assertEqual(self.cfg.SELECT_ACTIVE_MIN_SPEED, 1.0)

    # Reacquire gate geometry
    def test_reacquire_speed_dist_cap(self):
        self.assertEqual(self.cfg.REACQUIRE_SPEED_DIST_CAP, 90)

    def test_reacquire_speed_mult(self):
        self.assertEqual(self.cfg.REACQUIRE_SPEED_MULT, 1.8)

    def test_reacquire_lost_mult(self):
        self.assertEqual(self.cfg.REACQUIRE_LOST_MULT, 12)

    def test_reacquire_pred_gate_cap(self):
        self.assertEqual(self.cfg.REACQUIRE_PRED_GATE_CAP, 70)

    def test_reacquire_pred_gate_speed_mult(self):
        self.assertEqual(self.cfg.REACQUIRE_PRED_GATE_SPEED_MULT, 2.0)

    # Focus-mode gate
    def test_focus_max_dist_speed_cap(self):
        self.assertEqual(self.cfg.FOCUS_MAX_DIST_SPEED_CAP, 70)

    def test_focus_max_dist_speed_mult(self):
        self.assertEqual(self.cfg.FOCUS_MAX_DIST_SPEED_MULT, 1.6)

    # ROI overlap filter
    def test_roi_overlap_iou_thresh(self):
        self.assertEqual(self.cfg.ROI_OVERLAP_IOU_THRESH, 0.35)

    # Lock-score validation thresholds
    def test_lock_score_validate_margin(self):
        self.assertEqual(self.cfg.LOCK_SCORE_VALIDATE_MARGIN, 0.12)

    def test_lock_score_validate_min(self):
        self.assertEqual(self.cfg.LOCK_SCORE_VALIDATE_MIN, 0.55)


if __name__ == '__main__':
    unittest.main()
