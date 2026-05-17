"""Unit tests for training_desk_quality.

Pure-data tests: deterministic, no real video I/O (we point sources at temp
files so frame readers return None and the quality stack falls back to the
``unavailable`` paths).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.training_desk_data import (
    STATUS_ACCEPTED,
    STATUS_NEW,
    AnnotationRecord,
)
from app.training_desk_quality import (
    DUP_NEAR_FRAME_DISTANCE,
    QUALITY_FAIL,
    QUALITY_NA,
    QUALITY_OK,
    QUALITY_WARN,
    QualityRow,
    aggregate_quality,
    bbox_iou,
    duplicate_summary,
    evaluate_record_quality,
    find_duplicates,
)


def _rec(**overrides) -> AnnotationRecord:
    base = dict(
        record_id='r1',
        log_path='/tmp/log.jsonl',
        line_number=1,
        source='/tmp/clip.mp4',
        frame_index=10,
        bbox_xyxy=(100, 100, 200, 200),
        event='operator_bbox',
        status=STATUS_NEW,
        active_id=None,
        reason='',
    )
    base.update(overrides)
    return AnnotationRecord(**base)


# ── bbox_iou ────────────────────────────────────────────────────────────────


class TestBboxIoU:
    def test_identical_boxes_iou_1(self):
        b = (10, 10, 50, 50)
        assert bbox_iou(b, b) == pytest.approx(1.0)

    def test_disjoint_boxes_iou_0(self):
        assert bbox_iou((0, 0, 10, 10), (100, 100, 200, 200)) == 0.0

    def test_partial_overlap(self):
        # Two 100×100 boxes shifted 50 px → overlap is 50×100=5000, union=15000 → 1/3
        a = (0, 0, 100, 100)
        b = (50, 0, 150, 100)
        assert bbox_iou(a, b) == pytest.approx(5000 / 15000)

    def test_degenerate_returns_0(self):
        assert bbox_iou((0, 0, 0, 0), (0, 0, 10, 10)) == 0.0


# ── Quality rows: structural / source / bounds / size / crop ────────────────


class TestQualityRows:
    def test_unsupported_event_fails_structurally(self):
        r = _rec(event='operator_release')
        report = evaluate_record_quality(r)
        struct = next(row for row in report.rows if row.name == 'Структура')
        assert struct.state == QUALITY_FAIL

    def test_missing_bbox_fails(self):
        r = _rec(bbox_xyxy=None)
        report = evaluate_record_quality(r)
        assert any(row.state == QUALITY_FAIL for row in report.rows)

    def test_nonexistent_source_fails_source_check(self):
        r = _rec(source='/no/such/file.mp4')
        report = evaluate_record_quality(r)
        src = next(row for row in report.rows if row.name == 'Источник')
        assert src.state == QUALITY_FAIL

    def test_no_frame_marks_pixel_rows_na(self):
        # Source not openable (empty path) → pixel-level rows return N/A.
        r = _rec(source='')
        report = evaluate_record_quality(r)
        sharpness = next(row for row in report.rows if row.name == 'Резкость')
        exposure = next(row for row in report.rows if row.name == 'Экспозиция')
        assert sharpness.state == QUALITY_NA
        assert exposure.state == QUALITY_NA

    def test_tiny_crop_fails_crop_check(self):
        r = _rec(bbox_xyxy=(0, 0, 4, 4))  # 4×4, below MIN_CROP_PIXELS
        report = evaluate_record_quality(r)
        crop = next(row for row in report.rows if row.name == 'Crop')
        assert crop.state == QUALITY_FAIL


class TestQualityReportAggregation:
    def test_warnings_and_fails_counted(self):
        r1 = QualityRow('a', QUALITY_OK)
        r2 = QualityRow('b', QUALITY_WARN)
        r3 = QualityRow('c', QUALITY_FAIL)
        r4 = QualityRow('d', QUALITY_NA)
        from app.training_desk_quality import QualityReport
        report = QualityReport.from_rows('rid', [r1, r2, r3, r4])
        assert report.warnings == 1
        assert report.fails == 1


class TestAggregateQuality:
    def test_aggregate_handles_missing_sources(self, tmp_path):
        recs = [
            _rec(record_id='r1', source=''),  # missing source
            _rec(record_id='r2', source=str(tmp_path / 'absent.mp4')),  # nonexistent file
            _rec(record_id='r3', event='operator_release', bbox_xyxy=None),  # invalid struct
        ]
        agg = aggregate_quality(recs)
        assert agg['total'] == 3
        assert agg['invalid_struct'] >= 1
        assert agg['missing_source'] >= 1


# ── Duplicate detection ────────────────────────────────────────────────────


class TestDuplicates:
    def test_exact_duplicate_detected(self):
        a = _rec(record_id='a', frame_index=10, bbox_xyxy=(0, 0, 50, 50))
        b = _rec(record_id='b', frame_index=10, bbox_xyxy=(0, 0, 50, 50))
        links = find_duplicates([a, b])
        assert 'a' in links
        kinds = {l.kind for l in links['a']}
        assert 'exact' in kinds

    def test_near_frame_high_iou_detected(self):
        a = _rec(record_id='a', frame_index=10, bbox_xyxy=(0, 0, 100, 100))
        # Frame distance 2, IoU should be high
        b = _rec(record_id='b', frame_index=12, bbox_xyxy=(2, 2, 100, 100))
        links = find_duplicates([a, b])
        assert any(l.kind == 'near' for l in links.get('a', []))

    def test_low_iou_not_duplicate(self):
        a = _rec(record_id='a', frame_index=10, bbox_xyxy=(0, 0, 50, 50))
        b = _rec(record_id='b', frame_index=11, bbox_xyxy=(500, 500, 550, 550))
        links = find_duplicates([a, b])
        assert links == {}

    def test_different_source_not_duplicate(self):
        a = _rec(record_id='a', source='/tmp/clip_a.mp4', frame_index=10,
                 bbox_xyxy=(0, 0, 50, 50))
        b = _rec(record_id='b', source='/tmp/clip_b.mp4', frame_index=10,
                 bbox_xyxy=(0, 0, 50, 50))
        links = find_duplicates([a, b])
        assert links == {}

    def test_missing_bbox_ignored_safely(self):
        a = _rec(record_id='a', bbox_xyxy=None, event='operator_release')
        b = _rec(record_id='b')
        links = find_duplicates([a, b])
        assert 'a' not in links

    def test_far_frame_not_duplicate(self):
        a = _rec(record_id='a', frame_index=10, bbox_xyxy=(0, 0, 100, 100))
        b = _rec(record_id='b', frame_index=10 + DUP_NEAR_FRAME_DISTANCE + 5,
                 bbox_xyxy=(0, 0, 100, 100))
        links = find_duplicates([a, b])
        assert links == {}

    def test_summary_counts_unique_records_by_kind(self):
        a = _rec(record_id='a', frame_index=10, bbox_xyxy=(0, 0, 50, 50))
        b = _rec(record_id='b', frame_index=10, bbox_xyxy=(0, 0, 50, 50))
        c = _rec(record_id='c', frame_index=11, bbox_xyxy=(1, 1, 50, 50))
        links = find_duplicates([a, b, c])
        summary = duplicate_summary(links)
        assert summary['records_with_duplicates'] >= 2

    def test_overlap_same_frame_high_iou(self):
        # Same frame, large overlap: 100×100 vs 90×90 inset → IoU ~ 0.81
        a = _rec(record_id='a', frame_index=20, bbox_xyxy=(0, 0, 100, 100))
        b = _rec(record_id='b', frame_index=20, bbox_xyxy=(10, 10, 100, 100))
        links = find_duplicates([a, b])
        kinds_a = {l.kind for l in links.get('a', [])}
        assert 'overlap' in kinds_a
