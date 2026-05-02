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


SCENE_PRESET = {
    "day": "default",
    "ir": "antiuav_thermal",
    "night": "night",
    "noise": "default",
    "noisy": "default",
    "background": "default",
    "unknown": "default",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run reproducible OFF/ON gate for guarded ActionPolicy behavior."
    )
    p.add_argument(
        "--pack-file",
        type=Path,
        default=Path("configs/action_policy_gate_pack.csv"),
        help="CSV/TXT: source[,scene]. Scene controls preset when --preset is not set.",
    )
    p.add_argument(
        "--preset",
        type=str,
        default="",
        help="Optional preset override for all rows. Default: scene-specific preset mapping.",
    )
    p.add_argument("--mode", type=str, default="", help="Optional runtime mode override.")
    p.add_argument("--device", type=str, default="", help="Optional device override.")
    p.add_argument("--imgsz", type=int, default=0, help="Optional imgsz override.")
    p.add_argument("--conf", type=float, default=0.0, help="Optional confidence override.")
    p.add_argument("--small-target", type=str, default="auto", choices=["auto", "on", "off"])
    p.add_argument("--model", type=str, default="", help="Explicit model path override.")
    p.add_argument("--max-frames", type=int, default=0, help="Frame limit per source (0 = full clips).")
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/action_policy_gate"))
    p.add_argument("--tag", type=str, default="")
    p.add_argument(
        "--diagnostic",
        action="store_true",
        help="Mark every row diagnostic/non-blocking while still recording row failures.",
    )
    p.add_argument(
        "--diagnostic-scenes",
        type=str,
        default="",
        help="Comma-separated scene names to mark diagnostic/non-blocking.",
    )

    p.add_argument("--max-presence-drop", type=float, default=0.01)
    p.add_argument("--max-false-lock-increase", type=float, default=0.01)
    p.add_argument("--max-noise-presence-increase", type=float, default=0.01)
    p.add_argument("--max-noise-false-lock-increase", type=float, default=0.01)
    p.add_argument("--max-iou-drop", type=float, default=0.02)
    p.add_argument("--max-hit01-drop", type=int, default=2)
    p.add_argument("--max-fps-drop", type=float, default=5.0)
    p.add_argument("--max-drop-rate", type=float, default=0.02)
    return p.parse_args()


def load_pack(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Pack file not found: {path}")
    rows: list[dict[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",", 1)]
        rows.append({
            "source": parts[0],
            "scene": parts[1].lower() if len(parts) > 1 and parts[1] else "unknown",
        })
    if not rows:
        raise ValueError(f"Pack file is empty: {path}")
    return rows


def parse_scene_set(raw: str) -> set[str]:
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def resolve_source_path(raw_source: str) -> str:
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


def resolve_small_target(flag: str, preset_data: dict[str, Any]) -> bool:
    if flag == "on":
        return True
    if flag == "off":
        return False
    return bool(preset_data.get("small_target_mode", False))


def scene_preset(scene: str, override: str = "") -> str:
    if override:
        return override
    return SCENE_PRESET.get(scene.lower(), "default")


def build_cfg(args: argparse.Namespace, preset: str, *, behavior_enabled: bool) -> tuple[Config, bool]:
    if preset not in set(available_presets()):
        raise ValueError(f"Unknown preset: {preset}")
    cfg = Config()
    cfg, preset_data = load_preset(preset, cfg)
    if args.mode:
        cfg = apply_runtime_mode(cfg, args.mode)
    if args.device:
        cfg.DEVICE = args.device
    small_target = resolve_small_target(args.small_target, preset_data)
    imgsz = args.imgsz if args.imgsz > 0 else int(cfg.IMG_SIZE)
    conf = args.conf if args.conf > 0 else float(cfg.CONF_THRESH)
    cfg = apply_runtime_preset(cfg, small_target_mode=small_target, imgsz=imgsz, conf=conf)
    if args.model:
        cfg.MODEL_PATH = args.model
    cfg.ACTION_POLICY_BEHAVIOR_ENABLED = bool(behavior_enabled)
    return cfg, small_target


def compact_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "frames": int(report.get("total_frames", 0)),
        "gt_frames": int(report.get("gt_frames", 0)),
        "presence": round(float(report.get("active_presence_rate", 0.0)), 4),
        "false_lock": round(float(report.get("false_lock_rate", 0.0)), 4),
        "idchg_pm": round(float(report.get("active_id_changes_per_min", 0.0)), 4),
        "avg_gt_iou": round(float(report.get("avg_gt_iou", 0.0)), 4),
        "hits_iou_01": int(report.get("hits_iou_01", 0)),
        "hits_iou_05": int(report.get("hits_iou_05", 0)),
        "avg_fps": round(float(report.get("avg_fps", 0.0)), 3),
        "behavior_drop_count": int(report.get("behavior_drop_count", 0)),
    }


