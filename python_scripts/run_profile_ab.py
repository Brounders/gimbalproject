#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
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


DEFAULT_SOURCES = [
    "test_videos/night_ground_large_drones.mp4",
    "test_videos/night_ground_indicator_lights.mp4",
    "test_videos/Demo_IR_DRONE_146.mp4",
    "test_videos/IR_DRONE_001.mp4",
    "test_videos/IR_BIRD_001.mp4",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="A/B test: operator standard vs fast profile on night/IR clips.")
    p.add_argument("--base-preset", type=str, default="night_ir_lock_v2")
    p.add_argument("--profiles", type=str, default="operator_standard,fast")
    p.add_argument("--mode", type=str, default="operator")
    p.add_argument("--device", type=str, default="")
    p.add_argument("--imgsz", type=int, default=0)
    p.add_argument("--conf", type=float, default=0.0)
    p.add_argument("--max-frames", type=int, default=320)
    p.add_argument("--sources", type=str, default="")
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/ab"))
    p.add_argument("--tag", type=str, default="")
    return p.parse_args()


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


def _collect_sources(raw: str) -> list[str]:
    if raw.strip():
        return [x.strip() for x in raw.split(",") if x.strip()]
    return list(DEFAULT_SOURCES)


def _score(row: dict) -> float:
    return (
        40.0 * float(row.get("lock_rate", 0.0))
        + 15.0 * float(row.get("continuity_score", 0.0))
        + 12.0 * float(row.get("active_presence_rate", 0.0))
        + 20.0 * min(float(row.get("avg_fps", 0.0)) / 30.0, 1.0)
        - 6.0 * float(row.get("lock_switches_per_min", 0.0))
        - 8.0 * float(row.get("active_id_changes_per_min", 0.0))
        - 18.0 * float(row.get("effective_false_lock_rate", 0.0))
    )


def _write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})


