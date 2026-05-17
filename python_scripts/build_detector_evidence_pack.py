#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

import cv2

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_tracker.detectors.night_detector import NightSmallTargetDetector
from uav_tracker.profile_io import load_preset
from uav_tracker.runtime import create_detector_backend
from utils.geometry import iou


@dataclass(frozen=True)
class GtRow:
    source: str
    frame_index: int
    visible: bool
    bbox: tuple[int, int, int, int] | None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build detector evidence pack from Target Lab GT CSV files.")
    p.add_argument("--gt-files", nargs="+", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/detector_evidence_pack"))
    p.add_argument("--yolo-preset", default="tracking_live_auto")
    p.add_argument("--night-presets", default="tracking_live_auto,antiuav_thermal_peak,antiuav_thermal_hotspot")
    p.add_argument("--confs", default="0.30,0.12,0.08,0.05")
    p.add_argument("--sample-step", type=int, default=5)
    p.add_argument("--max-sampled-visible", type=int, default=180)
    return p.parse_args()


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _bbox(row: dict[str, str]) -> tuple[int, int, int, int] | None:
    try:
        vals = [row.get(k, "") for k in ("x1", "y1", "x2", "y2")]
        if any(str(v).strip() == "" for v in vals):
            return None
        x1, y1, x2, y2 = [int(float(v)) for v in vals]
    except ValueError:
        return None
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def load_gt(files: list[Path], sample_step: int, max_sampled_visible: int) -> dict[str, list[GtRow]]:
    by_source: dict[str, list[GtRow]] = defaultdict(list)
    for path in files:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            visible_seen = 0
            for row in reader:
                source = str(row.get("source", "")).strip()
                if not source:
                    continue
                frame_index = int(float(row.get("frame_index", "0") or 0))
                visible = _truthy(row.get("visible", ""))
                bbox = _bbox(row) if visible else None
                if visible:
                    visible_seen += 1
                    if sample_step > 1 and visible_seen % sample_step != 1:
                        continue
                    if max_sampled_visible > 0 and len([r for r in by_source[source] if r.visible]) >= max_sampled_visible:
                        continue
                by_source[source].append(GtRow(source, frame_index, visible, bbox))
    return {source: sorted(rows, key=lambda item: item.frame_index) for source, rows in by_source.items()}


def _best_iou_detections(detections: list[Any], gt_bbox: tuple[int, int, int, int] | None) -> float:
    if gt_bbox is None or not detections:
        return 0.0
    return max(iou(det.bbox, gt_bbox) for det in detections)


def _best_iou_night(detections: list[dict[str, Any]], gt_bbox: tuple[int, int, int, int] | None) -> float:
    if gt_bbox is None or not detections:
        return 0.0
    return max(iou(det["bbox"], gt_bbox) for det in detections)


def _safe_stem(source: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in Path(source).stem)[:100]


def diagnose_source(
    source: str,
    rows: list[GtRow],
    *,
    yolo_preset: str,
    night_presets: list[str],
    confs: list[float],
    out_dir: Path,
) -> dict[str, Any]:
    source_path = Path(source)
    if not source_path.exists():
        return {"source": source, "error": "source_missing"}

    yolo_cfg, _ = load_preset(yolo_preset)
    backend = create_detector_backend(yolo_cfg.MODEL_PATH, yolo_cfg.DEVICE)
    night_detectors: dict[str, NightSmallTargetDetector] = {}
    for preset in night_presets:
        cfg, _ = load_preset(preset)
        night_detectors[preset] = NightSmallTargetDetector(cfg)

    wanted = {row.frame_index: row for row in rows}
    max_frame = max(wanted) if wanted else 0
    cap = cv2.VideoCapture(str(source_path))
    if not cap.isOpened():
        return {"source": source, "error": "source_open_failed"}

    per_frame: list[dict[str, Any]] = []
    frame_index = 0
    try:
        while frame_index <= max_frame:
            ok, frame = cap.read()
            if not ok:
                break
            gt = wanted.get(frame_index)
            night_results: dict[str, tuple[int, float]] = {}
            for preset, detector in night_detectors.items():
                dets = detector.detect(frame)
                night_results[preset] = (len(dets), _best_iou_night(dets, gt.bbox if gt else None))
            if gt is not None:
                row: dict[str, Any] = {
                    "source": source,
                    "clip": source_path.stem,
                    "frame_index": frame_index,
                    "visible": int(gt.visible),
                }
                for conf in confs:
                    dets = backend.predict_frame(frame, yolo_cfg, conf=conf, imgsz=yolo_cfg.IMG_SIZE)
                    row[f"yolo_count_{conf:.2f}"] = len(dets)
                    row[f"yolo_iou_{conf:.2f}"] = round(_best_iou_detections(dets, gt.bbox), 4)
                for preset, (count, best_iou) in night_results.items():
                    key = preset.replace("-", "_")
                    row[f"{key}_count"] = count
                    row[f"{key}_iou"] = round(best_iou, 4)
                per_frame.append(row)
            frame_index += 1
    finally:
        cap.release()

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{_safe_stem(source)}_detector_evidence.csv"
    if per_frame:
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(per_frame[0].keys()))
            writer.writeheader()
            writer.writerows(per_frame)

    visible_rows = [row for row in per_frame if int(row["visible"]) == 1]
    summary: dict[str, Any] = {
        "source": source,
        "clip": source_path.stem,
        "sampled_frames": len(per_frame),
        "visible_frames": len(visible_rows),
        "csv": str(csv_path),
        "yolo": {},
        "night": {},
    }
    best_hit = 0.0
    best_label = ""
    for conf in confs:
        vals = [float(row[f"yolo_iou_{conf:.2f}"]) for row in visible_rows]
        hit01 = sum(1 for value in vals if value >= 0.10) / max(1, len(vals))
        hit03 = sum(1 for value in vals if value >= 0.30) / max(1, len(vals))
        summary["yolo"][f"{conf:.2f}"] = {
            "avg_iou": round(mean(vals), 4) if vals else 0.0,
            "hit01": round(hit01, 4),
            "hit03": round(hit03, 4),
        }
        if hit01 > best_hit:
            best_hit = hit01
            best_label = f"yolo@{conf:.2f}"
    for preset in night_presets:
        key = preset.replace("-", "_")
        vals = [float(row[f"{key}_iou"]) for row in visible_rows]
        hit01 = sum(1 for value in vals if value >= 0.10) / max(1, len(vals))
        hit03 = sum(1 for value in vals if value >= 0.30) / max(1, len(vals))
        presence = sum(1 for row in visible_rows if int(row[f"{key}_count"]) > 0) / max(1, len(visible_rows))
        summary["night"][preset] = {
            "presence": round(presence, 4),
            "avg_iou": round(mean(vals), 4) if vals else 0.0,
            "hit01": round(hit01, 4),
            "hit03": round(hit03, 4),
        }
        if hit01 > best_hit:
            best_hit = hit01
            best_label = preset
    if best_hit < 0.10:
        diagnosis = "detector_absent_or_wrong"
    elif best_hit < 0.45:
        diagnosis = "weak_detector_training_needed"
    elif best_label.startswith("yolo"):
        diagnosis = "yolo_signal_exists_tune_or_train"
    else:
        diagnosis = "night_signal_exists_ranking_or_semantics"
    summary["best_hit01"] = round(best_hit, 4)
    summary["best_source"] = best_label
    summary["diagnosis"] = diagnosis
    return summary


