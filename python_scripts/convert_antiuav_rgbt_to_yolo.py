#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import cv2


VALID_SPLITS = ("train", "val", "test")
VALID_MODALITIES = ("infrared", "visible")


@dataclass
class ConvertStats:
    sequences_total: int = 0
    sequences_used: int = 0
    frames_read: int = 0
    frames_saved: int = 0
    frames_skipped_no_target: int = 0
    frames_skipped_sampling: int = 0
    frames_skipped_invalid_box: int = 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert Anti-UAV-RGBT videos + json labels to YOLO format.")
    p.add_argument("--dataset-root", type=Path, required=True, help="Path to Anti-UAV-RGBT root.")
    p.add_argument("--out-root", type=Path, required=True, help="Output YOLO dataset root.")
    p.add_argument(
        "--splits",
        type=str,
        default="train,val,test",
        help="Comma-separated source splits (train,val,test).",
    )
    p.add_argument(
        "--modalities",
        type=str,
        default="infrared",
        help="Comma-separated modalities: infrared,visible.",
    )
    p.add_argument("--sample-step", type=int, default=20, help="Keep every N-th frame.")
    p.add_argument("--max-frames-per-seq", type=int, default=40, help="Max saved frames per sequence/modality.")
    p.add_argument("--max-sequences-per-split", type=int, default=0, help="0 = all.")
    p.add_argument("--min-box-size", type=float, default=3.0, help="Min width/height of valid bbox in pixels.")
    p.add_argument("--class-id", type=int, default=0, help="YOLO class id for UAV.")
    p.add_argument("--jpg-quality", type=int, default=90, help="JPEG quality (1..100).")
    return p.parse_args()


def _ensure_clean_dirs(out_root: Path, splits: list[str]) -> None:
    for split in splits:
        (out_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_root / "labels" / split).mkdir(parents=True, exist_ok=True)


def _clip_bbox(x: float, y: float, w: float, h: float, fw: int, fh: int) -> tuple[float, float, float, float] | None:
    x1 = max(0.0, min(float(fw - 1), x))
    y1 = max(0.0, min(float(fh - 1), y))
    x2 = max(0.0, min(float(fw - 1), x + w))
    y2 = max(0.0, min(float(fh - 1), y + h))
    bw = x2 - x1
    bh = y2 - y1
    if bw <= 0.0 or bh <= 0.0:
        return None
    return x1, y1, bw, bh


def _to_yolo_line(class_id: int, x: float, y: float, w: float, h: float, fw: int, fh: int) -> str:
    cx = (x + w / 2.0) / float(fw)
    cy = (y + h / 2.0) / float(fh)
    nw = w / float(fw)
    nh = h / float(fh)
    cx = min(max(cx, 0.0), 1.0)
    cy = min(max(cy, 0.0), 1.0)
    nw = min(max(nw, 1e-6), 1.0)
    nh = min(max(nh, 1e-6), 1.0)
    return f"{class_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n"


