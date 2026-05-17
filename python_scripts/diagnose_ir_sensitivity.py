#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_tracker.detectors.night_detector import NightSmallTargetDetector
from uav_tracker.pipeline import VideoSession
from uav_tracker.profile_io import load_preset
from uav_tracker.runtime import create_detector_backend
from utils.geometry import iou


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Raw detector sensitivity diagnostic for IR clips.")
    p.add_argument("--preset", default="antiuav_thermal")
    p.add_argument("--sources", nargs="+", required=True)
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/diagnostics/ir_sensitivity"))
    p.add_argument("--max-frames", type=int, default=300)
    p.add_argument("--confs", default="0.12,0.08,0.05")
    return p.parse_args()


def _best_gt_iou(detections, gt_bbox) -> float:
    if gt_bbox is None or not detections:
        return 0.0
    return max(iou(det.bbox, gt_bbox) for det in detections)


def _source_name(source: str) -> str:
    return Path(source).stem.replace(" ", "_")


def diagnose_source(source: str, preset: str, confs: list[float], max_frames: int, out_dir: Path) -> dict:
    cfg, _ = load_preset(preset)
    backend = create_detector_backend(cfg.MODEL_PATH, cfg.DEVICE)
    night = NightSmallTargetDetector(cfg)
    session = VideoSession(cfg, source, manage_cv_windows=False)
    session.open()

    rows = []
    frame_count = 0
    gt_frames = 0
    yolo_seen = {conf: 0 for conf in confs}
    yolo_gt_hit_01 = {conf: 0 for conf in confs}
    yolo_gt_hit_03 = {conf: 0 for conf in confs}
    yolo_det_counts = {conf: [] for conf in confs}
    yolo_best_ious = {conf: [] for conf in confs}
    night_seen = 0
    night_gt_hit_01 = 0
    night_gt_hit_03 = 0
    night_det_counts = []
    night_best_ious = []

    try:
        while True:
            ok, frame, meta = session.read()
            if not ok:
                break
            frame_count += 1
            gt_bbox = meta.get("gt_bbox")
            if gt_bbox is not None:
                gt_frames += 1

            row = {
                "frame": int(meta.get("frame_index", frame_count - 1)),
                "gt": int(gt_bbox is not None),
            }

            for conf in confs:
                dets = backend.predict_frame(frame, cfg, conf=conf, imgsz=cfg.IMG_SIZE)
                best = _best_gt_iou(dets, gt_bbox)
                count = len(dets)
                yolo_det_counts[conf].append(count)
                yolo_best_ious[conf].append(best)
                if count:
                    yolo_seen[conf] += 1
                if gt_bbox is not None and best >= 0.10:
                    yolo_gt_hit_01[conf] += 1
                if gt_bbox is not None and best >= 0.30:
                    yolo_gt_hit_03[conf] += 1
                row[f"yolo_count_conf_{conf:.2f}"] = count
                row[f"yolo_best_iou_conf_{conf:.2f}"] = round(best, 4)

            night_dets = night.detect(frame)
            night_best = max((iou(det["bbox"], gt_bbox) for det in night_dets), default=0.0) if gt_bbox is not None else 0.0
            night_det_counts.append(len(night_dets))
            night_best_ious.append(night_best)
            if night_dets:
                night_seen += 1
            if gt_bbox is not None and night_best >= 0.10:
                night_gt_hit_01 += 1
            if gt_bbox is not None and night_best >= 0.30:
                night_gt_hit_03 += 1
            row["night_count"] = len(night_dets)
            row["night_best_iou"] = round(night_best, 4)
            rows.append(row)

            if max_frames > 0 and frame_count >= max_frames:
                break
    finally:
        session.close()

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{_source_name(source)}_ir_sensitivity.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["frame"])
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "source": source,
        "preset": preset,
        "frames": frame_count,
        "gt_frames": gt_frames,
        "csv": str(csv_path),
        "yolo": {},
        "night": {
            "seen_rate": round(night_seen / max(1, frame_count), 4),
            "avg_count": round(mean(night_det_counts), 4) if night_det_counts else 0.0,
            "avg_best_gt_iou": round(mean(night_best_ious), 4) if night_best_ious else 0.0,
            "gt_hit_01_rate": round(night_gt_hit_01 / max(1, gt_frames), 4) if gt_frames else None,
            "gt_hit_03_rate": round(night_gt_hit_03 / max(1, gt_frames), 4) if gt_frames else None,
        },
    }
    for conf in confs:
        summary["yolo"][f"{conf:.2f}"] = {
            "seen_rate": round(yolo_seen[conf] / max(1, frame_count), 4),
            "avg_count": round(mean(yolo_det_counts[conf]), 4) if yolo_det_counts[conf] else 0.0,
            "avg_best_gt_iou": round(mean(yolo_best_ious[conf]), 4) if yolo_best_ious[conf] else 0.0,
            "gt_hit_01_rate": round(yolo_gt_hit_01[conf] / max(1, gt_frames), 4) if gt_frames else None,
            "gt_hit_03_rate": round(yolo_gt_hit_03[conf] / max(1, gt_frames), 4) if gt_frames else None,
        }
    return summary


def main() -> int:
    args = parse_args()
    confs = [float(item.strip()) for item in args.confs.split(",") if item.strip()]
    summaries = [
        diagnose_source(source, args.preset, confs, args.max_frames, args.out_dir)
        for source in args.sources
    ]
    summary_path = args.out_dir / "summary.json"
    summary_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(json.dumps(summaries, indent=2))
    print(f"[summary] {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
