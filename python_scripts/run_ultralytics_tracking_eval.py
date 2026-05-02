#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultralytics import YOLO

from uav_tracker.config import Config
from uav_tracker.evaluation import evaluate_source
from uav_tracker.modes import apply_runtime_mode
from uav_tracker.pipeline import VideoSession, apply_runtime_preset, parse_video_source
from uav_tracker.profile_io import available_presets, load_preset
from utils.geometry import iou


TRACKERS = {"bytetrack", "botsort"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Compare project tracking metrics with native Ultralytics tracker output."
    )
    p.add_argument("--pack-file", type=Path, default=Path("configs/regression_pack.csv"), help="CSV/TXT: source[,scene]")
    p.add_argument("--preset", type=str, default="night", help="Project preset from configs/")
    p.add_argument("--mode", type=str, default="", help="Optional runtime mode override.")
    p.add_argument("--device", type=str, default="", help="Optional device override.")
    p.add_argument("--imgsz", type=int, default=0, help="Optional imgsz override.")
    p.add_argument("--conf", type=float, default=0.0, help="Optional confidence override.")
    p.add_argument("--small-target", type=str, default="auto", choices=["auto", "on", "off"])
    p.add_argument("--model", type=str, default="", help="Explicit model path override.")
    p.add_argument("--tracker", type=str, default="bytetrack", choices=sorted(TRACKERS))
    p.add_argument("--tracker-config", type=Path, default=None, help="Optional custom Ultralytics tracker YAML path.")
    p.add_argument("--max-frames", type=int, default=0, help="Frame limit per source.")
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/ultralytics_tracking"))
    p.add_argument("--tag", type=str, default="")
    p.add_argument(
        "--skip-project",
        action="store_true",
        help="Run only native Ultralytics tracking metrics, without project pipeline baseline.",
    )
    return p.parse_args()


def _load_pack(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Pack file not found: {path}")
    rows: list[dict[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",", 1)]
        rows.append({"source": parts[0], "scene": parts[1].lower() if len(parts) > 1 and parts[1] else "unknown"})
    if not rows:
        raise ValueError(f"Pack file is empty: {path}")
    return rows


def _resolve_source_path(raw_source: str) -> str:
    if raw_source.isdigit():
        return raw_source
    path = Path(raw_source)
    if path.is_absolute() and path.exists():
        return str(path)
    if path.exists():
        return str(path)
    rooted = ROOT / path
    if rooted.exists():
        return str(rooted)
    return raw_source


def _resolve_small_target(flag: str, preset_data: dict[str, Any]) -> bool:
    if flag == "on":
        return True
    if flag == "off":
        return False
    return bool(preset_data.get("small_target_mode", False))


def _resolve_tracker_arg(tracker: str, tracker_config: Path | None) -> str:
    if tracker_config is not None and str(tracker_config).strip() not in {"", "."}:
        return str(tracker_config)
    return f"{tracker}.yaml"


def _build_cfg(args: argparse.Namespace) -> tuple[Config, bool]:
    if args.preset not in set(available_presets()):
        raise ValueError(f"Unknown preset: {args.preset}")
    cfg = Config()
    cfg, preset_data = load_preset(args.preset, cfg)
    if args.mode:
        cfg = apply_runtime_mode(cfg, args.mode)
    if args.device:
        cfg.DEVICE = args.device
    small_target = _resolve_small_target(args.small_target, preset_data)
    imgsz = args.imgsz if args.imgsz > 0 else int(cfg.IMG_SIZE)
    conf = args.conf if args.conf > 0 else float(cfg.CONF_THRESH)
    cfg = apply_runtime_preset(cfg, small_target_mode=small_target, imgsz=imgsz, conf=conf)
    if args.model:
        cfg.MODEL_PATH = args.model
    return cfg, small_target


def _select_native_track(boxes: Any, prefer_class_id: int) -> dict[str, Any] | None:
    if boxes is None or len(boxes) == 0:
        return None
    candidates: list[dict[str, Any]] = []
    for box in boxes:
        if getattr(box, "id", None) is None:
            continue
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cls_id = int(box.cls.item()) if box.cls is not None else -1
        conf = float(box.conf.item()) if box.conf is not None else 0.0
        candidates.append(
            {
                "track_id": int(box.id.item()),
                "bbox": (x1, y1, x2, y2),
                "cls_id": cls_id,
                "conf": conf,
            }
        )
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item["cls_id"] != prefer_class_id, -item["conf"], item["track_id"]))
    return candidates[0]