def pair_row(source: str, scene: str, preset: str, off: dict[str, Any], on: dict[str, Any]) -> dict[str, Any]:
    off_c = compact_report(off)
    on_c = compact_report(on)
    frames = max(1, int(on_c["frames"] or off_c["frames"] or 1))
    row: dict[str, Any] = {
        "source": source,
        "scene": scene,
        "preset": preset,
        "frames": on_c["frames"],
        "gt_frames": on_c["gt_frames"],
        "off_presence": off_c["presence"],
        "on_presence": on_c["presence"],
        "delta_presence": round(on_c["presence"] - off_c["presence"], 4),
        "off_false_lock": off_c["false_lock"],
        "on_false_lock": on_c["false_lock"],
        "delta_false_lock": round(on_c["false_lock"] - off_c["false_lock"], 4),
        "off_idchg_pm": off_c["idchg_pm"],
        "on_idchg_pm": on_c["idchg_pm"],
        "delta_idchg_pm": round(on_c["idchg_pm"] - off_c["idchg_pm"], 4),
        "off_avg_gt_iou": off_c["avg_gt_iou"],
        "on_avg_gt_iou": on_c["avg_gt_iou"],
        "delta_avg_gt_iou": round(on_c["avg_gt_iou"] - off_c["avg_gt_iou"], 4),
        "off_hits_iou_01": off_c["hits_iou_01"],
        "on_hits_iou_01": on_c["hits_iou_01"],
        "delta_hits_iou_01": int(on_c["hits_iou_01"] - off_c["hits_iou_01"]),
        "off_hits_iou_05": off_c["hits_iou_05"],
        "on_hits_iou_05": on_c["hits_iou_05"],
        "off_avg_fps": off_c["avg_fps"],
        "on_avg_fps": on_c["avg_fps"],
        "delta_avg_fps": round(on_c["avg_fps"] - off_c["avg_fps"], 3),
        "off_behavior_drop_count": off_c["behavior_drop_count"],
        "on_behavior_drop_count": on_c["behavior_drop_count"],
        "on_behavior_drop_rate": round(on_c["behavior_drop_count"] / frames, 4),
    }
    return row


def row_failures(row: dict[str, Any], args: argparse.Namespace) -> list[str]:
    failures: list[str] = []
    scene = str(row.get("scene", "")).lower()
    is_noise = scene in {"noise", "noisy", "background"}

    if int(row["off_behavior_drop_count"]) != 0:
        failures.append("off_behavior_drop_count_nonzero")
    if float(row["on_behavior_drop_rate"]) > float(args.max_drop_rate):
        failures.append(f"drop_rate>{args.max_drop_rate}")
    if float(row["delta_avg_fps"]) < -float(args.max_fps_drop):
        failures.append(f"fps_drop>{args.max_fps_drop}")

    if is_noise:
        if float(row["delta_presence"]) > float(args.max_noise_presence_increase):
            failures.append(f"noise_presence_increase>{args.max_noise_presence_increase}")
        if float(row["delta_false_lock"]) > float(args.max_noise_false_lock_increase):
            failures.append(f"noise_false_lock_increase>{args.max_noise_false_lock_increase}")
    else:
        if float(row["delta_presence"]) < -float(args.max_presence_drop):
            failures.append(f"presence_drop>{args.max_presence_drop}")
        if float(row["delta_false_lock"]) > float(args.max_false_lock_increase):
            failures.append(f"false_lock_increase>{args.max_false_lock_increase}")
        if float(row["delta_avg_gt_iou"]) < -float(args.max_iou_drop):
            failures.append(f"avg_iou_drop>{args.max_iou_drop}")
        if int(row["delta_hits_iou_01"]) < -int(args.max_hit01_drop):
            failures.append(f"hit01_drop>{args.max_hit01_drop}")

    return failures


def apply_row_decision(
    row: dict[str, Any],
    args: argparse.Namespace,
    *,
    diagnostic_scenes: set[str],
) -> list[str]:
    reasons = row_failures(row, args)
    scene = str(row.get("scene", "")).lower()
    is_diagnostic = bool(row.get("diagnostic", False)) or scene in diagnostic_scenes

    row["diagnostic"] = is_diagnostic
    row["passed"] = True if is_diagnostic else len(reasons) == 0
    row["fail_reasons"] = "" if is_diagnostic else ";".join(reasons)
    row["diagnostic_reasons"] = ";".join(reasons) if is_diagnostic else ""
    return reasons