def main() -> int:
    args = parse_args()
    presets = set(available_presets())
    if args.base_preset not in presets:
        print(f"[error] Unknown base preset: {args.base_preset}")
        return 2

    profile_names = [x.strip() for x in args.profiles.split(",") if x.strip()]
    for name in profile_names:
        if name not in presets:
            print(f"[error] Unknown profile preset: {name}")
            return 2

    sources = _collect_sources(args.sources)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    base_cfg, base_data = load_preset(args.base_preset, Config())
    base_cfg = apply_runtime_mode(base_cfg, args.mode)
    if args.device:
        base_cfg.DEVICE = args.device
    small_target = bool(base_data.get("small_target_mode", False))
    imgsz = args.imgsz if args.imgsz > 0 else int(base_cfg.IMG_SIZE)
    conf = args.conf if args.conf > 0 else float(base_cfg.CONF_THRESH)

    detail_rows: list[dict] = []

    for profile in profile_names:
        cfg = Config(**base_cfg.__dict__)
        cfg, _ = load_preset(profile, cfg)
        cfg = apply_runtime_preset(cfg, small_target_mode=small_target, imgsz=imgsz, conf=conf)

        for raw_source in sources:
            source = parse_video_source(_resolve_source_path(raw_source))
            report = evaluate_source(
                cfg,
                source=source,
                small_target_mode=small_target,
                max_frames=max(0, int(args.max_frames)),
                report_path="",
            ).to_dict()
            frames = max(1, int(report.get("total_frames", 0)))
            gt_frames = int(report.get("gt_frames", 0))
            false_lock_rate = float(report.get("false_lock_rate", 0.0))
            unverified_active_rate = float(report.get("unverified_active_rate", 0.0))
            effective_false_lock_rate = false_lock_rate if gt_frames > 0 else 0.5 * unverified_active_rate
            row = {
                "profile": profile,
                "source": str(source),
                "frames": int(report.get("total_frames", 0)),
                "avg_fps": round(float(report.get("avg_fps", 0.0)), 3),
                "lock_rate": round(float(report.get("lock_frames", 0)) / frames, 4),
                "continuity_score": round(float(report.get("continuity_score", 0.0)), 4),
                "active_presence_rate": round(float(report.get("active_presence_rate", 0.0)), 4),
                "active_id_changes_per_min": round(float(report.get("active_id_changes_per_min", 0.0)), 4),
                "lock_switches_per_min": round(float(report.get("lock_switches_per_min", 0.0)), 4),
                "false_lock_rate": round(false_lock_rate, 4),
                "unverified_active_rate": round(unverified_active_rate, 4),
                "effective_false_lock_rate": round(effective_false_lock_rate, 4),
            }
            row["score"] = round(_score(row), 3)
            detail_rows.append(row)
            print(
                f"[ab] {profile} | {Path(str(source)).name}: "
                f"score={row['score']:.2f} lock={row['lock_rate']:.3f} "
                f"fps={row['avg_fps']:.1f} false={row['effective_false_lock_rate']:.3f}"
            )

    summary_rows: list[dict] = []
    for profile in profile_names:
        subset = [r for r in detail_rows if r["profile"] == profile]
        if not subset:
            continue
        summary_rows.append(
            {
                "profile": profile,
                "clips": len(subset),
                "mean_score": round(sum(float(r["score"]) for r in subset) / len(subset), 4),
                "mean_lock_rate": round(sum(float(r["lock_rate"]) for r in subset) / len(subset), 4),
                "mean_avg_fps": round(sum(float(r["avg_fps"]) for r in subset) / len(subset), 4),
                "mean_continuity": round(sum(float(r["continuity_score"]) for r in subset) / len(subset), 4),
                "mean_presence": round(sum(float(r["active_presence_rate"]) for r in subset) / len(subset), 4),
                "mean_idchg_per_min": round(sum(float(r["active_id_changes_per_min"]) for r in subset) / len(subset), 4),
                "mean_swpm": round(sum(float(r["lock_switches_per_min"]) for r in subset) / len(subset), 4),
                "mean_effective_false": round(sum(float(r["effective_false_lock_rate"]) for r in subset) / len(subset), 4),
            }
        )

    if not summary_rows:
        print("[error] No A/B data produced")
        return 3

    winner = max(summary_rows, key=lambda x: float(x["mean_score"]))["profile"]
    for row in summary_rows:
        row["winner"] = row["profile"] == winner

    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    stem = f"{args.tag}profile_ab_{args.base_preset}_{stamp}"
    detail_csv = args.out_dir / f"{stem}_detail.csv"
    summary_csv = args.out_dir / f"{stem}_summary.csv"
    summary_json = args.out_dir / f"{stem}.json"

    _write_csv(
        detail_csv,
        detail_rows,
        [
            "profile",
            "source",
            "frames",
            "avg_fps",
            "lock_rate",
            "continuity_score",
            "active_presence_rate",
            "active_id_changes_per_min",
            "lock_switches_per_min",
            "false_lock_rate",
            "unverified_active_rate",
            "effective_false_lock_rate",
            "score",
        ],
    )
    _write_csv(
        summary_csv,
        summary_rows,
        [
            "profile",
            "clips",
            "mean_score",
            "mean_lock_rate",
            "mean_avg_fps",
            "mean_continuity",
            "mean_presence",
            "mean_idchg_per_min",
            "mean_swpm",
            "mean_effective_false",
            "winner",
        ],
    )

    payload = {
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "base_preset": args.base_preset,
        "profiles": profile_names,
        "sources": [str(parse_video_source(_resolve_source_path(s))) for s in sources],
        "winner": winner,
        "summary": summary_rows,
        "detail_csv": str(detail_csv),
        "summary_csv": str(summary_csv),
    }
    summary_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[summary] winner={winner}")
    print(f"[summary] detail_csv={detail_csv}")
    print(f"[summary] summary_csv={summary_csv}")
    print(f"[summary] json={summary_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
