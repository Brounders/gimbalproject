"""Tests for pure-logic helpers in pipeline.py.

All tests run without cv2 (VideoCapture), ultralytics, torch, or hardware.
TrackerPipeline.__init__ is never called here — only standalone functions and
SequenceGroundTruth are exercised.
"""
import unittest
from pathlib import Path

from uav_tracker.config import Config
from uav_tracker.pipeline import (
    SequenceGroundTruth,
    apply_runtime_preset,
    parse_video_source,
    resolve_model_path,
)


# ---------------------------------------------------------------------------
# parse_video_source
# ---------------------------------------------------------------------------

class TestParseVideoSource(unittest.TestCase):

    def test_integer_passthrough(self):
        self.assertEqual(parse_video_source(0), 0)

    def test_integer_string_converted(self):
        self.assertEqual(parse_video_source('2'), 2)

    def test_path_string_passthrough(self):
        self.assertEqual(parse_video_source('/tmp/video.mp4'), '/tmp/video.mp4')

    def test_rtsp_url_passthrough(self):
        url = 'rtsp://192.168.1.1/stream'
        self.assertEqual(parse_video_source(url), url)

    def test_http_url_passthrough(self):
        url = 'http://example.com/video.mp4'
        self.assertEqual(parse_video_source(url), url)

    def test_negative_int_passthrough(self):
        self.assertEqual(parse_video_source(-1), -1)


# ---------------------------------------------------------------------------
# apply_runtime_preset
# ---------------------------------------------------------------------------

class TestApplyRuntimePreset(unittest.TestCase):

    def test_no_overrides_is_noop(self):
        cfg = Config()
        original_imgsz = cfg.IMG_SIZE
        original_conf = cfg.CONF_THRESH
        apply_runtime_preset(cfg)
        self.assertEqual(cfg.IMG_SIZE, original_imgsz)
        self.assertAlmostEqual(cfg.CONF_THRESH, original_conf)

    def test_explicit_imgsz_override(self):
        cfg = Config()
        apply_runtime_preset(cfg, imgsz=1280)
        self.assertEqual(cfg.IMG_SIZE, 1280)

    def test_explicit_conf_override(self):
        cfg = Config()
        apply_runtime_preset(cfg, conf=0.55)
        self.assertAlmostEqual(cfg.CONF_THRESH, 0.55)

    def test_small_target_mode_bumps_imgsz_to_minimum(self):
        cfg = Config(IMG_SIZE=640, SMALL_TARGET_IMG_SIZE=960)
        apply_runtime_preset(cfg, small_target_mode=True)
        self.assertGreaterEqual(cfg.IMG_SIZE, 960)

    def test_small_target_mode_lowers_conf(self):
        cfg = Config(CONF_THRESH=0.30, SMALL_TARGET_CONF=0.15)
        apply_runtime_preset(cfg, small_target_mode=True)
        self.assertLessEqual(cfg.CONF_THRESH, 0.15)


# ---------------------------------------------------------------------------
# resolve_model_path
# ---------------------------------------------------------------------------

class TestResolveModelPath(unittest.TestCase):

    def test_nonexistent_returns_original(self):
        path = '/nonexistent/totally_fake_model.pt'
        result = resolve_model_path(path)
        self.assertEqual(result, path)

    def test_existing_path_returned_first(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            tmp = f.name
        try:
            result = resolve_model_path(tmp)
            self.assertEqual(result, tmp)
        finally:
            os.unlink(tmp)


# ---------------------------------------------------------------------------
# SequenceGroundTruth.bbox_for
# ---------------------------------------------------------------------------

class _FakeGT(SequenceGroundTruth):
    """SequenceGroundTruth with synthetic data, no filesystem access."""
    def __init__(self, exist, gt_rect):
        self.folder = Path('/fake')
        self.label_path = None
        self.exist = exist
        self.gt_rect = gt_rect


class TestSequenceGroundTruthBboxFor(unittest.TestCase):

    def test_existing_frame_returns_bbox(self):
        gt = _FakeGT(exist=[1], gt_rect=[[10, 20, 50, 60]])
        result = gt.bbox_for(0)
        self.assertEqual(result, (10, 20, 60, 80))  # x, y, x+w, y+h

    def test_absent_frame_returns_none(self):
        gt = _FakeGT(exist=[0], gt_rect=[[10, 20, 50, 60]])
        self.assertIsNone(gt.bbox_for(0))

    def test_out_of_range_index_returns_none(self):
        gt = _FakeGT(exist=[1], gt_rect=[[10, 20, 50, 60]])
        self.assertIsNone(gt.bbox_for(5))

    def test_zero_width_rect_returns_none(self):
        gt = _FakeGT(exist=[1], gt_rect=[[10, 20, 0, 60]])
        self.assertIsNone(gt.bbox_for(0))

    def test_empty_gt_returns_none(self):
        gt = _FakeGT(exist=[], gt_rect=[])
        self.assertIsNone(gt.bbox_for(0))


if __name__ == '__main__':
    unittest.main()