def csv_write(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = [
        "source",
        "scene",
        "preset",
        "frames",
        "gt_frames",
        "off_presence",
        "on_presence",
        "delta_presence",
        "off_false_lock",
        "on_false_lock",
        "delta_false_lock",
        "off_idchg_pm",
        "on_idchg_pm",
        "delta_idchg_pm",
        "off_avg_gt_iou",
        "on_avg_gt_iou",
        "delta_avg_gt_iou",
        "off_hits_iou_01",
        "on_hits_iou_01",
        "delta_hits_iou_01",
        "off_avg_fps",
        "on_avg_fps",
        "delta_avg_fps",
        "off_behavior_drop_count",
        "on_behavior_drop_count",
        "on_behavior_drop_rate",
        "diagnostic",
        "passed",
        "fail_reasons",
        "diagnostic_reasons",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def mean_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    keys = [
        "delta_presence",
        "delta_false_lock",
        "delta_idchg_pm",
        "delta_avg_gt_iou",
        "delta_avg_fps",
        "on_behavior_drop_rate",
    ]
    return {
        key: round(sum(float(row.get(key, 0.0)) for row in rows) / max(1, len(rows)), 4)
        for key in keys
    }


def main() -> int:
    args = parse_args()
    diagnostic_scenes = parse_scene_set(args.diagnostic_scenes)
    try:
        pack = load_pack(args.pack_file)
    except Exception as exc:
        print(f"[error] {exc}")
        return 2

    if args.preset and args.preset not in set(available_presets()):
        print(f"[error] Unknown preset: {args.preset}")
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    report_files: list[str] = []

    for item in pack:
        raw_source = item["source"]
        scene = item["scene"]
        preset = scene_preset(scene, args.preset)
        source = parse_video_source(resolve_source_path(raw_source))
        source_name = Path(str(source)).stem if isinstance(source, str) else f"camera_{source}"

        cfg_off, small_target = build_cfg(args, preset, behavior_enabled=False)
        cfg_on, _ = build_cfg(args, preset, behavior_enabled=True)

        off_path = args.out_dir / f"{args.tag}{source_name}_{preset}_off.json"
        on_path = args.out_dir / f"{args.tag}{source_name}_{preset}_on.json"
        off = evaluate_source(
            cfg_off,
            source=source,
            small_target_mode=small_target,
            max_frames=max(0, int(args.max_frames)),
            report_path=str(off_path),
        ).to_dict()
        on = evaluate_source(
            cfg_on,
            source=source,
            small_target_mode=small_target,
            max_frames=max(0, int(args.max_frames)),
            report_path=str(on_path),
        ).to_dict()
        report_files.extend([str(off_path), str(on_path)])

        row = pair_row(str(source), scene, preset, off, on)
        if args.diagnostic:
            row["diagnostic"] = True
        row_reasons = apply_row_decision(row, args, diagnostic_scenes=diagnostic_scenes)
        if row_reasons and not row["diagnostic"]:
            failures.append(f"{row['source']}: {row['fail_reasons']}")
        rows.append(row)
        print(
            f"[clip] {source_name} scene={scene} preset={preset} "
            f"diagnostic={row['diagnostic']} pass={row['passed']} "
            f"presence {row['off_presence']:.3f}->{row['on_presence']:.3f} "
            f"false_lock {row['off_false_lock']:.3f}->{row['on_false_lock']:.3f} "
            f"idchg/min {row['off_idchg_pm']:.2f}->{row['on_idchg_pm']:.2f} "
            f"drops={row['on_behavior_drop_count']}"
        )

    passed = len(failures) == 0
    summary = {
        "report_type": "action_policy_gate",
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "tag": args.tag,
        "pack_file": str(args.pack_file),
        "preset_override": args.preset,
        "device": args.device,
        "imgsz": args.imgsz,
        "conf": args.conf,
        "small_target": args.small_target,
        "max_frames": args.max_frames,
        "diagnostic": bool(args.diagnostic),
        "diagnostic_scenes": sorted(diagnostic_scenes),
        "thresholds": {
            "max_presence_drop": args.max_presence_drop,
            "max_false_lock_increase": args.max_false_lock_increase,
            "max_noise_presence_increase": args.max_noise_presence_increase,
            "max_noise_false_lock_increase": args.max_noise_false_lock_increase,
            "max_iou_drop": args.max_iou_drop,
            "max_hit01_drop": args.max_hit01_drop,
            "max_fps_drop": args.max_fps_drop,
            "max_drop_rate": args.max_drop_rate,
        },
        "gate_passed": passed,
        "rows": rows,
        "mean": mean_metrics(rows),
        "failures": failures,
        "report_files": report_files,
    }

    stem = f"{args.tag}action_policy_gate"
    out_json = args.out_dir / f"{stem}.json"
    out_csv = args.out_dir / f"{stem}.csv"
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    csv_write(out_csv, rows)

    print(f"[summary] pass={passed} json={out_json}")
    print(f"[summary] csv={out_csv}")
    if failures:
        for failure in failures:
            print(f"[fail] {failure}")
    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