def _convert_one_sequence(
    seq_dir: Path,
    split: str,
    modality: str,
    out_root: Path,
    sample_step: int,
    max_frames_per_seq: int,
    min_box_size: float,
    class_id: int,
    jpg_quality: int,
    stats: ConvertStats,
) -> int:
    json_path = seq_dir / f"{modality}.json"
    video_path = seq_dir / f"{modality}.mp4"
    if not json_path.exists() or not video_path.exists():
        return 0

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return 0

    exists = payload.get("exist")
    rects = payload.get("gt_rect")
    if not isinstance(exists, list) or not isinstance(rects, list):
        return 0
    n = min(len(exists), len(rects))
    if n <= 0:
        return 0

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 0

    saved = 0
    frame_idx = 0
    seq_name = seq_dir.name
    out_img_dir = out_root / "images" / split
    out_lbl_dir = out_root / "labels" / split
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(max(1, min(100, jpg_quality)))]

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        stats.frames_read += 1

        if frame_idx >= n:
            break
        if sample_step > 1 and (frame_idx % sample_step) != 0:
            stats.frames_skipped_sampling += 1
            frame_idx += 1
            continue
        if int(exists[frame_idx]) != 1:
            stats.frames_skipped_no_target += 1
            frame_idx += 1
            continue

        box = rects[frame_idx]
        if not isinstance(box, list) or len(box) < 4:
            stats.frames_skipped_invalid_box += 1
            frame_idx += 1
            continue

        x, y, w, h = float(box[0]), float(box[1]), float(box[2]), float(box[3])
        fh, fw = frame.shape[:2]
        clipped = _clip_bbox(x, y, w, h, fw=fw, fh=fh)
        if clipped is None:
            stats.frames_skipped_invalid_box += 1
            frame_idx += 1
            continue
        x, y, w, h = clipped
        if w < min_box_size or h < min_box_size:
            stats.frames_skipped_invalid_box += 1
            frame_idx += 1
            continue

        stem = f"{split}_{seq_name}_{modality}_{frame_idx:06d}"
        img_path = out_img_dir / f"{stem}.jpg"
        lbl_path = out_lbl_dir / f"{stem}.txt"

        ok_write = cv2.imwrite(str(img_path), frame, encode_params)
        if not ok_write:
            frame_idx += 1
            continue
        lbl_path.write_text(_to_yolo_line(class_id, x, y, w, h, fw=fw, fh=fh), encoding="utf-8")
        saved += 1
        stats.frames_saved += 1

        if max_frames_per_seq > 0 and saved >= max_frames_per_seq:
            break
        frame_idx += 1

    cap.release()
    return saved


def main() -> int:
    args = parse_args()
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    modalities = [m.strip() for m in args.modalities.split(",") if m.strip()]

    for split in splits:
        if split not in VALID_SPLITS:
            raise ValueError(f"Unsupported split: {split}")
    for mod in modalities:
        if mod not in VALID_MODALITIES:
            raise ValueError(f"Unsupported modality: {mod}")
    if not args.dataset_root.exists():
        raise FileNotFoundError(f"Dataset root not found: {args.dataset_root}")

    _ensure_clean_dirs(args.out_root, splits)
    stats = ConvertStats()

    for split in splits:
        split_root = args.dataset_root / split
        if not split_root.exists():
            print(f"[warn] split not found, skip: {split_root}")
            continue

        seq_dirs = sorted([p for p in split_root.iterdir() if p.is_dir()])
        stats.sequences_total += len(seq_dirs)
        if args.max_sequences_per_split > 0:
            seq_dirs = seq_dirs[: args.max_sequences_per_split]

        used_in_split = 0
        for seq_dir in seq_dirs:
            seq_saved_any = False
            for mod in modalities:
                saved = _convert_one_sequence(
                    seq_dir=seq_dir,
                    split=split,
                    modality=mod,
                    out_root=args.out_root,
                    sample_step=max(1, int(args.sample_step)),
                    max_frames_per_seq=max(0, int(args.max_frames_per_seq)),
                    min_box_size=float(args.min_box_size),
                    class_id=int(args.class_id),
                    jpg_quality=int(args.jpg_quality),
                    stats=stats,
                )
                if saved > 0:
                    seq_saved_any = True
            if seq_saved_any:
                used_in_split += 1
        stats.sequences_used += used_in_split
        print(f"[info] split={split}: used_sequences={used_in_split}/{len(seq_dirs)}")

    yolo_yaml = args.out_root / "dataset.yaml"
    yolo_yaml.write_text(
        "\n".join(
            [
                f"path: {args.out_root.resolve()}",
                "train: images/train",
                "val: images/val",
                "test: images/test",
                "nc: 1",
                "names:",
                "  0: drone",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("[summary]")
    print(f"  sequences_total:         {stats.sequences_total}")
    print(f"  sequences_used:          {stats.sequences_used}")
    print(f"  frames_read:             {stats.frames_read}")
    print(f"  frames_saved:            {stats.frames_saved}")
    print(f"  skipped_sampling:        {stats.frames_skipped_sampling}")
    print(f"  skipped_no_target:       {stats.frames_skipped_no_target}")
    print(f"  skipped_invalid_box:     {stats.frames_skipped_invalid_box}")
    print(f"  output:                  {args.out_root}")
    print(f"  dataset_yaml:            {yolo_yaml}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
