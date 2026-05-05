#!/usr/bin/env python3
"""export_operator_annotations_to_yolo.py — operator annotation → YOLO labels.

Читает один или несколько JSONL файлов из `runs/operator_annotations/`
(пишутся pipeline-ом при ручной разметке оператором) и формирует:

  1. YOLO label-файлы (`.txt`) в формате:
       <class_id> <cx_norm> <cy_norm> <w_norm> <h_norm>
  2. Manifest (JSON и CSV) со статусом каждой исходной строки.

Назначение: дать первый, минимально-инвазивный путь от operator-кликов
к training labels для дообучения модели на провальных сценах.

Кадры из видео в этой итерации НЕ извлекаются — только labels + manifest.

Out-of-bounds bbox (центр или габариты выходят за [0, 1] после нормализации)
**отклоняются** (`status=rejected_out_of_bounds`), а не клипаются — клипанная
рамка может испортить training, а оператор должен перерисовать корректно.

Usage:
  python python_scripts/export_operator_annotations_to_yolo.py \
      --input runs/operator_annotations/ \
      --output-dir runs/operator_yolo_labels/ \
      --frame-width 1920 --frame-height 1080 \
      [--class-id 0] [--dry-run] [--manifest-format json|csv|both]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional


# Status codes used in manifest rows.
STATUS_OK = 'ok'
STATUS_MALFORMED_LINE = 'malformed_line'
STATUS_MISSING_FIELD = 'missing_field'
STATUS_SKIPPED_EVENT = 'skipped_event'
STATUS_REJECTED_OOB = 'rejected_out_of_bounds'
STATUS_REJECTED_DEGENERATE = 'rejected_degenerate_bbox'


@dataclass
class ManifestRow:
    """One processed JSONL line, regardless of outcome."""
    input_file: str
    line_number: int
    status: str
    source: Optional[str] = None
    frame_index: Optional[int] = None
    bbox_xyxy: Optional[list[int]] = None
    label_path: Optional[str] = None
    yolo_xywh_norm: Optional[list[float]] = None
    reason: Optional[str] = None


@dataclass
class ExportSummary:
    total_lines: int = 0
    ok: int = 0
    malformed_line: int = 0
    missing_field: int = 0
    skipped_event: int = 0
    rejected_out_of_bounds: int = 0
    rejected_degenerate: int = 0
    files_written: int = 0
    rows: list[ManifestRow] = field(default_factory=list)


def xyxy_to_yolo_norm(
    bbox: tuple[int, int, int, int] | list[int],
    width: int,
    height: int,
) -> tuple[float, float, float, float]:
    """Convert (x1, y1, x2, y2) absolute to (cx, cy, w, h) normalized to [0, 1].

    Caller is responsible for validating the result is inside [0, 1].
    """
    if width <= 0 or height <= 0:
        raise ValueError(f'invalid frame size: width={width} height={height}')
    x1, y1, x2, y2 = (float(v) for v in bbox[:4])
    bw = x2 - x1
    bh = y2 - y1
    cx = (x1 + x2) / 2.0 / float(width)
    cy = (y1 + y2) / 2.0 / float(height)
    w_n = bw / float(width)
    h_n = bh / float(height)
    return cx, cy, w_n, h_n


def is_in_unit_bounds(cx: float, cy: float, w: float, h: float) -> bool:
    """True only if the YOLO-normalized box fits strictly inside [0, 1]."""
    if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0):
        return False
    if not (0.0 < w <= 1.0 and 0.0 < h <= 1.0):
        return False
    if cx - w / 2.0 < 0.0 or cy - h / 2.0 < 0.0:
        return False
    if cx + w / 2.0 > 1.0 or cy + h / 2.0 > 1.0:
        return False
    return True


def label_path_for(
    output_dir: Path,
    source_path: str | Path,
    frame_index: int,
) -> Path:
    """Stable label file name: `<video_stem>__f<frame_index:06d>.txt`."""
    stem = Path(str(source_path)).stem if source_path else 'unknown'
    return output_dir / f'{stem}__f{int(frame_index):06d}.txt'


def format_yolo_line(class_id: int, cx: float, cy: float, w: float, h: float) -> str:
    return f'{int(class_id)} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n'


def iter_input_files(input_path: Path) -> list[Path]:
    """Resolve --input into a sorted list of .jsonl files.

    Accepts either a single file or a directory.  Returns [] if nothing matches.
    """
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted(p for p in input_path.iterdir() if p.suffix == '.jsonl')
    return []


def process_jsonl(
    jsonl_path: Path,
    output_dir: Path,
    *,
    frame_width: int,
    frame_height: int,
    class_id: int,
    dry_run: bool,
    summary: ExportSummary,
) -> None:
    """Process one JSONL file, append rows + side-effects into `summary`."""
    with jsonl_path.open('r', encoding='utf-8') as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            summary.total_lines += 1
            stripped = raw_line.strip()
            if not stripped:
                # blank line — count as malformed for visibility, but cheap
                summary.malformed_line += 1
                summary.rows.append(ManifestRow(
                    input_file=str(jsonl_path),
                    line_number=line_no,
                    status=STATUS_MALFORMED_LINE,
                    reason='blank line',
                ))
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                summary.malformed_line += 1
                summary.rows.append(ManifestRow(
                    input_file=str(jsonl_path),
                    line_number=line_no,
                    status=STATUS_MALFORMED_LINE,
                    reason=f'json decode: {exc.msg}',
                ))
                continue

            event = obj.get('event')
            if event != 'operator_bbox':
                summary.skipped_event += 1
                summary.rows.append(ManifestRow(
                    input_file=str(jsonl_path),
                    line_number=line_no,
                    status=STATUS_SKIPPED_EVENT,
                    source=obj.get('source'),
                    frame_index=obj.get('frame_index'),
                    reason=f'event={event!r}',
                ))
                continue

            source = obj.get('source')
            frame_index = obj.get('frame_index')
            bbox = obj.get('bbox_xyxy')
            if source is None or frame_index is None or bbox is None:
                summary.missing_field += 1
                summary.rows.append(ManifestRow(
                    input_file=str(jsonl_path),
                    line_number=line_no,
                    status=STATUS_MISSING_FIELD,
                    source=source,
                    frame_index=frame_index,
                    bbox_xyxy=bbox if isinstance(bbox, list) else None,
                    reason='source/frame_index/bbox_xyxy missing',
                ))
                continue
            if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
                summary.missing_field += 1
                summary.rows.append(ManifestRow(
                    input_file=str(jsonl_path),
                    line_number=line_no,
                    status=STATUS_MISSING_FIELD,
                    source=source,
                    frame_index=frame_index,
                    reason='bbox_xyxy not a 4-tuple',
                ))
                continue

            try:
                bbox_int = [int(round(float(v))) for v in bbox[:4]]
            except (TypeError, ValueError):
                summary.missing_field += 1
                summary.rows.append(ManifestRow(
                    input_file=str(jsonl_path),
                    line_number=line_no,
                    status=STATUS_MISSING_FIELD,
                    source=source,
                    frame_index=int(frame_index) if isinstance(frame_index, (int, float)) else None,
                    reason='bbox_xyxy not numeric',
                ))
                continue

            x1, y1, x2, y2 = bbox_int
            if x2 <= x1 or y2 <= y1:
                summary.rejected_degenerate += 1
                summary.rows.append(ManifestRow(
                    input_file=str(jsonl_path),
                    line_number=line_no,
                    status=STATUS_REJECTED_DEGENERATE,
                    source=source,
                    frame_index=int(frame_index),
                    bbox_xyxy=bbox_int,
                    reason='x2<=x1 or y2<=y1',
                ))
                continue

            cx, cy, w_n, h_n = xyxy_to_yolo_norm(bbox_int, frame_width, frame_height)
            if not is_in_unit_bounds(cx, cy, w_n, h_n):
                summary.rejected_out_of_bounds += 1
                summary.rows.append(ManifestRow(
                    input_file=str(jsonl_path),
                    line_number=line_no,
                    status=STATUS_REJECTED_OOB,
                    source=source,
                    frame_index=int(frame_index),
                    bbox_xyxy=bbox_int,
                    yolo_xywh_norm=[cx, cy, w_n, h_n],
                    reason='normalized bbox outside [0, 1]',
                ))
                continue

            label_path = label_path_for(output_dir, source, int(frame_index))
            if not dry_run:
                output_dir.mkdir(parents=True, exist_ok=True)
                label_path.write_text(format_yolo_line(class_id, cx, cy, w_n, h_n), encoding='utf-8')
                summary.files_written += 1

            summary.ok += 1
            summary.rows.append(ManifestRow(
                input_file=str(jsonl_path),
                line_number=line_no,
                status=STATUS_OK,
                source=source,
                frame_index=int(frame_index),
                bbox_xyxy=bbox_int,
                label_path=str(label_path),
                yolo_xywh_norm=[cx, cy, w_n, h_n],
            ))


def write_manifest(
    summary: ExportSummary,
    *,
    manifest_dir: Path,
    formats: Iterable[str],
    dry_run: bool,
) -> dict[str, Path]:
    """Write manifest.{json,csv}.  Returns {format: path}.

    In dry-run still writes manifest (manifest itself is metadata, not a label).
    """
    if not dry_run:
        manifest_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    rows_dict = [asdict(r) for r in summary.rows]
    if 'json' in formats:
        path = manifest_dir / 'manifest.json'
        if not dry_run:
            path.write_text(json.dumps({
                'summary': {
                    'total_lines': summary.total_lines,
                    'ok': summary.ok,
                    'malformed_line': summary.malformed_line,
                    'missing_field': summary.missing_field,
                    'skipped_event': summary.skipped_event,
                    'rejected_out_of_bounds': summary.rejected_out_of_bounds,
                    'rejected_degenerate': summary.rejected_degenerate,
                    'files_written': summary.files_written,
                },
                'rows': rows_dict,
            }, indent=2), encoding='utf-8')
        written['json'] = path
    if 'csv' in formats:
        path = manifest_dir / 'manifest.csv'
        if not dry_run:
            with path.open('w', encoding='utf-8', newline='') as fh:
                writer = csv.writer(fh)
                writer.writerow([
                    'input_file', 'line_number', 'status',
                    'source', 'frame_index', 'bbox_xyxy',
                    'label_path', 'yolo_xywh_norm', 'reason',
                ])
                for r in summary.rows:
                    writer.writerow([
                        r.input_file, r.line_number, r.status,
                        r.source or '', r.frame_index if r.frame_index is not None else '',
                        json.dumps(r.bbox_xyxy) if r.bbox_xyxy is not None else '',
                        r.label_path or '',
                        json.dumps(r.yolo_xywh_norm) if r.yolo_xywh_norm is not None else '',
                        r.reason or '',
                    ])
        written['csv'] = path
    return written


def parse_manifest_formats(value: str) -> list[str]:
    if value == 'both':
        return ['json', 'csv']
    if value in ('json', 'csv'):
        return [value]
    raise ValueError(f'unknown manifest format: {value}')


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--input', type=Path, required=True,
                   help='JSONL file or directory containing operator annotation logs.')
    p.add_argument('--output-dir', type=Path,
                   default=Path('runs/operator_yolo_labels'),
                   help='Where to write YOLO .txt label files.')
    p.add_argument('--frame-width', type=int, required=True,
                   help='Frame width in px (jsonl does not currently store it).')
    p.add_argument('--frame-height', type=int, required=True,
                   help='Frame height in px (jsonl does not currently store it).')
    p.add_argument('--class-id', type=int, default=0,
                   help='YOLO class id to assign to all operator boxes (default 0).')
    p.add_argument('--dry-run', action='store_true',
                   help='Do not write label files; manifest is still written.')
    p.add_argument('--manifest-format', type=str, default='both',
                   choices=['json', 'csv', 'both'],
                   help='Manifest output format (default: both).')
    p.add_argument('--manifest-dir', type=Path, default=None,
                   help='Where to write manifest (default: --output-dir).')
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> ExportSummary:
    if args.frame_width <= 0 or args.frame_height <= 0:
        raise SystemExit(f'frame size must be > 0; got {args.frame_width}x{args.frame_height}')

    files = iter_input_files(args.input)
    if not files:
        raise SystemExit(f'no JSONL files found under: {args.input}')

    summary = ExportSummary()
    for jsonl_path in files:
        process_jsonl(
            jsonl_path,
            args.output_dir,
            frame_width=args.frame_width,
            frame_height=args.frame_height,
            class_id=args.class_id,
            dry_run=args.dry_run,
            summary=summary,
        )

    formats = parse_manifest_formats(args.manifest_format)
    manifest_dir = args.manifest_dir if args.manifest_dir is not None else args.output_dir
    write_manifest(summary, manifest_dir=manifest_dir, formats=formats, dry_run=args.dry_run)
    return summary


def print_summary(summary: ExportSummary, *, dry_run: bool) -> None:
    print('=== operator-annotations → YOLO export summary ===')
    print(f'  total_lines           : {summary.total_lines}')
    print(f'  ok                    : {summary.ok}')
    print(f'  files_written         : {summary.files_written}{" (dry-run)" if dry_run else ""}')
    print(f'  skipped_event         : {summary.skipped_event}')
    print(f'  malformed_line        : {summary.malformed_line}')
    print(f'  missing_field         : {summary.missing_field}')
    print(f'  rejected_out_of_bounds: {summary.rejected_out_of_bounds}')
    print(f'  rejected_degenerate   : {summary.rejected_degenerate}')


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    summary = run(args)
    print_summary(summary, dry_run=args.dry_run)
    return 0


if __name__ == '__main__':
    sys.exit(main())
