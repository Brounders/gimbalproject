#!/usr/bin/env python3
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
from uav_tracker.pipeline import apply_runtime_preset, parse_video_source
from uav_tracker.profile_io import available_presets, load_preset


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Deterministic quality gate for tracker stability.")
    p.add_argument("--pack-file", type=Path, default=Path("configs/regression_pack.csv"), help="CSV/TXT: source[,scene]")
    p.add_argument("--preset", type=str, default="night", help="Preset from configs/")
    p.add_argument("--mode", type=str, default="", help="Optional runtime mode override")
    p.add_argument("--device", type=str, default="", help="Optional device override")
    p.add_argument("--imgsz", type=int, default=0, help="Optional imgsz override")
    p.add_argument("--conf", type=float, default=0.0, help="Optional conf override")
    p.add_argument("--small-target", type=str, default="auto", choices=["auto", "on", "off"])
    p.add_argument("--max-frames", type=int, default=0, help="Frame limit per source")
    p.add_argument("--model", type=str, default="", help="Explicit model path override for candidate evaluation (bypasses preset model_path).")
    p.add_argument("--baseline", type=Path, default=None, help="Previous quality_gate JSON for regression comparison")

    p.add_argument("--min-avg-fps", type=float, default=8.0)
    p.add_argument("--max-lock-switches-per-min", type=float, default=6.0)
    p.add_argument("--max-id-changes-per-min", type=float, default=8.0)
    p.add_argument("--min-continuity", type=float, default=0.45)
    p.add_argument("--min-presence", type=float, default=0.08)
    p.add_argument("--max-false-lock-rate", type=float, default=0.35)
    p.add_argument("--max-noise-false-lock-rate", type=float, default=0.18)
    p.add_argument("--max-noise-id-changes-per-min", type=float, default=15.0,
                   help="Max active_id_changes_per_min for noise/background scenes (default: 15.0).")

    p.add_argument("--allow-baseline-fps-drop", type=float, default=1.0)
    p.add_argument("--allow-baseline-continuity-drop", type=float, default=0.03)
    p.add_argument("--allow-baseline-presence-drop", type=float, default=0.03)
    p.add_argument("--allow-baseline-idchg-increase", type=float, default=0.3)
    p.add_argument("--allow-baseline-swpm-increase", type=float, default=0.2)
    p.add_argument("--allow-baseline-false-lock-increase", type=float, default=0.02)

    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/quality_gate"))
    p.add_argument("--tag", type=str, default="")
    p.add_argument(
        "--context",
        type=str,
        default="",
        choices=["day", "night", "ir"],
        help=(
            "Preset context shorthand: auto-selects --pack-file and --preset. "
            "day=default+regression_pack_day.csv, "
            "night=night+regression_pack_night.csv, "
            "ir=antiuav_thermal+regression_pack_ir.csv. "
            "Overrides --preset and --pack-file when specified."
        ),
    )
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
        source = parts[0]
        scene = parts[1].lower() if len(parts) > 1 and parts[1] else "unknown"
        entries.append({"source": source, "scene": scene})

    if not entries:
        raise ValueError(f"Pack file is empty: {path}")
    return entries


def _resolve_small_target(flag: str, preset_data: dict[str, Any]) -> bool:
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


def _score_row(row: dict[str, Any]) -> float:
    return (
        40.0 * float(row.get("lock_rate", 0.0))
        + 15.0 * float(row.get("continuity_score", 0.0))
        + 12.0 * float(row.get("active_presence_rate", 0.0))
        + 20.0 * min(float(row.get("avg_fps", 0.0)) / 30.0, 1.0)
        - 6.0 * float(row.get("lock_switches_per_min", 0.0))
        - 8.0 * float(row.get("active_id_changes_per_min", 0.0))
        - 18.0 * float(row.get("false_lock_rate", 0.0))
    )


def _csv_write(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = [
        "source",
        "scene",
        "frames",
        "avg_fps",
        "lock_rate",
        "continuity_score",
        "active_presence_rate",
        "active_id_changes",
        "active_id_changes_per_min",
        "lock_switches_per_min",
        "false_lock_frames",
        "false_lock_rate",
        "score",
        "passed",
        "fail_reasons",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in headers})


