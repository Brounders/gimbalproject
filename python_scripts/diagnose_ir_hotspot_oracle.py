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
from utils.geometry import iou


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GT-assisted oracle analysis for IR hotspot candidates.")
    p.add_argument("--preset", default="antiuav_thermal_hotspot")
    p.add_argument("--sources", nargs="+", required=True)
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/diagnostics/ir_hotspot_oracle"))
    p.add_argument("--max-frames", type=int, default=300)
    p.add_argument("--top-k", type=int, default=12)
    return p.parse_args()


def _source_name(source: str) -> str:
    return Path(source).stem.replace(" ", "_")


def diagnose(source: str, preset: str, top_k: int, max_frames: int, out_dir: Path) -> dict:
    cfg, _ = load_preset(preset)
    cfg.NIGHT_STICKY_ENABLED = False
    cfg.NIGHT_MAX_DETECTIONS = int(top_k)
    cfg.NIGHT_HOTSPOT_TOP_K = 0
    detector = NightSmallTargetDetector(cfg)
    session = VideoSession(cfg, source, manage_cv_windows=False)
    session.open()

    rows = []
    total = 0
    gt_frames = 0
    frames_with_candidates = 0
    top1_iou_values = []
    oracle_iou_values = []
    top1_hit_01 = 0
    oracle_hit_01 = 0
    top1_hit_03 = 0
    oracle_hit_03 = 0

    try:
        while True:
            ok, frame, meta = session.read()
            if not ok:
                break
            total += 1
            gt = meta.get("gt_bbox")
            dets = detector.detect(frame)
            if dets:
                frames_with_candidates += 1
            top1_iou = iou(dets[0]["bbox"], gt) if gt is not None and dets else 0.0
            oracle_iou = max((iou(det["bbox"], gt) for det in dets), default=0.0) if gt is not None else 0.0
            if gt is not None:
                gt_frames += 1
                top1_iou_values.append(top1_iou)
                oracle_iou_values.append(oracle_iou)
                if top1_iou >= 0.10:
                    top1_hit_01 += 1
                if oracle_iou >= 0.10:
                    oracle_hit_01 += 1
                if top1_iou >= 0.30:
                    top1_hit_03 += 1
                if oracle_iou >= 0.30:
                    oracle_hit_03 += 1
            rows.append({
                "frame": int(meta.get("frame_index", total - 1)),
                "gt": int(gt is not None),
                "candidate_count": len(dets),
                "top1_iou": round(top1_iou, 4),
                "oracle_iou": round(oracle_iou, 4),
                "top1_bbox": list(dets[0]["bbox"]) if dets else "",
                "oracle_bbox": list(max(dets, key=lambda det: iou(det["bbox"], gt))["bbox"]) if gt is not None and dets else "",
            })
            if max_frames > 0 and total >= max_frames:
                break
    finally:
        session.close()

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{_source_name(source)}_hotspot_oracle.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["frame"])
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "source": source,
        "preset": preset,
        "frames": total,
        "gt_frames": gt_frames,
        "candidate_presence_rate": round(frames_with_candidates / max(1, total), 4),
        "top1_avg_iou": round(mean(top1_iou_values), 4) if top1_iou_values else 0.0,
        "oracle_avg_iou": round(mean(oracle_iou_values), 4) if oracle_iou_values else 0.0,
        "top1_hit_01_rate": round(top1_hit_01 / max(1, gt_frames), 4) if gt_frames else None,
        "oracle_hit_01_rate": round(oracle_hit_01 / max(1, gt_frames), 4) if gt_frames else None,
        "top1_hit_03_rate": round(top1_hit_03 / max(1, gt_frames), 4) if gt_frames else None,
        "oracle_hit_03_rate": round(oracle_hit_03 / max(1, gt_frames), 4) if gt_frames else None,
        "csv": str(csv_path),
    }
    return summary


def main() -> int:
    args = parse_args()
    summaries = [diagnose(source, args.preset, args.top_k, args.max_frames, args.out_dir) for source in args.sources]
    summary_path = args.out_dir / "summary.json"
    summary_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(json.dumps(summaries, indent=2))
    print(f"[summary] {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
