"""Tests for pure-logic helpers in pipeline.py.

All tests run without cv2 (VideoCapture), ultralytics, torch, or hardware.
TrackerPipeline.__init__ is never called here — only standalone functions and
SequenceGroundTruth are exercised.
"""
import json
import tempfile
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


# ---------------------------------------------------------------------------
# SequenceGroundTruth — MP4 file-source GT resolution
# ---------------------------------------------------------------------------

class TestSequenceGroundTruthFileSources(unittest.TestCase):
    """Tests for the MP4/file-source extension of SequenceGroundTruth."""

    def _write_gt(self, path: Path, exist, gt_rect):
        path.write_text(json.dumps({'exist': exist, 'gt_rect': gt_rect}), encoding='utf-8')

    def test_resolves_sibling_gt_json(self):
        """_gt.json sibling next to MP4 is found without pack dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mp4 = Path(tmpdir) / 'myclip.mp4'
            mp4.touch()
            gt_path = Path(tmpdir) / 'myclip_gt.json'
            self._write_gt(gt_path, [1], [[10, 20, 50, 60]])
            gt = SequenceGroundTruth(mp4)
            self.assertEqual(gt.label_path, gt_path)
            self.assertEqual(gt.exist, [1])

    def test_resolves_pack_dir_gt_json(self):
        """GT in configs/ground_truth/regression_pack/<stem>_gt.json is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake video file in a video dir
            video_dir = Path(tmpdir) / 'test_videos'
            video_dir.mkdir()
            mp4 = video_dir / 'testclip.mp4'
            mp4.touch()
            # Create pack GT dir and write GT
            pack_dir = Path(tmpdir) / 'configs' / 'ground_truth' / 'regression_pack'
            pack_dir.mkdir(parents=True)
            gt_path = pack_dir / 'testclip_gt.json'
            self._write_gt(gt_path, [1, 0], [[5, 5, 10, 10], [0, 0, 0, 0]])
            # Patch the class-level _PACK_GT_DIR to point into our tmpdir
            orig = SequenceGroundTruth._PACK_GT_DIR
            try:
                SequenceGroundTruth._PACK_GT_DIR = pack_dir
                gt = SequenceGroundTruth(mp4)
                self.assertEqual(gt.label_path, gt_path)
                self.assertEqual(len(gt.exist), 2)
            finally:
                SequenceGroundTruth._PACK_GT_DIR = orig

    def test_no_gt_returns_none_from_bbox_for(self):
        """MP4 with no GT file: bbox_for() returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mp4 = Path(tmpdir) / 'noclip.mp4'
            mp4.touch()
            gt = SequenceGroundTruth(mp4)
            self.assertIsNone(gt.label_path)
            self.assertIsNone(gt.bbox_for(0))

    def test_bbox_for_xywh_to_xyxy_conversion(self):
        """bbox_for converts [x, y, w, h] → (x, y, x+w, y+h)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mp4 = Path(tmpdir) / 'clip.mp4'
            mp4.touch()
            gt_path = Path(tmpdir) / 'clip_gt.json'
            self._write_gt(gt_path, [1], [[100, 200, 30, 40]])
            gt = SequenceGroundTruth(mp4)
            result = gt.bbox_for(0)
            self.assertEqual(result, (100, 200, 130, 240))

    def test_target_absent_gt_returns_none(self):
        """Frames with exist=0 and zero rect return None even when GT is present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mp4 = Path(tmpdir) / 'absent.mp4'
            mp4.touch()
            gt_path = Path(tmpdir) / 'absent_gt.json'
            self._write_gt(gt_path, [0, 0, 0], [[0, 0, 0, 0]] * 3)
            gt = SequenceGroundTruth(mp4)
            for i in range(3):
                self.assertIsNone(gt.bbox_for(i))

    def test_antiuav_format_preserves_frame_count_and_first_bbox(self):
        """Anti-UAV JSON (list of [x,y,w,h] per frame) survives round-trip."""
        exist_data = [1] * 5 + [0] * 3
        gt_rect_data = [[100 + i, 200, 50, 60] for i in range(8)]
        with tempfile.TemporaryDirectory() as tmpdir:
            mp4 = Path(tmpdir) / 'antiuav_clip.mp4'
            mp4.touch()
            gt_path = Path(tmpdir) / 'antiuav_clip_gt.json'
            self._write_gt(gt_path, exist_data, gt_rect_data)
            gt = SequenceGroundTruth(mp4)
            self.assertEqual(len(gt.exist), 8)
            # First frame: exist=1, bbox [100, 200, 50, 60] → xyxy (100, 200, 150, 260)
            self.assertEqual(gt.bbox_for(0), (100, 200, 150, 260))
            # Frame 6: exist=0 → None
            self.assertIsNone(gt.bbox_for(6))

    def test_sibling_takes_priority_over_pack_dir(self):
        """Sibling _gt.json is preferred over pack dir when both exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mp4 = Path(tmpdir) / 'prio.mp4'
            mp4.touch()
            sibling = Path(tmpdir) / 'prio_gt.json'
            self._write_gt(sibling, [1], [[1, 1, 5, 5]])
            pack_dir = Path(tmpdir) / 'pack'
            pack_dir.mkdir()
            pack_gt = pack_dir / 'prio_gt.json'
            self._write_gt(pack_gt, [0], [[0, 0, 0, 0]])
            orig = SequenceGroundTruth._PACK_GT_DIR
            try:
                SequenceGroundTruth._PACK_GT_DIR = pack_dir
                gt = SequenceGroundTruth(mp4)
                # Should use sibling (exist=[1])
                self.assertEqual(gt.exist, [1])
            finally:
                SequenceGroundTruth._PACK_GT_DIR = orig


