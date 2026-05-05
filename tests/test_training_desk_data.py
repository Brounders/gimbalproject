"""Data-layer tests for the DTS training desk."""
from __future__ import annotations

import json

from app.training_desk_data import (
    STATUS_ACCEPTED,
    STATUS_NEW,
    STATUS_REJECTED,
    load_annotation_records,
    save_review_state,
    set_record_status,
    status_counts,
)


def test_load_annotation_records_reads_valid_operator_bbox_lines(tmp_path):
    log_dir = tmp_path / 'runs' / 'operator_annotations'
    log_dir.mkdir(parents=True)
    log_file = log_dir / 'session.jsonl'
    log_file.write_text(
        json.dumps({
            'frame_index': 12,
            'source': '/tmp/clip.mp4',
            'bbox_xyxy': [10, 20, 40, 60],
            'event': 'operator_bbox',
            'active_id': 9000,
        }) + '\n',
        encoding='utf-8',
    )

    records = load_annotation_records(log_dir)

    assert len(records) == 1
    assert records[0].source == '/tmp/clip.mp4'
    assert records[0].frame_index == 12
    assert records[0].bbox_xyxy == (10, 20, 40, 60)
    assert records[0].status == STATUS_NEW
    assert records[0].record_id


def test_load_annotation_records_preserves_malformed_rows_as_rejected(tmp_path):
    log_dir = tmp_path / 'runs' / 'operator_annotations'
    log_dir.mkdir(parents=True)
    (log_dir / 'bad.jsonl').write_text('{bad json\n', encoding='utf-8')

    records = load_annotation_records(log_dir)

    assert len(records) == 1
    assert records[0].status == STATUS_REJECTED
    assert 'json' in records[0].reason


def test_review_state_overrides_record_status(tmp_path):
    log_dir = tmp_path / 'runs' / 'operator_annotations'
    log_dir.mkdir(parents=True)
    log_file = log_dir / 'session.jsonl'
    log_file.write_text(
        json.dumps({
            'frame_index': 1,
            'source': '/tmp/clip.mp4',
            'bbox_xyxy': [1, 2, 11, 22],
            'event': 'operator_bbox',
        }) + '\n',
        encoding='utf-8',
    )
    state_path = tmp_path / 'review_state.json'
    first = load_annotation_records(log_dir, state_path=state_path)

    set_record_status(first, first[0].record_id, STATUS_ACCEPTED)
    save_review_state(first, state_path)
    second = load_annotation_records(log_dir, state_path=state_path)

    assert second[0].status == STATUS_ACCEPTED


def test_status_counts_groups_records(tmp_path):
    log_dir = tmp_path / 'runs' / 'operator_annotations'
    log_dir.mkdir(parents=True)
    rows = [
        {'frame_index': 1, 'source': 'a.mp4', 'bbox_xyxy': [1, 1, 10, 10], 'event': 'operator_bbox'},
        {'frame_index': 2, 'source': 'a.mp4', 'bbox_xyxy': [2, 2, 11, 11], 'event': 'operator_bbox'},
    ]
    (log_dir / 'session.jsonl').write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')
    records = load_annotation_records(log_dir)
    set_record_status(records, records[0].record_id, STATUS_ACCEPTED)

    counts = status_counts(records)

    assert counts[STATUS_ACCEPTED] == 1
    assert counts[STATUS_NEW] == 1
