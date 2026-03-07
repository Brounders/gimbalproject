#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_tracker.config import Config
from uav_tracker.evaluation import evaluate_source
from uav_tracker.modes import apply_runtime_mode
from uav_tracker.pipeline import apply_runtime_preset, parse_video_source
from uav_tracker.profile_io import available_presets, load_preset


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Offline benchmark over fixed video list.")
    p.add_argument("--sources", type=str, default="", help="Comma-separated list of video paths.")
    p.add_argument(
        "--source-list",
        type=Path,
        default=None,
        help="Text file with one source path per line. Optional second CSV column: scene tag (day/night/ir/noise).",
    )
    p.add_argument("--preset", type=str, default="night", help="Preset from configs/")
    p.add_argument("--mode", type=str, default="", help="Optional runtime mode override.")
    p.add_argument("--device", type=str, default="", help="Optional device override (mps/cpu/hailo).")
    p.add_argument("--imgsz", type=int, default=0, help="Optional imgsz override.")
    p.add_argument("--conf", type=float, default=0.0, help="Optional conf override.")
    p.add_argument("--small-target", type=str, default="auto", choices=["auto", "on", "off"])
    p.add_argument("--max-frames", type=int, default=0, help="Frame limit per source (0 = all).")
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/benchmark"))
    p.add_argument("--tag", type=str, default="")
    return p.parse_args()


def _collect_sources(args: argparse.Namespace) -> list[dict]:
    result: list[dict] = []
    if args.sources.strip():
        for item in [x.strip() for x in args.sources.split(",") if x.strip()]:
            result.append({"source": item, "scene": "unknown"})
    if args.source_list is not None and args.source_list.exists():
        for line in args.source_list.read_text(encoding="utf-8").splitlines():
            item = line.strip()
            if item and not item.startswith("#"):
                parts = [p.strip() for p in item.split(",", 1)]
                source = parts[0]
                scene = parts[1] if len(parts) > 1 and parts[1] else "unknown"
                result.append({"source": source, "scene": scene.lower()})
    return result


def _resolve_small_target(flag: str, preset_data: dict) -> bool:
    if flag == "on":
        return True
    if flag == "off":
        return False
    return bool(preset_data.get("small_target_mode", False))


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


def _row_score(row: dict) -> float:
    return (
        40.0 * float(row.get("lock_rate", 0.0))
        + 15.0 * float(row.get("continuity_score", 0.0))
        + 12.0 * float(row.get("active_presence_rate", 0.0))
        + 20.0 * min(float(row.get("avg_fps", 0.0)) / 30.0, 1.0)
        - 6.0 * float(row.get("lock_switches_per_min", 0.0))
        - 8.0 * float(row.get("active_id_changes_per_min", 0.0))
        - 18.0 * float(row.get("false_lock_rate", 0.0))
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    headers = [
        "source",
        "scene",
        "frames",
        "lock_rate",
        "lock_frames",
        "avg_fps",
        "continuity_score",
        "active_presence_rate",
        "active_id_changes",
        "active_id_changes_per_min",
        "lost_events",
        "lock_switches_per_min",
        "false_lock_frames",
        "false_lock_rate",
        "score",
    ]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(key, "")) for key in headers))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_list = _collect_sources(args)
    if not source_list:
        print("[error] No sources provided. Use --sources or --source-list.")
        return 2
    if args.preset not in set(available_presets()):
        print(f"[error] Unknown preset: {args.preset}")
        return 2

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

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    generated_reports: list[str] = []

    for item in source_list:
        source = parse_video_source(_resolve_source_path(item["source"]))
        scene = str(item.get("scene", "unknown")).lower()
        source_name = Path(str(source)).stem if isinstance(source, str) else f"camera_{source}"
        report_path = args.out_dir / f"{args.tag}{source_name}_{args.preset}.json"
        report = evaluate_source(
            cfg,
            source=source,
            small_target_mode=small_target,
            max_frames=max(0, int(args.max_frames)),
            report_path=str(report_path),
        ).to_dict()
        total_frames = max(1, int(report.get("total_frames", 0)))
        false_lock_frames = int(report.get("false_lock_frames", 0))
        row = {
            "source": str(source),
            "scene": scene,
            "frames": int(report.get("total_frames", 0)),
            "lock_frames": int(report.get("lock_frames", 0)),
            "lock_rate": round(float(report.get("lock_frames", 0)) / total_frames, 4),
            "avg_fps": round(float(report.get("avg_fps", 0.0)), 3),
            "continuity_score": round(float(report.get("continuity_score", 0.0)), 4),
            "active_presence_rate": round(float(report.get("active_presence_rate", 0.0)), 4),
            "active_id_changes": int(report.get("active_id_changes", 0)),
            "active_id_changes_per_min": round(float(report.get("active_id_changes_per_min", 0.0)), 4),
            "lost_events": int(report.get("lock_event_counts", {}).get("lost", 0)),
            "lock_switches_per_min": round(float(report.get("lock_switches_per_min", 0.0)), 4),
            "false_lock_frames": false_lock_frames,
            "false_lock_rate": round(float(report.get("false_lock_rate", 0.0)), 4),
        }
        row["score"] = round(_row_score(row), 3)
        rows.append(row)
        generated_reports.append(str(report_path))
        print(
            f"[done] {source_name}: lock={row['lock_rate']:.3f} fps={row['avg_fps']:.1f} "
            f"idchg/min={row['active_id_changes_per_min']:.2f} sw/min={row['lock_switches_per_min']:.2f} "
            f"false_lock={row['false_lock_rate']:.3f} score={row['score']:.2f}"
        )

    overall = {
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "preset": args.preset,
        "runtime_mode": cfg.RUNTIME_MODE,
        "device": cfg.DEVICE,
        "imgsz": cfg.IMG_SIZE,
        "conf": cfg.CONF_THRESH,
        "small_target_mode": small_target,
        "rows": rows,
        "mean": {
            "lock_rate": round(sum(r["lock_rate"] for r in rows) / max(1, len(rows)), 4),
            "avg_fps": round(sum(r["avg_fps"] for r in rows) / max(1, len(rows)), 3),
            "continuity_score": round(sum(r["continuity_score"] for r in rows) / max(1, len(rows)), 4),
            "active_presence_rate": round(sum(r["active_presence_rate"] for r in rows) / max(1, len(rows)), 4),
            "active_id_changes": round(sum(r["active_id_changes"] for r in rows) / max(1, len(rows)), 3),
            "active_id_changes_per_min": round(sum(r["active_id_changes_per_min"] for r in rows) / max(1, len(rows)), 4),
            "lost_events": round(sum(r["lost_events"] for r in rows) / max(1, len(rows)), 3),
            "lock_switches_per_min": round(sum(r["lock_switches_per_min"] for r in rows) / max(1, len(rows)), 4),
            "false_lock_rate": round(sum(r["false_lock_rate"] for r in rows) / max(1, len(rows)), 4),
            "score": round(sum(r["score"] for r in rows) / max(1, len(rows)), 3),
        },
        "report_files": generated_reports,
    }

    stem = f"{args.tag}benchmark_{args.preset}"
    out_json = args.out_dir / f"{stem}.json"
    out_csv = args.out_dir / f"{stem}.csv"
    out_json.write_text(json.dumps(overall, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_csv(out_csv, rows)

    print(f"[summary] json={out_json}")
    print(f"[summary] csv={out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
