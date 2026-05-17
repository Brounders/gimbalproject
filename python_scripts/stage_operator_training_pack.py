"""stage_operator_training_pack.py — assemble a YOLO-style training pack
from accepted/staged operator annotations.

Reads ``runs/operator_annotations/*.jsonl`` plus ``dts_review_state.json`` and
produces:

    <output-dir>/
      images/train/<stem>__f<NNNNNN>.jpg
      images/val/<stem>__f<NNNNNN>.jpg
      labels/train/<stem>__f<NNNNNN>.txt
      labels/val/<stem>__f<NNNNNN>.txt
      manifest.json
      data.yaml          (minimal: train/val image dirs)

Train/val split is deterministic (stable hash on record_id, default ratio 0.8).
Frames are extracted from the source video via cv2.  Records whose source video
is missing or whose frame cannot be read are listed in the manifest as
``skipped_frame``.

Training is **not** started by this script.

Usage::

    python stage_operator_training_pack.py \
        --log-dir runs/operator_annotations/ \
        --state-file runs/operator_annotations/dts_review_state.json \
        --output-dir runs/operator_training_packs/pack_v01/ \
        --val-ratio 0.2
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.training_desk_data import (  # noqa: E402
    AnnotationRecord,
    hard_negative_records,
    load_annotation_records,
    training_candidate_records,
)


@dataclass
class StagingResult:
    record_id: str
    # status: 'ok' | 'skipped_status' | 'skipped_invalid' | 'skipped_source' | 'skipped_frame'
    #         'negative_ok' | 'negative_skipped_conflict' | 'negative_skipped_ratio' | 'negative_skipped_invalid'
    status: str
    split: str = ''
    image_path: str = ''
    label_path: str = ''
    reason: str = ''
    sample_type: str = 'positive'  # 'positive' | 'negative_background'


def _stable_split(record_id: str, val_ratio: float) -> str:
    """Deterministic train/val routing."""
    h = hashlib.sha1(record_id.encode('utf-8')).hexdigest()
    bucket = int(h[:8], 16) / 0xFFFFFFFF
    return 'val' if bucket < val_ratio else 'train'


def _xyxy_to_yolo(bbox: tuple[int, int, int, int], frame_w: int, frame_h: int) -> Optional[tuple[float, float, float, float]]:
    x1, y1, x2, y2 = bbox
    if x2 <= x1 or y2 <= y1 or frame_w <= 0 or frame_h <= 0:
        return None
    cx = (x1 + x2) / 2.0 / float(frame_w)
    cy = (y1 + y2) / 2.0 / float(frame_h)
    w = (x2 - x1) / float(frame_w)
    h = (y2 - y1) / float(frame_h)
    if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
        return None
    return cx, cy, w, h


def _source_key(source: str) -> str:
    """Normalize a source path for conflict-key comparisons.

    Camera index strings (digits) are returned as-is.  Real paths are resolved
    to absolute form when the file exists; otherwise the POSIX string is used so
    that absolute and relative forms of the same path still match.
    """
    if source.isdigit():
        return source
    p = Path(source)
    try:
        if p.exists():
            return str(p.resolve())
    except OSError:
        pass
    return p.as_posix()


def stage_pack(
    *,
    log_dir: Path,
    state_file: Path,
    output_dir: Path,
    val_ratio: float = 0.2,
    class_id: int = 0,
    statuses_to_include: tuple[str, ...] = ('accepted', 'staged'),
    extract_frames: bool = True,
    neg_ratio: float = 1.0,
) -> dict:
    """Build a training pack at *output_dir*.  Returns a manifest dict."""
    images_train = output_dir / 'images' / 'train'
    images_val = output_dir / 'images' / 'val'
    labels_train = output_dir / 'labels' / 'train'
    labels_val = output_dir / 'labels' / 'val'
    for d in (images_train, images_val, labels_train, labels_val):
        d.mkdir(parents=True, exist_ok=True)

    cv2 = None
    if extract_frames:
        try:
            import cv2 as _cv2  # type: ignore
            cv2 = _cv2
        except Exception:
            cv2 = None

    all_records = load_annotation_records(log_dir, state_path=state_file)
    candidate_records = training_candidate_records(all_records)
    candidate_ids = {record.record_id for record in candidate_records if record.status in statuses_to_include}

    results: list[StagingResult] = []
    for record in all_records:
        if record.event != 'operator_bbox':
            continue
        if record.record_id not in candidate_ids:
            results.append(StagingResult(record_id=record.record_id, status='skipped_status', reason=record.status))
            continue

        source = record.source
        frame_index = int(record.frame_index)
        bbox = record.bbox_xyxy
        if bbox is None or not source or frame_index < 0:
            results.append(StagingResult(record_id=record.record_id, status='skipped_invalid',
                                         reason='missing fields'))
            continue

        src_path = Path(source)
        if not src_path.exists():
            results.append(StagingResult(record_id=record.record_id, status='skipped_source',
                                         reason=f'no file {source}'))
            continue

        split = _stable_split(record.record_id, val_ratio)
        stem = src_path.stem
        base_name = f'{stem}__f{frame_index:06d}'
        label_dir = labels_val if split == 'val' else labels_train
        image_dir = images_val if split == 'val' else images_train
        label_path = label_dir / f'{base_name}.txt'
        image_path = image_dir / f'{base_name}.jpg'

        # Read frame to know frame size + persist image (if cv2 is available).
        frame = None
        frame_w = frame_h = 0
        if cv2 is not None:
            cap = cv2.VideoCapture(str(src_path))
            try:
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_index))
                    ok, frame = cap.read()
            finally:
                cap.release()
            if frame is not None:
                frame_h, frame_w = frame.shape[:2]
        if frame is None or frame_w <= 0 or frame_h <= 0:
            results.append(StagingResult(record_id=record.record_id, status='skipped_frame',
                                         reason=f'cannot read frame {frame_index}'))
            continue

        yolo = _xyxy_to_yolo(bbox, frame_w, frame_h)
        if yolo is None:
            results.append(StagingResult(record_id=record.record_id, status='skipped_invalid',
                                         reason='bbox out of bounds after norm'))
            continue
        cx, cy, w, h = yolo
        label_path.write_text(
            f'{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n',
            encoding='utf-8',
        )
        if extract_frames and cv2 is not None:
            cv2.imwrite(str(image_path), frame)

        results.append(StagingResult(
            record_id=record.record_id,
            status='ok',
            split=split,
            image_path=str(image_path),
            label_path=str(label_path),
            sample_type='positive',
        ))

    # ── Hard negatives ────────────────────────────────────────────────────
    # Budget: floor(positive_ok * neg_ratio). Zero positives → zero negatives.
    positive_ok_count = sum(1 for r in results if r.status == 'ok')
    neg_budget = math.floor(positive_ok_count * neg_ratio)
    neg_used = 0

    # Conflict set: normalized (source, frame_index) of all accepted/staged candidates.
    # Built from candidate_records (not results) so annotations on temporarily
    # unavailable videos still block the corresponding hard negative frame.
    positive_keys: set[tuple[str, int]] = {
        (_source_key(record.source), int(record.frame_index))
        for record in candidate_records
    }

    for neg in hard_negative_records(all_records):
        key = (_source_key(neg.source), int(neg.frame_index))
        if key in positive_keys:
            results.append(StagingResult(record_id=neg.record_id, status='negative_skipped_conflict',
                                         reason='same source+frame has accepted positive', sample_type='negative_background'))
            continue
        if neg_used >= neg_budget:
            results.append(StagingResult(record_id=neg.record_id, status='negative_skipped_ratio',
                                         reason=f'neg_budget={neg_budget} exhausted', sample_type='negative_background'))
            continue

        src_path = Path(neg.source)
        if not src_path.exists():
            results.append(StagingResult(record_id=neg.record_id, status='negative_skipped_invalid',
                                         reason=f'no file {neg.source}', sample_type='negative_background'))
            continue

        split = _stable_split(neg.record_id, val_ratio)
        stem = src_path.stem
        base_name = f'{stem}__f{int(neg.frame_index):06d}__neg'
        label_dir = labels_val if split == 'val' else labels_train
        image_dir = images_val if split == 'val' else images_train
        label_path = label_dir / f'{base_name}.txt'
        image_path = image_dir / f'{base_name}.jpg'

        # Extract frame for image if cv2 available
        frame = None
        frame_w = frame_h = 0
        if cv2 is not None:
            cap = cv2.VideoCapture(str(src_path))
            try:
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(neg.frame_index)))
                    ok, frame = cap.read()
            finally:
                cap.release()
            if frame is not None:
                frame_h, frame_w = frame.shape[:2]

        if cv2 is not None and (frame is None or frame_w <= 0 or frame_h <= 0):
            results.append(StagingResult(record_id=neg.record_id, status='negative_skipped_invalid',
                                         reason=f'cannot read frame {neg.frame_index}', sample_type='negative_background'))
            continue

        # Empty label = full-frame negative (no annotations)
        label_path.write_text('', encoding='utf-8')
        if extract_frames and cv2 is not None and frame is not None:
            cv2.imwrite(str(image_path), frame)

        neg_used += 1
        results.append(StagingResult(
            record_id=neg.record_id,
            status='negative_ok',
            split=split,
            image_path=str(image_path),
            label_path=str(label_path),
            sample_type='negative_background',
        ))

    # Manifest
    manifest = {
        'output_dir': str(output_dir),
        'val_ratio': val_ratio,
        'class_id': class_id,
        'neg_ratio': neg_ratio,
        'statuses_to_include': list(statuses_to_include),
        'counts': {
            'ok': sum(1 for r in results if r.status == 'ok'),
            'positive_ok': sum(1 for r in results if r.status == 'ok'),
            'negative_ok': sum(1 for r in results if r.status == 'negative_ok'),
            'negative_skipped_conflict': sum(1 for r in results if r.status == 'negative_skipped_conflict'),
            'negative_skipped_ratio': sum(1 for r in results if r.status == 'negative_skipped_ratio'),
            'negative_skipped_invalid': sum(1 for r in results if r.status == 'negative_skipped_invalid'),
            'skipped_status': sum(1 for r in results if r.status == 'skipped_status'),
            'skipped_invalid': sum(1 for r in results if r.status == 'skipped_invalid'),
            'skipped_source': sum(1 for r in results if r.status == 'skipped_source'),
            'skipped_frame': sum(1 for r in results if r.status == 'skipped_frame'),
        },
        'records': [asdict(r) for r in results],
    }
    (output_dir / 'manifest.json').write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    with (output_dir / 'manifest.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['record_id', 'status', 'split', 'image_path', 'label_path', 'reason'])
        for r in results:
            writer.writerow([r.record_id, r.status, r.split, r.image_path, r.label_path, r.reason])

    # Minimal data.yaml so Ultralytics can ingest the pack.
    yaml_text = (
        f"# operator training pack assembled by stage_operator_training_pack.py\n"
        f"path: {output_dir}\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"names:\n"
        f"  {class_id}: drone\n"
    )
    (output_dir / 'data.yaml').write_text(yaml_text, encoding='utf-8')
    return manifest


# ── CLI ────────────────────────────────────────────────────────────────────


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--log-dir', type=Path,
                   default=ROOT / 'runs' / 'operator_annotations',
                   help='Directory with operator annotation jsonl files.')
    p.add_argument('--state-file', type=Path,
                   default=ROOT / 'runs' / 'operator_annotations' / 'dts_review_state.json',
                   help='DTS review state json file.')
    p.add_argument('--output-dir', type=Path, required=True,
                   help='Directory to write the YOLO-style training pack.')
    p.add_argument('--val-ratio', type=float, default=0.2,
                   help='Fraction of records routed to images/val (default: 0.2).')
    p.add_argument('--class-id', type=int, default=0,
                   help='YOLO class id for operator labels (default: 0).')
    p.add_argument('--no-extract', action='store_true',
                   help='Skip writing images, only write labels + manifest.')
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    if not (0.0 <= args.val_ratio < 1.0):
        print(f'ERROR: --val-ratio must be in [0, 1), got {args.val_ratio}', file=sys.stderr)
        return 2
    manifest = stage_pack(
        log_dir=args.log_dir,
        state_file=args.state_file,
        output_dir=args.output_dir,
        val_ratio=args.val_ratio,
        class_id=args.class_id,
        extract_frames=not args.no_extract,
    )
    print(json.dumps(manifest['counts'], indent=2, ensure_ascii=False))
    print(f'\nPack: {args.output_dir}')
    print(f'Manifest: {args.output_dir / "manifest.json"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
