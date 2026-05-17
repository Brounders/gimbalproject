"""Data-layer tests for the DTS training desk."""
from __future__ import annotations

import json

from app.training_desk_data import (
    STATUS_ACCEPTED,
    STATUS_HARD_NEGATIVE,
    STATUS_NEW,
    STATUS_REJECTED,
    STATUS_STAGED,
    AnnotationRecord,
    hard_negative_records,
    is_hard_negative,
    load_annotation_records,
    save_review_state,
    set_record_status,
    status_counts,
    training_candidate_records,
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


def _record(**overrides) -> AnnotationRecord:
    data = {
        'record_id': 'r1',
        'log_path': '/tmp/session.jsonl',
        'line_number': 1,
        'source': '/tmp/clip.mp4',
        'frame_index': 10,
        'bbox_xyxy': (1, 2, 11, 22),
        'event': 'operator_bbox',
        'status': STATUS_NEW,
        'active_id': 1,
        'reason': '',
    }
    data.update(overrides)
    return AnnotationRecord(**data)


def test_training_candidate_records_include_only_valid_accepted_and_staged():
    records = [
        _record(record_id='accepted', status=STATUS_ACCEPTED),
        _record(record_id='staged', status=STATUS_STAGED),
        _record(record_id='new', status=STATUS_NEW),
        _record(record_id='rejected', status=STATUS_REJECTED),
        _record(record_id='no_bbox', status=STATUS_ACCEPTED, bbox_xyxy=None),
        _record(record_id='bad_event', status=STATUS_ACCEPTED, event='operator_release'),
        _record(record_id='no_source', status=STATUS_ACCEPTED, source=''),
    ]

    selected = training_candidate_records(records)

    assert [record.record_id for record in selected] == ['accepted', 'staged']


def test_training_candidate_records_can_require_accepted_only():
    records = [
        _record(record_id='accepted', status=STATUS_ACCEPTED),
        _record(record_id='staged', status=STATUS_STAGED),
    ]

    selected = training_candidate_records(records, include_staged=False)

    assert [record.record_id for record in selected] == ['accepted']


def test_hard_negative_status_accepted_by_set_record_status():
    records = [_record(record_id='r1', status=STATUS_NEW)]
    assert set_record_status(records, 'r1', STATUS_HARD_NEGATIVE) is True
    assert records[0].status == STATUS_HARD_NEGATIVE


def test_hard_negative_not_in_training_candidates():
    records = [
        _record(record_id='neg', status=STATUS_HARD_NEGATIVE),
        _record(record_id='pos', status=STATUS_ACCEPTED),
    ]
    selected = training_candidate_records(records)
    assert [r.record_id for r in selected] == ['pos']


def test_is_hard_negative_requires_source_and_frame():
    assert is_hard_negative(_record(status=STATUS_HARD_NEGATIVE)) is True
    assert is_hard_negative(_record(status=STATUS_HARD_NEGATIVE, source='')) is False
    assert is_hard_negative(_record(status=STATUS_HARD_NEGATIVE, frame_index=-1)) is False
    assert is_hard_negative(_record(status=STATUS_ACCEPTED)) is False


def test_hard_negative_records_returns_only_hard_negatives():
    records = [
        _record(record_id='neg', status=STATUS_HARD_NEGATIVE),
        _record(record_id='pos', status=STATUS_ACCEPTED),
        _record(record_id='rej', status=STATUS_REJECTED),
    ]
    result = hard_negative_records(records)
    assert [r.record_id for r in result] == ['neg']


def test_status_counts_includes_hard_negative():
    records = [
        _record(record_id='n1', status=STATUS_HARD_NEGATIVE),
        _record(record_id='a1', status=STATUS_ACCEPTED),
    ]
    counts = status_counts(records)
    assert counts[STATUS_HARD_NEGATIVE] == 1
    assert counts[STATUS_ACCEPTED] == 1


def test_hard_negative_survives_save_reload(tmp_path):
    log_dir = tmp_path / 'logs'
    log_dir.mkdir()
    state_path = tmp_path / 'state.json'
    row = {'frame_index': 5, 'source': 'clip.mp4', 'bbox_xyxy': [1, 1, 10, 10], 'event': 'operator_bbox'}
    (log_dir / 'session.jsonl').write_text(json.dumps(row), encoding='utf-8')
    records = load_annotation_records(log_dir, state_path=state_path)
    set_record_status(records, records[0].record_id, STATUS_HARD_NEGATIVE)
    save_review_state(records, state_path)

    reloaded = load_annotation_records(log_dir, state_path=state_path)
    assert reloaded[0].status == STATUS_HARD_NEGATIVE
