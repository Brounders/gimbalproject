"""Unit tests for python_scripts/export_operator_annotations_to_yolo.py.

Validates:
  - xyxy → YOLO normalized xywh conversion correctness;
  - malformed JSON line does not abort the export;
  - bbox out-of-bounds is rejected (not clipped);
  - dry-run mode does not create label files;
  - manifest contains expected per-line records.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

# Add python_scripts/ to import path so the script module is importable.
_PY_SCRIPTS = Path(__file__).resolve().parent.parent / 'python_scripts'
if str(_PY_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_PY_SCRIPTS))

import export_operator_annotations_to_yolo as exporter  # noqa: E402


# ---------------------------------------------------------------------------
# xyxy -> YOLO normalized xywh
# ---------------------------------------------------------------------------


class TestXyxyToYoloNorm(unittest.TestCase):

    def test_centered_box(self):
        cx, cy, w, h = exporter.xyxy_to_yolo_norm([0, 0, 100, 100], 200, 200)
        self.assertAlmostEqual(cx, 0.25)
        self.assertAlmostEqual(cy, 0.25)
        self.assertAlmostEqual(w, 0.5)
        self.assertAlmostEqual(h, 0.5)

    def test_full_frame_box(self):
        cx, cy, w, h = exporter.xyxy_to_yolo_norm([0, 0, 1920, 1080], 1920, 1080)
        self.assertAlmostEqual(cx, 0.5)
        self.assertAlmostEqual(cy, 0.5)
        self.assertAlmostEqual(w, 1.0)
        self.assertAlmostEqual(h, 1.0)

    def test_offset_box(self):
        # bbox = (100, 200, 300, 400) on 1000x800 → cx=0.2 cy=0.375 w=0.2 h=0.25
        cx, cy, w, h = exporter.xyxy_to_yolo_norm([100, 200, 300, 400], 1000, 800)
        self.assertAlmostEqual(cx, 0.2)
        self.assertAlmostEqual(cy, 0.375)
        self.assertAlmostEqual(w, 0.2)
        self.assertAlmostEqual(h, 0.25)

    def test_invalid_size_raises(self):
        with self.assertRaises(ValueError):
            exporter.xyxy_to_yolo_norm([0, 0, 10, 10], 0, 100)


# ---------------------------------------------------------------------------
# is_in_unit_bounds
# ---------------------------------------------------------------------------


class TestIsInUnitBounds(unittest.TestCase):

    def test_inside(self):
        self.assertTrue(exporter.is_in_unit_bounds(0.5, 0.5, 0.2, 0.2))

    def test_extends_below_zero(self):
        # cx=0.05, w=0.2 → x1=-0.05 → out of bounds
        self.assertFalse(exporter.is_in_unit_bounds(0.05, 0.5, 0.2, 0.2))

    def test_extends_above_one(self):
        # cx=0.95, w=0.2 → x2=1.05 → out of bounds
        self.assertFalse(exporter.is_in_unit_bounds(0.95, 0.5, 0.2, 0.2))

    def test_zero_size_rejected(self):
        self.assertFalse(exporter.is_in_unit_bounds(0.5, 0.5, 0.0, 0.2))


# ---------------------------------------------------------------------------
# Full export with synthetic JSONL fixtures
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, lines: list[str]) -> None:
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _ok_line(frame: int, bbox: list[int], source: str = '/tmp/clip.mp4') -> str:
    return json.dumps({
        'frame_index': frame,
        'source': source,
        'bbox_xyxy': bbox,
        'active_id': 9000,
        'active_source': 'operator',
        'event': 'operator_bbox',
    })


class TestExportEndToEnd(unittest.TestCase):

    def setUp(self):
        # All tests build their own tmp_path via unittest's mkdtemp pattern.
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix='op_export_'))
        self.input_dir = self.tmp / 'annotations'
        self.input_dir.mkdir()
        self.output_dir = self.tmp / 'labels'

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _args(self, **overrides):
        import argparse
        ns = argparse.Namespace(
            input=self.input_dir,
            output_dir=self.output_dir,
            frame_width=1000,
            frame_height=800,
            class_id=0,
            dry_run=False,
            manifest_format='both',
            manifest_dir=None,
        )
        for k, v in overrides.items():
            setattr(ns, k, v)
        return ns

    # -----------------------------------------------------------------------
    # Conversion correctness end-to-end
    # -----------------------------------------------------------------------

    def test_ok_line_creates_label_file_with_expected_content(self):
        jsonl = self.input_dir / 'session1.jsonl'
        _write_jsonl(jsonl, [_ok_line(42, [100, 200, 300, 400], '/v/clip_a.mp4')])

        summary = exporter.run(self._args())
        self.assertEqual(summary.ok, 1)
        self.assertEqual(summary.files_written, 1)

        label_path = self.output_dir / 'clip_a__f000042.txt'
        self.assertTrue(label_path.exists(), f'expected label file at {label_path}')
        content = label_path.read_text(encoding='utf-8').strip()
        # cx=0.2 cy=0.375 w=0.2 h=0.25
        parts = content.split()
        self.assertEqual(parts[0], '0')
        self.assertAlmostEqual(float(parts[1]), 0.2, places=5)
        self.assertAlmostEqual(float(parts[2]), 0.375, places=5)
        self.assertAlmostEqual(float(parts[3]), 0.2, places=5)
        self.assertAlmostEqual(float(parts[4]), 0.25, places=5)

    # -----------------------------------------------------------------------
    # Malformed JSON line resilience
    # -----------------------------------------------------------------------

    def test_malformed_line_does_not_abort_export(self):
        jsonl = self.input_dir / 'session2.jsonl'
        _write_jsonl(jsonl, [
            _ok_line(1, [10, 20, 110, 120], '/v/clip_b.mp4'),
            '{not json',                                 # malformed
            _ok_line(2, [10, 20, 110, 120], '/v/clip_b.mp4'),
        ])

        summary = exporter.run(self._args())
        self.assertEqual(summary.total_lines, 3)
        self.assertEqual(summary.ok, 2)
        self.assertEqual(summary.malformed_line, 1)
        self.assertEqual(summary.files_written, 2)
        # Manifest must include the malformed row with status=malformed_line.
        statuses = [r.status for r in summary.rows]
        self.assertIn(exporter.STATUS_MALFORMED_LINE, statuses)
        self.assertEqual(statuses.count(exporter.STATUS_OK), 2)

    # -----------------------------------------------------------------------
    # Out-of-bounds bbox is REJECTED (decision: reject, do not clip).
    # -----------------------------------------------------------------------

    def test_bbox_out_of_bounds_is_rejected(self):
        jsonl = self.input_dir / 'session3.jsonl'
        # frame is 1000x800, bbox extends past the right edge.
        _write_jsonl(jsonl, [
            _ok_line(7, [950, 100, 1100, 200], '/v/clip_c.mp4'),
        ])

        summary = exporter.run(self._args())
        self.assertEqual(summary.ok, 0)
        self.assertEqual(summary.rejected_out_of_bounds, 1)
        self.assertEqual(summary.files_written, 0)
        # No label file must be created for the rejected row.
        self.assertFalse((self.output_dir / 'clip_c__f000007.txt').exists())
        # Manifest reflects the rejection.
        oob_rows = [r for r in summary.rows if r.status == exporter.STATUS_REJECTED_OOB]
        self.assertEqual(len(oob_rows), 1)
        self.assertEqual(oob_rows[0].bbox_xyxy, [950, 100, 1100, 200])

    def test_degenerate_bbox_is_rejected(self):
        jsonl = self.input_dir / 'session4.jsonl'
        _write_jsonl(jsonl, [
            _ok_line(1, [100, 100, 100, 200], '/v/clip_d.mp4'),  # zero width
        ])
        summary = exporter.run(self._args())
        self.assertEqual(summary.rejected_degenerate, 1)
        self.assertEqual(summary.ok, 0)

    # -----------------------------------------------------------------------
    # dry-run does not write label files
    # -----------------------------------------------------------------------

    def test_dry_run_skips_label_files_but_writes_manifest(self):
        jsonl = self.input_dir / 'session5.jsonl'
        _write_jsonl(jsonl, [
            _ok_line(1, [100, 100, 200, 200], '/v/clip_e.mp4'),
            _ok_line(2, [300, 300, 400, 400], '/v/clip_e.mp4'),
        ])

        summary = exporter.run(self._args(dry_run=True))
        # Logical counters still increment: 2 rows are valid OK conversions.
        self.assertEqual(summary.ok, 2)
        # But no .txt label files written.
        self.assertEqual(summary.files_written, 0)
        # output_dir must not exist (we never created it because dry-run).
        # Note: manifest_dir defaults to output_dir; in dry-run manifest itself
        # is also skipped from disk. Verify nothing on disk.
        self.assertFalse(self.output_dir.exists(),
                         'dry-run must not create label/manifest files')
        self.assertFalse((self.output_dir / 'manifest.json').exists())
        self.assertFalse((self.output_dir / 'manifest.csv').exists())

    # -----------------------------------------------------------------------
    # Manifest content
    # -----------------------------------------------------------------------

    def test_manifest_files_written_with_expected_records(self):
        jsonl = self.input_dir / 'session6.jsonl'
        _write_jsonl(jsonl, [
            _ok_line(1, [100, 100, 200, 200], '/v/clip_f.mp4'),
            json.dumps({'event': 'other_event', 'source': '/v/clip_f.mp4',
                        'frame_index': 2, 'bbox_xyxy': [0, 0, 10, 10]}),
        ])
        summary = exporter.run(self._args())

        # Manifest JSON
        manifest_json = self.output_dir / 'manifest.json'
        self.assertTrue(manifest_json.exists())
        data = json.loads(manifest_json.read_text(encoding='utf-8'))
        self.assertEqual(data['summary']['ok'], 1)
        self.assertEqual(data['summary']['skipped_event'], 1)
        self.assertEqual(len(data['rows']), 2)
        # Manifest CSV
        manifest_csv = self.output_dir / 'manifest.csv'
        self.assertTrue(manifest_csv.exists())
        csv_text = manifest_csv.read_text(encoding='utf-8')
        self.assertIn('clip_f__f000001.txt', csv_text)
        self.assertIn('skipped_event', csv_text)

    # -----------------------------------------------------------------------
    # Skipped event types (e.g. operator_confirm) are not converted
    # -----------------------------------------------------------------------

    def test_non_operator_bbox_event_is_skipped(self):
        jsonl = self.input_dir / 'session7.jsonl'
        _write_jsonl(jsonl, [
            json.dumps({'event': 'operator_confirm', 'source': '/v/c.mp4',
                        'frame_index': 1, 'bbox_xyxy': [0, 0, 10, 10]}),
        ])
        summary = exporter.run(self._args())
        self.assertEqual(summary.ok, 0)
        self.assertEqual(summary.skipped_event, 1)
        self.assertEqual(summary.files_written, 0)

    # -----------------------------------------------------------------------
    # Missing field handling
    # -----------------------------------------------------------------------

    def test_missing_bbox_is_recorded(self):
        jsonl = self.input_dir / 'session8.jsonl'
        _write_jsonl(jsonl, [
            json.dumps({'event': 'operator_bbox', 'source': '/v/c.mp4',
                        'frame_index': 5}),
        ])
        summary = exporter.run(self._args())
        self.assertEqual(summary.missing_field, 1)
        self.assertEqual(summary.ok, 0)


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


class TestCliArgs(unittest.TestCase):

    def test_defaults(self):
        ns = exporter.parse_args(['--input', '/tmp/x', '--frame-width', '640', '--frame-height', '480'])
        self.assertEqual(ns.class_id, 0)
        self.assertFalse(ns.dry_run)
        self.assertEqual(ns.manifest_format, 'both')

    def test_dry_run_flag(self):
        ns = exporter.parse_args(['--input', '/tmp/x', '--frame-width', '1', '--frame-height', '1', '--dry-run'])
        self.assertTrue(ns.dry_run)

    def test_parse_manifest_formats(self):
        self.assertEqual(exporter.parse_manifest_formats('json'), ['json'])
        self.assertEqual(exporter.parse_manifest_formats('csv'), ['csv'])
        self.assertEqual(sorted(exporter.parse_manifest_formats('both')), ['csv', 'json'])
        with self.assertRaises(ValueError):
            exporter.parse_manifest_formats('xml')


if __name__ == '__main__':
    unittest.main()