def write_outputs(summaries: list[dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")
    headers = ["clip", "sampled_frames", "visible_frames", "best_source", "best_hit01", "diagnosis", "csv"]
    with (out_dir / "summary.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for row in summaries:
            writer.writerow({key: row.get(key, "") for key in headers})
    lines = ["# Detector Evidence Pack", ""]
    lines.append("| Clip | Frames | Best source | Hit@0.1 | Diagnosis |")
    lines.append("|---|---:|---|---:|---|")
    for row in summaries:
        lines.append(
            f"| {row.get('clip', '')} | {row.get('visible_frames', 0)} | "
            f"{row.get('best_source', '')} | {row.get('best_hit01', 0):.3f} | {row.get('diagnosis', '')} |"
        )
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    confs = [float(item.strip()) for item in args.confs.split(",") if item.strip()]
    night_presets = [item.strip() for item in args.night_presets.split(",") if item.strip()]
    gt_by_source = load_gt(args.gt_files, max(1, args.sample_step), max(0, args.max_sampled_visible))
    summaries = [
        diagnose_source(
            source,
            rows,
            yolo_preset=args.yolo_preset,
            night_presets=night_presets,
            confs=confs,
            out_dir=args.out_dir,
        )
        for source, rows in gt_by_source.items()
    ]
    write_outputs(summaries, args.out_dir)
    print(json.dumps(summaries, indent=2, ensure_ascii=False))
    print(f"[detector-evidence] {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