def _native_tracking_report(
    cfg: Config,
    source: str | int,
    *,
    tracker: str,
    tracker_config: Path | None,
    max_frames: int,
    report_path: Path,
) -> dict[str, Any]:
    session = VideoSession(cfg, source, manage_cv_windows=False)
    session.open()
    model = YOLO(cfg.MODEL_PATH)
    total_frames = 0
    gt_frames = 0
    active_frames = 0
    false_lock_frames = 0
    hits_iou_01 = 0
    gt_ious: list[float] = []
    active_id_changes = 0
    previous_active_id: int | None = None
    elapsed_video_sec = 0.0
    timings: list[float] = []
    tracker_arg = _resolve_tracker_arg(tracker, tracker_config)

    try:
        while True:
            ret, frame, meta = session.read()
            if not ret:
                break
            total_frames += 1
            source_fps = float(meta.get("source_fps") or 0.0)
            if source_fps > cfg.SOURCE_FPS_MIN_VALID:
                elapsed_video_sec += 1.0 / source_fps
            else:
                elapsed_video_sec += 1.0 / max(1.0, cfg.FALLBACK_FPS)

            t0 = time.perf_counter()
            results = model.track(
                frame,
                conf=float(cfg.CONF_THRESH),
                iou=float(cfg.IOU_THRESH),
                imgsz=int(cfg.IMG_SIZE),
                device=cfg.DEVICE,
                persist=True,
                classes=cfg.CLASSES,
                tracker=tracker_arg,
                verbose=False,
            )
            timings.append(time.perf_counter() - t0)

            selected = _select_native_track(results[0].boxes if results else None, int(cfg.PREFER_CLASS_ID))
            gt_bbox = meta.get("gt_bbox")
            if gt_bbox is not None:
                gt_frames += 1

            if selected is not None:
                active_frames += 1
                active_id = int(selected["track_id"])
                if previous_active_id is not None and active_id != previous_active_id:
                    active_id_changes += 1
                previous_active_id = active_id

                gt_iou = iou(selected["bbox"], gt_bbox) if gt_bbox is not None else 0.0
                if gt_bbox is not None:
                    gt_ious.append(gt_iou)
                    if gt_iou >= 0.10:
                        hits_iou_01 += 1
                if gt_bbox is None or gt_iou < 0.10:
                    false_lock_frames += 1
            else:
                previous_active_id = None

            if max_frames > 0 and total_frames >= max_frames:
                break
    finally:
        session.close()

    elapsed_safe = max(elapsed_video_sec, 1e-6)
    total_safe = max(total_frames, 1)
    report = {
        "report_type": "native_ultralytics_tracking",
        "source": str(source),
        "tracker": tracker,
        "tracker_config": tracker_arg,
        "model_path": cfg.MODEL_PATH,
        "device": cfg.DEVICE,
        "imgsz": cfg.IMG_SIZE,
        "conf": cfg.CONF_THRESH,
        "total_frames": total_frames,
        "gt_frames": gt_frames,
        "active_frames": active_frames,
        "active_presence_rate": round(active_frames / total_safe, 4),
        "false_lock_frames": false_lock_frames,
        "false_lock_rate": round(false_lock_frames / total_safe, 4),
        "hits_iou_01": hits_iou_01,
        "avg_gt_iou": round(sum(gt_ious) / max(1, len(gt_ious)), 4),
        "active_id_changes": active_id_changes,
        "active_id_changes_per_min": round(active_id_changes * 60.0 / elapsed_safe, 4) if elapsed_video_sec >= 5.0 else 0.0,
        "avg_fps": round(total_frames / max(sum(timings), 1e-6), 3),
        "elapsed_video_sec": round(elapsed_video_sec, 4),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _comparison_row(source: str, scene: str, project: dict[str, Any] | None, native: dict[str, Any]) -> dict[str, Any]:
    row = {
        "source": source,
        "scene": scene,
        "frames": int(native.get("total_frames", 0)),
        "tracker": native.get("tracker", ""),
        "native_presence": float(native.get("active_presence_rate", 0.0)),
        "native_idchg_pm": float(native.get("active_id_changes_per_min", 0.0)),
        "native_false_lock": float(native.get("false_lock_rate", 0.0)),
        "native_fps": float(native.get("avg_fps", 0.0)),
    }
    if project is not None:
        project_frames = max(1, int(project.get("total_frames", 0)))
        row.update(
            {
                "project_presence": round(float(project.get("active_presence_rate", 0.0)), 4),
                "project_idchg_pm": round(float(project.get("active_id_changes_per_min", 0.0)), 4),
                "project_false_lock": round(float(project.get("false_lock_rate", 0.0)), 4),
                "project_fps": round(float(project.get("avg_fps", 0.0)), 3),
                "project_lock_rate": round(float(project.get("lock_frames", 0)) / project_frames, 4),
            }
        )
        row["presence_delta"] = round(abs(row["native_presence"] - row["project_presence"]), 4)
        row["idchg_pm_delta"] = round(abs(row["native_idchg_pm"] - row["project_idchg_pm"]), 4)
        row["false_lock_delta"] = round(abs(row["native_false_lock"] - row["project_false_lock"]), 4)
        row["fps_delta"] = round(row["native_fps"] - row["project_fps"], 3)
    return row


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = [
        "source",
        "scene",
        "frames",
        "tracker",
        "project_presence",
        "native_presence",
        "presence_delta",
        "project_idchg_pm",
        "native_idchg_pm",
        "idchg_pm_delta",
        "project_false_lock",
        "native_false_lock",
        "false_lock_delta",
        "project_fps",
        "native_fps",
        "fps_delta",
        "project_lock_rate",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def main() -> int:
    args = parse_args()
    try:
        pack = _load_pack(args.pack_file)
        cfg, small_target = _build_cfg(args)
    except Exception as exc:
        print(f"[error] {exc}")
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    report_files: list[str] = []

    for item in pack:
        source = parse_video_source(_resolve_source_path(item["source"]))
        scene = item["scene"]
        source_name = Path(str(source)).stem if isinstance(source, str) else f"camera_{source}"

        project_report: dict[str, Any] | None = None
        if not args.skip_project:
            project_path = args.out_dir / f"{args.tag}{source_name}_project.json"
            project_report = evaluate_source(
                cfg,
                source=source,
                small_target_mode=small_target,
                max_frames=max(0, int(args.max_frames)),
                report_path=str(project_path),
            ).to_dict()
            report_files.append(str(project_path))

        native_path = args.out_dir / f"{args.tag}{source_name}_{args.tracker}.json"
        native_report = _native_tracking_report(
            cfg,
            source,
            tracker=args.tracker,
            tracker_config=args.tracker_config,
            max_frames=max(0, int(args.max_frames)),
            report_path=native_path,
        )
        report_files.append(str(native_path))

        row = _comparison_row(str(source), scene, project_report, native_report)
        rows.append(row)
        print(
            f"[track-eval] {source_name}: tracker={args.tracker} "
            f"native_presence={row['native_presence']:.3f} native_idchg/min={row['native_idchg_pm']:.2f} "
            f"native_false_lock={row['native_false_lock']:.3f}"
        )

    mean: dict[str, float] = {}
    for key in ("native_presence", "native_idchg_pm", "native_false_lock", "native_fps"):
        mean[key] = round(sum(float(row.get(key, 0.0)) for row in rows) / max(1, len(rows)), 4)
    if not args.skip_project:
        for key in ("project_presence", "project_idchg_pm", "project_false_lock", "project_fps", "presence_delta", "idchg_pm_delta", "false_lock_delta", "fps_delta"):
            mean[key] = round(sum(float(row.get(key, 0.0)) for row in rows) / max(1, len(rows)), 4)

    summary = {
        "report_type": "ultralytics_tracking_eval",
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "tag": args.tag,
        "pack_file": str(args.pack_file),
        "preset": args.preset,
        "tracker": args.tracker,
        "tracker_config": _resolve_tracker_arg(args.tracker, args.tracker_config),
        "model_path": cfg.MODEL_PATH,
        "device": cfg.DEVICE,
        "imgsz": cfg.IMG_SIZE,
        "conf": cfg.CONF_THRESH,
        "small_target_mode": small_target,
        "skip_project": bool(args.skip_project),
        "rows": rows,
        "mean": mean,
        "report_files": report_files,
        "decision": "measurement_only",
    }
    stem = f"{args.tag}tracking_eval_{args.preset}_{args.tracker}"
    out_json = args.out_dir / f"{stem}.json"
    out_csv = args.out_dir / f"{stem}.csv"
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_csv(out_csv, rows)
    print(f"[summary] json={out_json}")
    print(f"[summary] csv={out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
