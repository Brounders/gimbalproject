#!/usr/bin/env python3
"""Quick KPI smoke runner.

Runs a lightweight tracker evaluation on 1-3 short sources and prints a
compact KPI summary.  No pass/fail decision — use run_quality_gate.py for
gating.

Usage examples
--------------
# Single video, 300 frames, default preset
PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py \
    --sources /path/to/clip.mp4 --max-frames 300 --preset default

# CSV pack (same format as regression_pack.csv)
PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py \
    --pack configs/regression_pack.csv --max-frames 150 --preset night \
    --output-json runs/smoke/latest.json --output-csv runs/smoke/latest.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_tracker.config import Config
from uav_tracker.evaluation import evaluate_source
from uav_tracker.modes import apply_runtime_mode
from uav_tracker.pipeline import apply_runtime_preset
from uav_tracker.profile_io import available_presets, load_preset

# KPI fields exposed in compact summary
_KPI_FIELDS = [
    "source",
    "scene",
    "frames",
    "avg_fps",
    "active_id_changes_per_min",
    "lock_switches_per_min",
    "false_lock_rate",
    "continuity_score",
    "active_presence_rate",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Quick KPI smoke: lightweight tracker evaluation for fast regression checks."
    )
    src_group = p.add_mutually_exclusive_group(required=True)
    src_group.add_argument(
        "--sources",
        type=str,
        help="Comma-separated list of video paths / camera indices.",
    )
    src_group.add_argument(
        "--pack",
        type=Path,
        help="CSV pack file (source[,scene] per line, same format as regression_pack.csv).",
    )
    p.add_argument("--preset", type=str, default="default", help="Preset name from configs/.")
    p.add_argument("--mode", type=str, default="", help="Optional runtime mode override.")
    p.add_argument("--device", type=str, default="", help="Optional device override.")
    p.add_argument(
        "--max-frames",
        type=int,
        default=300,
        help="Max frames per source (0 = unlimited).",
    )
    p.add_argument("--output-json", type=Path, default=None, help="Write summary JSON to path.")
    p.add_argument("--output-csv", type=Path, default=None, help="Write summary CSV to path.")
    return p.parse_args()


def _load_pack(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Pack file not found: {path}")
    entries: list[dict[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",", 1)]
        entries.append({"source": parts[0], "scene": parts[1].lower() if len(parts) > 1 else "unknown"})
    if not entries:
        raise ValueError(f"Pack file is empty: {path}")
    return entries


def _load_sources_arg(sources_str: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for raw in sources_str.split(","):
        src = raw.strip()
        if src:
            entries.append({"source": src, "scene": "unknown"})
    return entries


def _resolve_source(raw: str) -> str:
    if raw.isdigit():
        return raw
    path = Path(raw)
    if path.is_absolute() and path.exists():
        return str(path)
    if path.exists():
        return str(path)
    rooted = ROOT / path
    if rooted.exists():
        return str(rooted)
    return raw


def _run_one(
    cfg: Config,
    entry: dict[str, str],
    max_frames: int,
) -> dict[str, Any]:
    source = _resolve_source(entry["source"])
    scene = entry.get("scene", "unknown")
    print(f"  [{scene}] {source} ...", end="", flush=True)
    report = evaluate_source(cfg, source, max_frames=max_frames)
    print(
        f" {report.total_frames}f  fps={report.avg_fps:.1f}  "
        f"id_chg/min={report.active_id_changes_per_min:.2f}  "
        f"sw/min={report.lock_switches_per_min:.2f}  "
        f"false_lock={report.false_lock_rate:.3f}"
    )
    return {
        "source": entry["source"],
        "scene": scene,
        "frames": report.total_frames,
        "avg_fps": round(report.avg_fps, 2),
        "active_id_changes_per_min": round(report.active_id_changes_per_min, 3),
        "lock_switches_per_min": round(report.lock_switches_per_min, 3),
        "false_lock_rate": round(report.false_lock_rate, 4),
        "continuity_score": round(report.continuity_score, 4),
        "active_presence_rate": round(report.active_presence_rate, 4),
    }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Simple mean across all sources for numeric KPI fields."""
    numeric = [f for f in _KPI_FIELDS if f not in ("source", "scene", "frames")]
    agg: dict[str, Any] = {"source": "__aggregate__", "scene": "all", "frames": sum(r["frames"] for r in rows)}
    for field in numeric:
        values = [r[field] for r in rows if field in r]
        agg[field] = round(sum(values) / len(values), 4) if values else 0.0
    return agg


def _write_json(path: Path, rows: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "rows": rows}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[smoke] JSON → {path}")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_KPI_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in _KPI_FIELDS})
    print(f"[smoke] CSV  → {path}")


def main() -> int:
    args = parse_args()

    if args.preset not in set(available_presets()):
        print(f"[error] Unknown preset: {args.preset}. Available: {available_presets()}")
        return 2

    if args.pack:
        try:
            entries = _load_pack(args.pack)
        except Exception as exc:
            print(f"[error] {exc}")
            return 2
    else:
        entries = _load_sources_arg(args.sources)

    if not entries:
        print("[error] No sources specified.")
        return 2

    cfg = Config()
    cfg, preset_data = load_preset(args.preset, cfg)
    if args.mode:
        cfg = apply_runtime_mode(cfg, args.mode)
    if args.device:
        cfg.DEVICE = args.device

    small_target = bool(preset_data.get("small_target_mode", False))
    cfg = apply_runtime_preset(cfg, small_target_mode=small_target)

    print(f"[smoke] preset={args.preset}  max_frames={args.max_frames}  sources={len(entries)}")
    print(f"[smoke] device={cfg.DEVICE}  imgsz={cfg.IMG_SIZE}  conf={cfg.CONF_THRESH}")
    print("-" * 64)

    rows: list[dict[str, Any]] = []
    errors = 0
    for entry in entries:
        try:
            row = _run_one(cfg, entry, args.max_frames)
            rows.append(row)
        except Exception as exc:
            print(f"  [ERROR] {entry['source']}: {exc}")
            errors += 1

    if not rows:
        print("[smoke] No results — all sources failed.")
        return 1

    agg = _aggregate(rows)
    all_rows = rows + [agg]

    print("-" * 64)
    print(
        f"[smoke] AGGREGATE  fps={agg['avg_fps']:.1f}  "
        f"id_chg/min={agg['active_id_changes_per_min']:.2f}  "
        f"sw/min={agg['lock_switches_per_min']:.2f}  "
        f"false_lock={agg['false_lock_rate']:.3f}"
    )
    if errors:
        print(f"[smoke] WARNING: {errors} source(s) failed.")

    meta = {
        "timestamp": datetime.utcnow().isoformat(),
        "preset": args.preset,
        "max_frames": args.max_frames,
        "sources": len(entries),
        "errors": errors,
    }

    if args.output_json:
        _write_json(args.output_json, all_rows, meta)
    if args.output_csv:
        _write_csv(args.output_csv, all_rows)

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
