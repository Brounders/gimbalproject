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
    p = argparse.ArgumentParser(description="Parity check across two tracker backend profiles on identical clips.")
    p.add_argument("--pack-file", type=Path, default=Path("configs/regression_pack.csv"), help="CSV/TXT: source[,scene]")
    p.add_argument("--left-preset", type=str, default="night")
    p.add_argument("--right-preset", type=str, default="rpi_hailo")
    p.add_argument("--left-label", type=str, default="mac")
    p.add_argument("--right-label", type=str, default="embedded")
    p.add_argument("--left-mode", type=str, default="")
    p.add_argument("--right-mode", type=str, default="")
    p.add_argument("--left-device", type=str, default="")
    p.add_argument("--right-device", type=str, default="")
    p.add_argument("--left-imgsz", type=int, default=0)
    p.add_argument("--right-imgsz", type=int, default=0)
    p.add_argument("--left-conf", type=float, default=0.0)
    p.add_argument("--right-conf", type=float, default=0.0)
    p.add_argument("--left-small-target", type=str, default="auto", choices=["auto", "on", "off"])
    p.add_argument("--right-small-target", type=str, default="auto", choices=["auto", "on", "off"])
    p.add_argument("--max-frames", type=int, default=0)

    p.add_argument("--max-lock-rate-delta", type=float, default=0.08)
    p.add_argument("--max-continuity-delta", type=float, default=0.10)
    p.add_argument("--max-presence-delta", type=float, default=0.12)
    p.add_argument("--max-idchg-pm-delta", type=float, default=1.2)
    p.add_argument("--max-swpm-delta", type=float, default=1.0)
    p.add_argument("--max-false-lock-rate-delta", type=float, default=0.06)
    p.add_argument("--max-track-ratio-delta", type=float, default=0.12)
    p.add_argument("--max-lost-ratio-delta", type=float, default=0.12)
    p.add_argument("--max-fps-drop", type=float, default=8.0, help="Allowed right-side FPS drop vs left-side")

    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/parity"))
    p.add_argument("--tag", type=str, default="")
    return p.parse_args()


