#!/usr/bin/env python3
"""Unit tests for python_scripts/analyze_lock_events.py.

Tests exercise the core logic (load_events / summarize / analyze_files)
without touching the filesystem beyond a temporary JSONL fixture.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

# Allow running directly: python tests/test_analyze_lock_events.py
sys.path.insert(0, str(Path(__file__).parent.parent / 'python_scripts'))

from analyze_lock_events import load_events, summarize, analyze_files


def _make_event(event_type: str, frame_index: int, switches_per_min: float = 2.0) -> dict:
    return {
        'frame_index': frame_index,
        'event': event_type,
        'active_id': 1,
        'mode': 'yolo',
        'lock_score': 0.9,
        'lock_switches_per_min': switches_per_min,
        'budget_level': 1,
        'budget_load': 0.5,
    }


def _write_jsonl(path: Path, events: list[dict]) -> None:
    with path.open('w', encoding='utf-8') as fh:
        for ev in events:
            fh.write(json.dumps(ev) + '\n')


class TestSummarize(unittest.TestCase):
    def test_empty_returns_zeros(self):
        result = summarize([], source_name='empty')
        self.assertEqual(result['total_events'], 0)
        self.assertEqual(result['acquired'], 0)
        self.assertEqual(result['lost'], 0)
        self.assertEqual(result['reacquired'], 0)
        self.assertEqual(result['switch'], 0)
        self.assertEqual(result['switches_per_min_mean'], 0.0)
        self.assertEqual(result['switches_per_min_max'], 0.0)
        self.assertEqual(result['frame_span'], 0)
        self.assertEqual(result['source'], 'empty')

    def test_counts_all_event_types(self):
        events = [
            _make_event('acquired', 0),
            _make_event('lost', 10),
            _make_event('reacquired', 20),
            _make_event('switch', 30),
            _make_event('switch', 40),
        ]
        result = summarize(events, source_name='test')
        self.assertEqual(result['total_events'], 5)
        self.assertEqual(result['acquired'], 1)
        self.assertEqual(result['lost'], 1)
        self.assertEqual(result['reacquired'], 1)
        self.assertEqual(result['switch'], 2)

    def test_frame_span_correct(self):
        events = [_make_event('acquired', 5), _make_event('lost', 15)]
        result = summarize(events)
        # span = max - min + 1 = 15 - 5 + 1 = 11
        self.assertEqual(result['frame_span'], 11)

    def test_single_frame_span_is_one(self):
        events = [_make_event('acquired', 7)]
        result = summarize(events)
        self.assertEqual(result['frame_span'], 1)

    def test_switches_per_min_mean_and_max(self):
        events = [
            _make_event('acquired', 0, switches_per_min=1.0),
            _make_event('switch', 10, switches_per_min=3.0),
        ]
        result = summarize(events)
        self.assertAlmostEqual(result['switches_per_min_mean'], 2.0, places=4)
        self.assertAlmostEqual(result['switches_per_min_max'], 3.0, places=4)

    def test_unknown_event_type_counted_in_total(self):
        events = [
            _make_event('acquired', 0),
            {'frame_index': 1, 'event': 'UNKNOWN_TYPE', 'lock_switches_per_min': 1.0},
        ]
        result = summarize(events)
        self.assertEqual(result['total_events'], 2)
        self.assertEqual(result['acquired'], 1)


class TestLoadEvents(unittest.TestCase):
    def test_loads_valid_jsonl(self):
        events = [_make_event('acquired', i) for i in range(3)]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as fh:
            for ev in events:
                fh.write(json.dumps(ev) + '\n')
            tmp = Path(fh.name)
        try:
            loaded = load_events(tmp)
            self.assertEqual(len(loaded), 3)
            self.assertEqual(loaded[0]['event'], 'acquired')
        finally:
            tmp.unlink()

    def test_skips_blank_lines(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as fh:
            fh.write('\n')
            fh.write(json.dumps(_make_event('lost', 0)) + '\n')
            fh.write('\n')
            tmp = Path(fh.name)
        try:
            loaded = load_events(tmp)
            self.assertEqual(len(loaded), 1)
        finally:
            tmp.unlink()

    def test_warns_on_bad_json_but_continues(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as fh:
            fh.write('not-json\n')
            fh.write(json.dumps(_make_event('acquired', 0)) + '\n')
            tmp = Path(fh.name)
        try:
            loaded = load_events(tmp)
            self.assertEqual(len(loaded), 1)
        finally:
            tmp.unlink()


class TestAnalyzeFiles(unittest.TestCase):
    def test_missing_file_skipped(self):
        results = analyze_files([Path('/tmp/__nonexistent_lock_log__.jsonl')])
        self.assertEqual(results, [])

    def test_multiple_files_returns_one_summary_each(self):
        tmp1 = Path(tempfile.mktemp(suffix='.jsonl'))
        tmp2 = Path(tempfile.mktemp(suffix='.jsonl'))
        _write_jsonl(tmp1, [_make_event('acquired', 0)])
        _write_jsonl(tmp2, [_make_event('lost', 0), _make_event('reacquired', 5)])
        try:
            results = analyze_files([tmp1, tmp2])
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]['total_events'], 1)
            self.assertEqual(results[1]['total_events'], 2)
        finally:
            tmp1.unlink(missing_ok=True)
            tmp2.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
