#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train YOLO model from dataset YAML with optional time budget.")
    p.add_argument("--data", type=Path, required=True, help="Path to dataset.yaml")
    p.add_argument("--model", type=Path, default=Path("models/yolo11n.pt"), help="Initial model or checkpoint")
    p.add_argument("--project", type=Path, default=Path("runs"), help="Ultralytics project dir")
    p.add_argument("--name", type=str, default="autotrain_yolo")
    p.add_argument("--device", type=str, default="mps")
    p.add_argument("--imgsz", type=int, default=736)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--epochs", type=int, default=1000)
    p.add_argument("--time-hours", type=float, default=0.0, help="If >0, stop by time budget.")
    p.add_argument("--patience", type=int, default=80)
    p.add_argument("--lr0", type=float, default=0.0025)
    p.add_argument("--lrf", type=float, default=0.01)
    p.add_argument("--cache", choices=["none", "disk", "ram"], default="disk")
    p.add_argument("--freeze", type=int, default=0)
    p.add_argument("--max-det", type=int, default=120, help="Maximum detections per image (affects NMS load).")
    p.add_argument("--conf", type=float, default=0.25, help="Confidence threshold used by validator/NMS.")
    p.add_argument("--iou", type=float, default=0.70, help="IoU threshold for NMS.")
    p.add_argument("--save-period", type=int, default=1, help="Save periodic checkpoints every N epochs.")
    p.add_argument(
        "--val",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run validation each epoch. Disable for faster/safer long runs.",
    )
    p.add_argument(
        "--plots",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Generate plots during training.",
    )
    p.add_argument("--resume", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.data.exists():
        raise FileNotFoundError(f"dataset yaml not found: {args.data}")
    if not args.model.exists() and not args.resume:
        raise FileNotFoundError(f"model not found: {args.model}")

    cache_value: bool | str = False
    if args.cache == "disk":
        cache_value = "disk"
    elif args.cache == "ram":
        cache_value = "ram"

    model = YOLO(str(args.model))
    kwargs = dict(
        data=str(args.data),
        epochs=int(args.epochs),
        imgsz=int(args.imgsz),
        batch=int(args.batch),
        device=args.device,
        workers=int(args.workers),
        project=str(args.project),
        name=args.name,
        exist_ok=True,
        patience=int(args.patience),
        lr0=float(args.lr0),
        lrf=float(args.lrf),
        optimizer="AdamW",
        weight_decay=5e-4,
        warmup_epochs=3.0,
        close_mosaic=15,
        mosaic=0.8,
        mixup=0.05,
        copy_paste=0.0,
        hsv_h=0.01,
        hsv_s=0.35,
        hsv_v=0.45,
        degrees=6.0,
        translate=0.06,
        scale=0.35,
        fliplr=0.5,
        amp=False,
        val=bool(args.val),
        max_det=int(args.max_det),
        conf=float(args.conf),
        iou=float(args.iou),
        cache=cache_value,
        save=True,
        save_period=max(1, int(args.save_period)),
        freeze=int(args.freeze),
        resume=bool(args.resume),
        plots=bool(args.plots),
    )
    if args.time_hours > 0:
        kwargs["time"] = float(args.time_hours)

    print(
        f"[INFO] Train start | data={args.data} model={args.model} device={args.device} "
        f"imgsz={args.imgsz} batch={args.batch} time={args.time_hours}h resume={args.resume} "
        f"val={args.val} max_det={args.max_det} conf={args.conf}"
    )
    model.train(**kwargs)

    save_dir = Path(model.trainer.save_dir)
    print(f"[INFO] save_dir: {save_dir}")
    print(f"[INFO] best: {save_dir / 'weights' / 'best.pt'}")
    print(f"[INFO] last: {save_dir / 'weights' / 'last.pt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