def _load_pack(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Pack file not found: {path}")
    out: list[dict[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [x.strip() for x in line.split(",", 1)]
        source = parts[0]
        scene = parts[1].lower() if len(parts) > 1 and parts[1] else "unknown"
        out.append({"source": source, "scene": scene})
    if not out:
        raise ValueError(f"Pack file is empty: {path}")
    return out


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


def _build_cfg(
    *,
    preset: str,
    mode: str,
    device: str,
    imgsz: int,
    conf: float,
    small_target_flag: str,
) -> tuple[Config, bool]:
    cfg = Config()
    cfg, preset_data = load_preset(preset, cfg)
    if mode:
        cfg = apply_runtime_mode(cfg, mode)
    if device:
        cfg.DEVICE = device

    small_target = _resolve_small_target(small_target_flag, preset_data)
    resolved_imgsz = imgsz if imgsz > 0 else int(cfg.IMG_SIZE)
    resolved_conf = conf if conf > 0 else float(cfg.CONF_THRESH)
    cfg = apply_runtime_preset(cfg, small_target_mode=small_target, imgsz=resolved_imgsz, conf=resolved_conf)
    return cfg, small_target


def _mode_ratio(mode_counts: dict[str, Any], key: str, total_frames: int) -> float:
    total = max(1, int(total_frames))
    return float(mode_counts.get(key, 0)) / float(total)


def _row_score(lock_rate: float, continuity: float, presence: float, idchg_pm: float, swpm: float, false_lock_rate: float) -> float:
    return (
        45.0 * lock_rate
        + 18.0 * continuity
        + 14.0 * presence
        - 8.0 * idchg_pm
        - 7.0 * swpm
        - 22.0 * false_lock_rate
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = [
        "source",
        "scene",
        "lock_rate_left",
        "lock_rate_right",
        "lock_rate_delta",
        "continuity_left",
        "continuity_right",
        "continuity_delta",
        "presence_left",
        "presence_right",
        "presence_delta",
        "idchg_pm_left",
        "idchg_pm_right",
        "idchg_pm_delta",
        "swpm_left",
        "swpm_right",
        "swpm_delta",
        "false_lock_rate_left",
        "false_lock_rate_right",
        "false_lock_rate_delta",
        "track_ratio_left",
        "track_ratio_right",
        "track_ratio_delta",
        "lost_ratio_left",
        "lost_ratio_right",
        "lost_ratio_delta",
        "fps_left",
        "fps_right",
        "fps_drop",
        "score_left",
        "score_right",
        "score_delta",
        "passed",
        "fail_reasons",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in headers})


def main() -> int:
    args = parse_args()
    known_presets = set(available_presets())
    if args.left_preset not in known_presets:
        print(f"[error] Unknown left preset: {args.left_preset}")
        return 2
    if args.right_preset not in known_presets:
        print(f"[error] Unknown right preset: {args.right_preset}")
        return 2

    try:
        pack = _load_pack(args.pack_file)
    except Exception as exc:
        print(f"[error] {exc}")
        return 2

    left_cfg, left_small = _build_cfg(
        preset=args.left_preset,
        mode=args.left_mode,
        device=args.left_device,
        imgsz=args.left_imgsz,
        conf=args.left_conf,
        small_target_flag=args.left_small_target,
    )
    right_cfg, right_small = _build_cfg(
        preset=args.right_preset,
        mode=args.right_mode,
        device=args.right_device,
        imgsz=args.right_imgsz,
        conf=args.right_conf,
        small_target_flag=args.right_small_target,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    failures: list[str] = []

    for item in pack:
        source = parse_video_source(_resolve_source_path(item["source"]))
        scene = item["scene"]
        source_name = Path(str(source)).stem if isinstance(source, str) else f"camera_{source}"

        left_report = evaluate_source(
            left_cfg,
            source=source,
            small_target_mode=left_small,
            max_frames=max(0, int(args.max_frames)),
            report_path=str(args.out_dir / f"{args.tag}{source_name}_{args.left_label}.json"),
        ).to_dict()
        right_report = evaluate_source(
            right_cfg,
            source=source,
            small_target_mode=right_small,
            max_frames=max(0, int(args.max_frames)),
            report_path=str(args.out_dir / f"{args.tag}{source_name}_{args.right_label}.json"),
        ).to_dict()

        left_frames = max(1, int(left_report.get("total_frames", 0)))
        right_frames = max(1, int(right_report.get("total_frames", 0)))
        lock_rate_left = float(left_report.get("lock_frames", 0)) / left_frames
        lock_rate_right = float(right_report.get("lock_frames", 0)) / right_frames

        continuity_left = float(left_report.get("continuity_score", 0.0))
        continuity_right = float(right_report.get("continuity_score", 0.0))
        presence_left = float(left_report.get("active_presence_rate", 0.0))
        presence_right = float(right_report.get("active_presence_rate", 0.0))
        idchg_left = float(left_report.get("active_id_changes_per_min", 0.0))
        idchg_right = float(right_report.get("active_id_changes_per_min", 0.0))
        swpm_left = float(left_report.get("lock_switches_per_min", 0.0))
        swpm_right = float(right_report.get("lock_switches_per_min", 0.0))
        false_lock_left = float(left_report.get("false_lock_rate", 0.0))
        false_lock_right = float(right_report.get("false_lock_rate", 0.0))
        fps_left = float(left_report.get("avg_fps", 0.0))
        fps_right = float(right_report.get("avg_fps", 0.0))

        track_ratio_left = _mode_ratio(left_report.get("mode_counts", {}), "TRACK", left_frames)
        track_ratio_right = _mode_ratio(right_report.get("mode_counts", {}), "TRACK", right_frames)
        lost_ratio_left = _mode_ratio(left_report.get("mode_counts", {}), "LOST", left_frames)
        lost_ratio_right = _mode_ratio(right_report.get("mode_counts", {}), "LOST", right_frames)

        row = {
            "source": str(source),
            "scene": scene,
            "lock_rate_left": round(lock_rate_left, 4),
            "lock_rate_right": round(lock_rate_right, 4),
            "lock_rate_delta": round(abs(lock_rate_left - lock_rate_right), 4),
            "continuity_left": round(continuity_left, 4),
            "continuity_right": round(continuity_right, 4),
            "continuity_delta": round(abs(continuity_left - continuity_right), 4),
            "presence_left": round(presence_left, 4),
            "presence_right": round(presence_right, 4),
            "presence_delta": round(abs(presence_left - presence_right), 4),
            "idchg_pm_left": round(idchg_left, 4),
            "idchg_pm_right": round(idchg_right, 4),
            "idchg_pm_delta": round(abs(idchg_left - idchg_right), 4),
            "swpm_left": round(swpm_left, 4),
            "swpm_right": round(swpm_right, 4),
            "swpm_delta": round(abs(swpm_left - swpm_right), 4),
            "false_lock_rate_left": round(false_lock_left, 4),
            "false_lock_rate_right": round(false_lock_right, 4),
            "false_lock_rate_delta": round(abs(false_lock_left - false_lock_right), 4),
            "track_ratio_left": round(track_ratio_left, 4),
            "track_ratio_right": round(track_ratio_right, 4),
            "track_ratio_delta": round(abs(track_ratio_left - track_ratio_right), 4),
            "lost_ratio_left": round(lost_ratio_left, 4),
            "lost_ratio_right": round(lost_ratio_right, 4),
            "lost_ratio_delta": round(abs(lost_ratio_left - lost_ratio_right), 4),
            "fps_left": round(fps_left, 3),
            "fps_right": round(fps_right, 3),
            "fps_drop": round(max(0.0, fps_left - fps_right), 3),
        }

        row["score_left"] = round(_row_score(lock_rate_left, continuity_left, presence_left, idchg_left, swpm_left, false_lock_left), 3)
        row["score_right"] = round(_row_score(lock_rate_right, continuity_right, presence_right, idchg_right, swpm_right, false_lock_right), 3)
        row["score_delta"] = round(abs(float(row["score_left"]) - float(row["score_right"])), 3)

        row_failures: list[str] = []
        if float(row["lock_rate_delta"]) > float(args.max_lock_rate_delta):
            row_failures.append(f"lock_rate_delta>{args.max_lock_rate_delta}")
        if float(row["continuity_delta"]) > float(args.max_continuity_delta):
            row_failures.append(f"continuity_delta>{args.max_continuity_delta}")
        if float(row["presence_delta"]) > float(args.max_presence_delta):
            row_failures.append(f"presence_delta>{args.max_presence_delta}")
        if float(row["idchg_pm_delta"]) > float(args.max_idchg_pm_delta):
            row_failures.append(f"idchg_delta>{args.max_idchg_pm_delta}")
        if float(row["swpm_delta"]) > float(args.max_swpm_delta):
            row_failures.append(f"swpm_delta>{args.max_swpm_delta}")
        if float(row["false_lock_rate_delta"]) > float(args.max_false_lock_rate_delta):
            row_failures.append(f"false_lock_delta>{args.max_false_lock_rate_delta}")
        if float(row["track_ratio_delta"]) > float(args.max_track_ratio_delta):
            row_failures.append(f"track_ratio_delta>{args.max_track_ratio_delta}")
        if float(row["lost_ratio_delta"]) > float(args.max_lost_ratio_delta):
            row_failures.append(f"lost_ratio_delta>{args.max_lost_ratio_delta}")
        if float(row["fps_drop"]) > float(args.max_fps_drop):
            row_failures.append(f"fps_drop>{args.max_fps_drop}")

        row["passed"] = len(row_failures) == 0
        row["fail_reasons"] = ";".join(row_failures)
        if row_failures:
            failures.append(f"{row['source']}: {row['fail_reasons']}")

        rows.append(row)
        print(
            f"[parity] {source_name} pass={row['passed']} "
            f"lockΔ={row['lock_rate_delta']:.3f} contΔ={row['continuity_delta']:.3f} "
            f"idΔ={row['idchg_pm_delta']:.2f} swΔ={row['swpm_delta']:.2f} fps_drop={row['fps_drop']:.1f}"
        )

    mean = {
        "lock_rate_delta": round(sum(float(r["lock_rate_delta"]) for r in rows) / max(1, len(rows)), 4),
        "continuity_delta": round(sum(float(r["continuity_delta"]) for r in rows) / max(1, len(rows)), 4),
        "presence_delta": round(sum(float(r["presence_delta"]) for r in rows) / max(1, len(rows)), 4),
        "idchg_pm_delta": round(sum(float(r["idchg_pm_delta"]) for r in rows) / max(1, len(rows)), 4),
        "swpm_delta": round(sum(float(r["swpm_delta"]) for r in rows) / max(1, len(rows)), 4),
        "false_lock_rate_delta": round(sum(float(r["false_lock_rate_delta"]) for r in rows) / max(1, len(rows)), 4),
        "track_ratio_delta": round(sum(float(r["track_ratio_delta"]) for r in rows) / max(1, len(rows)), 4),
        "lost_ratio_delta": round(sum(float(r["lost_ratio_delta"]) for r in rows) / max(1, len(rows)), 4),
        "fps_drop": round(sum(float(r["fps_drop"]) for r in rows) / max(1, len(rows)), 4),
        "score_delta": round(sum(float(r["score_delta"]) for r in rows) / max(1, len(rows)), 3),
    }

    passed = len(failures) == 0
    summary = {
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "pack_file": str(args.pack_file),
        "left": {
            "label": args.left_label,
            "preset": args.left_preset,
            "mode": left_cfg.RUNTIME_MODE,
            "device": left_cfg.DEVICE,
            "imgsz": left_cfg.IMG_SIZE,
            "conf": left_cfg.CONF_THRESH,
            "small_target_mode": left_small,
        },
        "right": {
            "label": args.right_label,
            "preset": args.right_preset,
            "mode": right_cfg.RUNTIME_MODE,
            "device": right_cfg.DEVICE,
            "imgsz": right_cfg.IMG_SIZE,
            "conf": right_cfg.CONF_THRESH,
            "small_target_mode": right_small,
        },
        "thresholds": {
            "max_lock_rate_delta": args.max_lock_rate_delta,
            "max_continuity_delta": args.max_continuity_delta,
            "max_presence_delta": args.max_presence_delta,
            "max_idchg_pm_delta": args.max_idchg_pm_delta,
            "max_swpm_delta": args.max_swpm_delta,
            "max_false_lock_rate_delta": args.max_false_lock_rate_delta,
            "max_track_ratio_delta": args.max_track_ratio_delta,
            "max_lost_ratio_delta": args.max_lost_ratio_delta,
            "max_fps_drop": args.max_fps_drop,
        },
        "parity_passed": passed,
        "rows": rows,
        "mean": mean,
        "failures": failures,
    }

    stem = f"{args.tag}parity_{args.left_label}_vs_{args.right_label}"
    out_json = args.out_dir / f"{stem}.json"
    out_csv = args.out_dir / f"{stem}.csv"
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_csv(out_csv, rows)

    print(f"[summary] pass={passed} json={out_json}")
    print(f"[summary] csv={out_csv}")
    if failures:
        for item in failures:
            print(f"[fail] {item}")

    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