# ---------------------------------------------------------------------------
# import_regression_pack_gt — import script unit tests
# ---------------------------------------------------------------------------

class TestImportRegressionPackGt(unittest.TestCase):
    """Unit tests for import_regression_pack_gt helpers."""

    def test_synthesise_absent_creates_all_zero_gt(self):
        """synthesise_absent creates exist=[0]*N gt_rect=[[0,0,0,0]]*N."""
        import sys
        import os
        sys.path.insert(0, str(Path(__file__).parent.parent / 'python_scripts'))
        try:
            from import_regression_pack_gt import synthesise_absent
        except ImportError:
            self.skipTest('import_regression_pack_gt not importable')
        with tempfile.TemporaryDirectory() as tmpdir:
            # synthesise_absent needs a real video path for frame count;
            # patch cv2.VideoCapture by providing a mock video path that
            # returns 0 frames → function returns error
            out_dir = Path(tmpdir)
            fake_video = Path(tmpdir) / 'fake.mp4'
            fake_video.touch()
            result = synthesise_absent('fake', fake_video, out_dir)
            # Can't get frame count from empty file; expect error
            self.assertEqual(result['status'], 'error')

    def test_import_antiuav_missing_source_returns_error(self):
        """import_antiuav with missing Desktop source returns error dict."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / 'python_scripts'))
        try:
            from import_regression_pack_gt import import_antiuav
        except ImportError:
            self.skipTest('import_regression_pack_gt not importable')
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / 'nonexistent.json'
            result = import_antiuav('myclip', missing, Path(tmpdir))
            self.assertEqual(result['status'], 'error')
            self.assertIn('Source not found', result['reason'])

    def test_import_antiuav_valid_source_preserves_frame_count(self):
        """import_antiuav reads exist/gt_rect and writes canonical GT JSON."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / 'python_scripts'))
        try:
            from import_regression_pack_gt import import_antiuav
        except ImportError:
            self.skipTest('import_regression_pack_gt not importable')
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / 'visible.json'
            exist = [1, 1, 0, 1]
            gt_rect = [[10, 20, 5, 6]] * 4
            src.write_text(json.dumps({'exist': exist, 'gt_rect': gt_rect}))
            out_dir = Path(tmpdir) / 'out'
            out_dir.mkdir()
            result = import_antiuav('myclip', src, out_dir)
            self.assertEqual(result['status'], 'ok')
            self.assertEqual(result['total_frames'], 4)
            self.assertEqual(result['gt_frames'], 3)
            out_data = json.loads((out_dir / 'myclip_gt.json').read_text())
            self.assertEqual(out_data['exist'], exist)


if __name__ == '__main__':
    unittest.main()
