from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


STATUS_NEW = 'new'
STATUS_ACCEPTED = 'accepted'
STATUS_REJECTED = 'rejected'
STATUS_STAGED = 'staged'
STATUS_VALUES = {STATUS_NEW, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_STAGED}


@dataclass
class AnnotationRecord:
    record_id: str
    log_path: str
    line_number: int
    source: str
    frame_index: int
    bbox_xyxy: tuple[int, int, int, int] | None
    event: str
    status: str = STATUS_NEW
    active_id: int | None = None
    reason: str = ''

    @property
    def clip_name(self) -> str:
        return Path(self.source).name if self.source else '-'

    @property
    def bbox_size(self) -> str:
        if self.bbox_xyxy is None:
            return '-'
        x1, y1, x2, y2 = self.bbox_xyxy
        return f'{max(0, x2 - x1)}x{max(0, y2 - y1)}'


def _record_id(log_path: Path, line_number: int, source: str, frame_index: int, bbox: object) -> str:
    raw = f'{log_path}|{line_number}|{source}|{frame_index}|{bbox}'
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]


def _read_review_state(state_path: Path | None) -> dict[str, str]:
    if state_path is None or not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text(encoding='utf-8'))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    statuses = data.get('statuses', data)
    if not isinstance(statuses, dict):
        return {}
    return {str(k): str(v) for k, v in statuses.items() if str(v) in STATUS_VALUES}


def _iter_jsonl_files(log_dir: Path) -> list[Path]:
    if log_dir.is_file():
        return [log_dir]
    if not log_dir.exists():
        return []
    return sorted(p for p in log_dir.glob('*.jsonl') if p.is_file())


def _coerce_bbox(value: object) -> tuple[int, int, int, int] | None:
    if not isinstance(value, (list, tuple)) or len(value) < 4:
        return None
    try:
        x1, y1, x2, y2 = [int(round(float(v))) for v in value[:4]]
    except (TypeError, ValueError):
        return None
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def load_annotation_records(
    log_dir: str | Path,
    *,
    state_path: str | Path | None = None,
) -> list[AnnotationRecord]:
    log_root = Path(log_dir)
    state = _read_review_state(Path(state_path) if state_path is not None else None)
    records: list[AnnotationRecord] = []

    for jsonl_path in _iter_jsonl_files(log_root):
        try:
            lines = jsonl_path.read_text(encoding='utf-8').splitlines()
        except Exception as exc:
            rid = _record_id(jsonl_path, 0, '', -1, '')
            records.append(AnnotationRecord(
                record_id=rid,
                log_path=str(jsonl_path),
                line_number=0,
                source='',
                frame_index=-1,
                bbox_xyxy=None,
                event='read_error',
                status=STATUS_REJECTED,
                reason=f'read error: {exc}',
            ))
            continue

        for line_no, line in enumerate(lines, start=1):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                rid = _record_id(jsonl_path, line_no, '', -1, line)
                records.append(AnnotationRecord(
                    record_id=rid,
                    log_path=str(jsonl_path),
                    line_number=line_no,
                    source='',
                    frame_index=-1,
                    bbox_xyxy=None,
                    event='malformed',
                    status=STATUS_REJECTED,
                    reason=f'json decode: {exc.msg}',
                ))
                continue

            event = str(obj.get('event', ''))
            source = str(obj.get('source', ''))
            try:
                frame_index = int(obj.get('frame_index', -1))
            except (TypeError, ValueError):
                frame_index = -1
            bbox = _coerce_bbox(obj.get('bbox_xyxy'))
            rid = _record_id(jsonl_path, line_no, source, frame_index, bbox)
            status = state.get(rid, STATUS_NEW)
            reason = ''
            if event != 'operator_bbox':
                status = STATUS_REJECTED
                reason = f'unsupported event: {event}'
            elif bbox is None or not source or frame_index < 0:
                status = STATUS_REJECTED
                reason = 'missing source/frame_index/bbox'
            records.append(AnnotationRecord(
                record_id=rid,
                log_path=str(jsonl_path),
                line_number=line_no,
                source=source,
                frame_index=frame_index,
                bbox_xyxy=bbox,
                event=event,
                status=status,
                active_id=obj.get('active_id') if isinstance(obj.get('active_id'), int) else None,
                reason=reason,
            ))
    return records


def set_record_status(records: Iterable[AnnotationRecord], record_id: str, status: str) -> bool:
    if status not in STATUS_VALUES:
        raise ValueError(f'unknown status: {status}')
    for record in records:
        if record.record_id == record_id:
            record.status = status
            return True
    return False


def save_review_state(records: Iterable[AnnotationRecord], state_path: str | Path) -> None:
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    statuses = {record.record_id: record.status for record in records if record.status in STATUS_VALUES}
    path.write_text(json.dumps({'statuses': statuses}, indent=2, ensure_ascii=False), encoding='utf-8')


def status_counts(records: Iterable[AnnotationRecord]) -> dict[str, int]:
    counts = Counter(record.status for record in records)
    return {status: int(counts.get(status, 0)) for status in sorted(STATUS_VALUES)}
