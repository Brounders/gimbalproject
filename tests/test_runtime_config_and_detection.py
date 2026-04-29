"""Tests for RuntimeConfigView and Detection factory methods.

Runs without cv2, ultralytics, torch, or hardware.
"""
import unittest

from uav_tracker.config import Config, RuntimeConfigView
from uav_tracker.runtime.base import Detection


# ---------------------------------------------------------------------------
# RuntimeConfigView
# ---------------------------------------------------------------------------

class TestRuntimeConfigView(unittest.TestCase):

    def test_from_config_round_trips_fields(self):
        cfg = Config()
        view = RuntimeConfigView.from_config(cfg)
        self.assertEqual(view.CONF_THRESH, cfg.CONF_THRESH)
        self.assertEqual(view.IMG_SIZE, cfg.IMG_SIZE)
        self.assertEqual(view.DEVICE, cfg.DEVICE)
        self.assertEqual(view.NIGHT_ENABLED, cfg.NIGHT_ENABLED)

    def test_view_is_immutable(self):
        view = RuntimeConfigView.from_config(Config())
        with self.assertRaises((AttributeError, TypeError)):
            view.CONF_THRESH = 0.99  # type: ignore[misc]

    def test_view_independent_of_cfg_mutation(self):
        cfg = Config()
        view = RuntimeConfigView.from_config(cfg)
        original = view.CONF_THRESH
        cfg.CONF_THRESH = 0.05  # mutate cfg after snapshot
        self.assertEqual(view.CONF_THRESH, original)  # view unaffected

    def test_override_reflected_in_view(self):
        cfg = Config(CONF_THRESH=0.75, NIGHT_ENABLED=False)
        view = RuntimeConfigView.from_config(cfg)
        self.assertAlmostEqual(view.CONF_THRESH, 0.75)
        self.assertFalse(view.NIGHT_ENABLED)


# ---------------------------------------------------------------------------
# Detection.from_night
# ---------------------------------------------------------------------------

class TestDetectionFromNight(unittest.TestCase):

    def _det(self, **kw):
        base = {'bbox': (10, 20, 30, 40), 'cx': 20.0, 'cy': 30.0, 'conf': 0.8, 'cls_id': 0}
        base.update(kw)
        return base

    def test_basic_fields(self):
        d = Detection.from_night(self._det())
        self.assertEqual(d.bbox, (10, 20, 30, 40))
        self.assertAlmostEqual(d.cx, 20.0)
        self.assertAlmostEqual(d.cy, 30.0)
        self.assertAlmostEqual(d.conf, 0.8)
        self.assertEqual(d.source, 'night')

    def test_missing_conf_defaults_zero(self):
        det = {'bbox': (0, 0, 10, 10), 'cx': 5.0, 'cy': 5.0}
        d = Detection.from_night(det)
        self.assertAlmostEqual(d.conf, 0.0)

    def test_missing_cls_id_defaults_minus_one(self):
        det = {'bbox': (0, 0, 10, 10), 'cx': 5.0, 'cy': 5.0}
        d = Detection.from_night(det)
        self.assertEqual(d.cls_id, -1)

    def test_track_id_is_none(self):
        d = Detection.from_night(self._det())
        self.assertIsNone(d.track_id)


# ---------------------------------------------------------------------------
# Detection.from_lock
# ---------------------------------------------------------------------------

class TestDetectionFromLock(unittest.TestCase):

    def test_basic_fields(self):
        d = Detection.from_lock(cx=100.0, cy=200.0, bbox=(80, 180, 120, 220), conf=0.92)
        self.assertEqual(d.bbox, (80, 180, 120, 220))
        self.assertAlmostEqual(d.cx, 100.0)
        self.assertAlmostEqual(d.cy, 200.0)
        self.assertAlmostEqual(d.conf, 0.92)
        self.assertEqual(d.source, 'lock')
        self.assertEqual(d.cls_id, -1)
        self.assertIsNone(d.track_id)


if __name__ == '__main__':
    unittest.main()
