"""Unit tests for TemplateLockTracker — init, reset, clip_bbox geometry."""
import unittest

import numpy as np

from uav_tracker.config import Config
from uav_tracker.tracking.lock_tracker import TemplateLockTracker


def _cfg(**kw) -> Config:
    return Config(**kw)


def _gray_frame(h: int = 100, w: int = 100) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


class TestTemplateLockTrackerInit(unittest.TestCase):
    def test_initial_state(self):
        t = TemplateLockTracker(_cfg())
        self.assertIsNone(t.template)
        self.assertIsNone(t.bbox)
        self.assertEqual(t.last_score, 0.0)
        self.assertEqual(t._consecutive_low_score, 0)
        self.assertFalse(t.needs_recovery)


class TestTemplateLockTrackerReset(unittest.TestCase):
    def test_reset_clears_all_state(self):
        t = TemplateLockTracker(_cfg())
        t.template = np.zeros((10, 10), dtype=np.uint8)
        t.bbox = (0, 0, 10, 10)
        t.last_score = 0.9
        t._consecutive_low_score = 5
        t.needs_recovery = True

        t.reset()

        self.assertIsNone(t.template)
        self.assertIsNone(t.bbox)
        self.assertEqual(t.last_score, 0.0)
        self.assertEqual(t._consecutive_low_score, 0)
        self.assertFalse(t.needs_recovery)


class TestTemplateLockTrackerClipBbox(unittest.TestCase):
    def _t(self):
        return TemplateLockTracker(_cfg())

    def test_normal_bbox_unchanged(self):
        t = self._t()
        result = t._clip_bbox((10, 10, 50, 50), (100, 100))
        self.assertEqual(result, (10, 10, 50, 50))

    def test_bbox_clamped_to_frame_bounds(self):
        t = self._t()
        result = t._clip_bbox((-5, -5, 150, 150), (100, 100))
        self.assertIsNotNone(result)
        x1, y1, x2, y2 = result
        self.assertGreaterEqual(x1, 0)
        self.assertGreaterEqual(y1, 0)
        self.assertLessEqual(x2, 100)
        self.assertLessEqual(y2, 100)

    def test_degenerate_bbox_returns_none(self):
        t = self._t()
        # width < 4 → None
        self.assertIsNone(t._clip_bbox((10, 10, 12, 50), (100, 100)))

    def test_degenerate_height_returns_none(self):
        t = self._t()
        # height < 4 → None
        self.assertIsNone(t._clip_bbox((10, 10, 50, 12), (100, 100)))

    def test_zero_area_bbox_returns_none(self):
        t = self._t()
        self.assertIsNone(t._clip_bbox((50, 50, 51, 51), (100, 100)))


class TestTemplateLockTrackerPredictNoTemplate(unittest.TestCase):
    def test_predict_without_template_returns_none(self):
        t = TemplateLockTracker(_cfg())
        det, score, roi = t.predict(_gray_frame())
        self.assertIsNone(det)
        self.assertEqual(score, 0.0)
        self.assertIsNone(roi)


if __name__ == '__main__':
    unittest.main()