def _load_baseline(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    mapping: dict[str, dict[str, Any]] = {}
    for row in rows:
        source = str(row.get("source", "")).strip()
        if not source:
            continue
        mapping[source] = row
        mapping[Path(source).name] = row
        mapping[Path(source).stem] = row
    return mapping


def _find_baseline_row(mapping: dict[str, dict[str, Any]], source: str) -> dict[str, Any] | None:
    return mapping.get(source) or mapping.get(Path(source).name) or mapping.get(Path(source).stem)


_CONTEXT_MAP: dict[str, tuple[str, Path]] = {
    "day":   ("default",         Path("configs/regression_pack_day.csv")),
    "night": ("night",           Path("configs/regression_pack_night.csv")),
    "ir":    ("antiuav_thermal", Path("configs/regression_pack_ir.csv")),
}


def main() -> int:
    args = parse_args()

    if args.context:
        args.preset, args.pack_file = _CONTEXT_MAP[args.context]

    if args.preset not in set(available_presets()):
        print(f"[error] Unknown preset: {args.preset}")
        return 2

    try:
        pack = _load_pack(args.pack_file)
    except Exception as exc:
        print(f"[error] {exc}")
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
    if args.model:
        cfg.MODEL_PATH = args.model

    baseline_rows = _load_baseline(args.baseline)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    failures: list[str] = []

    for item in pack:
        source = parse_video_source(_resolve_source_path(item["source"]))
        scene = item["scene"]
        source_name = Path(str(source)).stem if isinstance(source, str) else f"camera_{source}"
        report_path = args.out_dir / f"{args.tag}{source_name}_{args.preset}.json"

        try:
            report = evaluate_source(
                cfg,
                source=source,
                small_target_mode=small_target,
                max_frames=max(0, int(args.max_frames)),
                report_path=str(report_path),
            ).to_dict()
        except Exception as exc:
            print(f"[error] {source_name}: {exc}")
            failed_row: dict[str, Any] = {
                "source": str(source), "scene": scene, "frames": 0,
                "avg_fps": 0.0, "lock_rate": 0.0, "continuity_score": 0.0,
                "active_presence_rate": 0.0, "active_id_changes": 0,
                "active_id_changes_per_min": 0.0, "lock_switches_per_min": 0.0,
                "false_lock_frames": 0, "false_lock_rate": 0.0, "mode_counts": {},
                "score": 0.0, "passed": False,
                "fail_reasons": f"evaluate_error:{type(exc).__name__}",
            }
            rows.append(failed_row)
            failures.append(f"{source}: evaluate_error:{type(exc).__name__}")
            continue

        total_frames = max(1, int(report.get("total_frames", 0)))
        row = {
            "source": str(source),
            "scene": scene,
            "frames": int(report.get("total_frames", 0)),
            "avg_fps": round(float(report.get("avg_fps", 0.0)), 3),
            "lock_rate": round(float(report.get("lock_frames", 0)) / total_frames, 4),
            "continuity_score": round(float(report.get("continuity_score", 0.0)), 4),
            "active_presence_rate": round(float(report.get("active_presence_rate", 0.0)), 4),
            "active_id_changes": int(report.get("active_id_changes", 0)),
            "active_id_changes_per_min": round(float(report.get("active_id_changes_per_min", 0.0)), 4),
            "lock_switches_per_min": round(float(report.get("lock_switches_per_min", 0.0)), 4),
            "false_lock_frames": int(report.get("false_lock_frames", 0)),
            "false_lock_rate": round(float(report.get("false_lock_rate", 0.0)), 4),
            "mode_counts": report.get("mode_counts", {}),
        }
        row["score"] = round(_score_row(row), 3)

        row_failures: list[str] = []
        if float(row["avg_fps"]) < float(args.min_avg_fps):
            row_failures.append(f"fps<{args.min_avg_fps}")
        if float(row["lock_switches_per_min"]) > float(args.max_lock_switches_per_min):
            row_failures.append(f"swpm>{args.max_lock_switches_per_min}")
        is_noise = scene in {"noise", "noisy", "background"}
        if is_noise:
            if float(row["active_id_changes_per_min"]) > float(args.max_noise_id_changes_per_min):
                row_failures.append(f"noise_idchg/min>{args.max_noise_id_changes_per_min}")
        else:
            if float(row["active_id_changes_per_min"]) > float(args.max_id_changes_per_min):
                row_failures.append(f"idchg/min>{args.max_id_changes_per_min}")

        false_lock_limit = float(args.max_noise_false_lock_rate if is_noise else args.max_false_lock_rate)
        if float(row["false_lock_rate"]) > false_lock_limit:
            row_failures.append(f"false_lock_rate>{false_lock_limit}")

        if not is_noise:
            if float(row["continuity_score"]) < float(args.min_continuity):
                row_failures.append(f"continuity<{args.min_continuity}")
            if float(row["active_presence_rate"]) < float(args.min_presence):
                row_failures.append(f"presence<{args.min_presence}")

        baseline = _find_baseline_row(baseline_rows, row["source"])
        if baseline is not None:
            base_fps = float(baseline.get("avg_fps", 0.0))
            base_cont = float(baseline.get("continuity_score", 0.0))
            base_presence = float(baseline.get("active_presence_rate", 0.0))
            base_idchg = float(baseline.get("active_id_changes_per_min", 0.0))
            base_swpm = float(baseline.get("lock_switches_per_min", 0.0))
            base_false_lock = float(baseline.get("false_lock_rate", 0.0))

            if float(row["avg_fps"]) < base_fps - float(args.allow_baseline_fps_drop):
                row_failures.append("baseline_fps_regression")
            if float(row["continuity_score"]) < base_cont - float(args.allow_baseline_continuity_drop):
                row_failures.append("baseline_continuity_regression")
            if float(row["active_presence_rate"]) < base_presence - float(args.allow_baseline_presence_drop):
                row_failures.append("baseline_presence_regression")
            if float(row["active_id_changes_per_min"]) > base_idchg + float(args.allow_baseline_idchg_increase):
                row_failures.append("baseline_idchg_regression")
            if float(row["lock_switches_per_min"]) > base_swpm + float(args.allow_baseline_swpm_increase):
                row_failures.append("baseline_swpm_regression")
            if float(row["false_lock_rate"]) > base_false_lock + float(args.allow_baseline_false_lock_increase):
                row_failures.append("baseline_false_lock_regression")

        row["passed"] = len(row_failures) == 0
        row["fail_reasons"] = ";".join(row_failures)
        if row_failures:
            failures.append(f"{row['source']}: {row['fail_reasons']}")

        rows.append(row)
        print(
            f"[clip] {source_name} scene={scene} pass={row['passed']} "
            f"fps={row['avg_fps']:.1f} idchg/min={row['active_id_changes_per_min']:.2f} "
            f"sw/min={row['lock_switches_per_min']:.2f} false_lock={row['false_lock_rate']:.3f}"
        )

    means = {
        "avg_fps": round(sum(float(r["avg_fps"]) for r in rows) / max(1, len(rows)), 3),
        "lock_rate": round(sum(float(r["lock_rate"]) for r in rows) / max(1, len(rows)), 4),
        "continuity_score": round(sum(float(r["continuity_score"]) for r in rows) / max(1, len(rows)), 4),
        "active_presence_rate": round(sum(float(r["active_presence_rate"]) for r in rows) / max(1, len(rows)), 4),
        "active_id_changes_per_min": round(sum(float(r["active_id_changes_per_min"]) for r in rows) / max(1, len(rows)), 4),
        "lock_switches_per_min": round(sum(float(r["lock_switches_per_min"]) for r in rows) / max(1, len(rows)), 4),
        "false_lock_rate": round(sum(float(r["false_lock_rate"]) for r in rows) / max(1, len(rows)), 4),
        "score": round(sum(float(r["score"]) for r in rows) / max(1, len(rows)), 3),
    }

    passed = len(failures) == 0
    summary = {
        "report_type": "quality_gate",
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "pack_file": str(args.pack_file),
        "preset": args.preset,
        "context": args.context if args.context else "",
        "runtime_mode": cfg.RUNTIME_MODE,
        "device": cfg.DEVICE,
        "imgsz": cfg.IMG_SIZE,
        "conf": cfg.CONF_THRESH,
        "small_target_mode": small_target,
        "thresholds": {
            "min_avg_fps": args.min_avg_fps,
            "max_lock_switches_per_min": args.max_lock_switches_per_min,
            "max_id_changes_per_min": args.max_id_changes_per_min,
            "min_continuity": args.min_continuity,
            "min_presence": args.min_presence,
            "max_false_lock_rate": args.max_false_lock_rate,
            "max_noise_false_lock_rate": args.max_noise_false_lock_rate,
            "max_noise_id_changes_per_min": args.max_noise_id_changes_per_min,
        },
        "baseline": str(args.baseline) if args.baseline else "",
        "gate_passed": passed,
        "rows": rows,
        "mean": means,
        "failures": failures,
    }

    stem = f"{args.tag}quality_gate_{args.preset}"
    out_json = args.out_dir / f"{stem}.json"
    out_csv = args.out_dir / f"{stem}.csv"
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _csv_write(out_csv, rows)

    print(f"[summary] pass={passed} json={out_json}")
    print(f"[summary] csv={out_csv}")
    if failures:
        for item in failures:
            print(f"[fail] {item}")

    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
