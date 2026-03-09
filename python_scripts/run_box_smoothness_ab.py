#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_tracker.config import Config
from uav_tracker.modes import apply_runtime_mode
from uav_tracker.pipeline import TrackerPipeline, VideoSession, apply_runtime_preset, parse_video_source
from uav_tracker.profile_io import available_presets, load_preset


DEFAULT_SOURCES = [
    "test_videos/night_ground_large_drones.mp4",
    "test_videos/Demo_IR_DRONE_146.mp4",
    "test_videos/IR_DRONE_001.mp4",
    "test_videos/night_ground_indicator_lights.mp4",
    "test_videos/IR_BIRD_001.mp4",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="A/B test for tracking box smoothness (DISPLAY_BOX_ALPHA).")
    p.add_argument("--preset", type=str, default="night_ir_lock_v2", help="Preset from configs/")
    p.add_argument("--mode", type=str, default="operator", help="Runtime mode override")
    p.add_argument("--device", type=str, default="", help="Optional device override")
    p.add_argument("--imgsz", type=int, default=0, help="Optional imgsz override")
    p.add_argument("--conf", type=float, default=0.0, help="Optional conf override")
    p.add_argument("--small-target", type=str, default="auto", choices=["auto", "on", "off"])
    p.add_argument("--sources", type=str, default="", help="Comma separated sources")
    p.add_argument("--alphas", type=str, default="0.2,0.4,0.6", help="Comma separated alphas")
    p.add_argument("--max-frames", type=int, default=600)
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/smoothness_ab"))
    p.add_argument("--tag", type=str, default="")
    return p.parse_args()


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


def _parse_sources(raw: str) -> list[str]:
    if raw.strip():
        return [x.strip() for x in raw.split(",") if x.strip()]
    return list(DEFAULT_SOURCES)


def _parse_alphas(raw: str) -> list[float]:
    values: list[float] = []
    for token in [x.strip() for x in raw.split(",") if x.strip()]:
        try:
            v = float(token)
        except ValueError:
            continue
        values.append(max(0.0, min(1.0, v)))
    if not values:
        values = [0.2, 0.4, 0.6]
    return values


def _run_single(cfg: Config, source: str | int, max_frames: int) -> dict:
    session = VideoSession(cfg, source, manage_cv_windows=False)
    session.open()
    pipeline = TrackerPipeline(cfg)

    frames = 0
    fps_values: list[float] = []
    lock_segments: list[int] = []
    current_lock = 0
    last_output = None

    try:
        while True:
            ret, frame, meta = session.read()
            if not ret:
                break
            output = pipeline.process_frame(
                frame,
                frame_index=int(meta.get("frame_index", frames)),
                gt_bbox=meta.get("gt_bbox"),
                small_target_mode=True,
                render=False,
                source_fps=meta.get("source_fps"),
            )
            last_output = output
            frames += 1
            fps_values.append(float(output.fps))

            if str(output.mode).upper() == "TRACK":
                current_lock += 1
            elif current_lock > 0:
                lock_segments.append(current_lock)
                current_lock = 0

            if max_frames > 0 and frames >= max_frames:
                break
    finally:
        session.close()

    if current_lock > 0:
        lock_segments.append(current_lock)

    if last_output is None:
        return {
            "frames": 0,
            "avg_fps": 0.0,
            "target_switches": 0,
            "target_switches_per_min": 0.0,
            "lock_switches": 0,
            "lock_switches_per_min": 0.0,
            "lock_frames": 0,
            "lock_segments": 0,
            "avg_lock_duration_frames": 0.0,
            "max_lock_duration_frames": 0,
            "active_presence_rate": 0.0,
            "continuity_score": 0.0,
        }

    avg_lock_duration = mean(lock_segments) if lock_segments else 0.0
    max_lock_duration = max(lock_segments) if lock_segments else 0
    lock_frames = sum(lock_segments)

    return {
        "frames": frames,
        "avg_fps": mean(fps_values) if fps_values else 0.0,
        "target_switches": int(last_output.active_id_changes),
        "target_switches_per_min": float(last_output.active_id_changes) * 60.0 / max(5.0, float(pipeline._video_elapsed_sec)),
        "lock_switches": int(last_output.lock_switch_count),
        "lock_switches_per_min": float(last_output.lock_switches_per_min),
        "lock_frames": lock_frames,
        "lock_segments": len(lock_segments),
        "avg_lock_duration_frames": float(avg_lock_duration),
        "max_lock_duration_frames": int(max_lock_duration),
        "active_presence_rate": float(last_output.active_presence_rate),
        "continuity_score": float(last_output.continuity_score),
    }


def _score(row: dict) -> float:
    return (
        0.25 * float(row["avg_fps"])
        + 12.0 * float(row["active_presence_rate"])
        + 10.0 * float(row["continuity_score"])
        + 0.08 * float(row["avg_lock_duration_frames"])
        - 7.0 * float(row["target_switches_per_min"])
        - 8.0 * float(row["lock_switches_per_min"])
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    headers = [
        "alpha",
        "source",
        "frames",
        "avg_fps",
        "target_switches",
        "target_switches_per_min",
        "lock_switches",
        "lock_switches_per_min",
        "lock_frames",
        "lock_segments",
        "avg_lock_duration_frames",
        "max_lock_duration_frames",
        "active_presence_rate",
        "continuity_score",
        "score",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in headers})


def main() -> int:
    args = parse_args()
    if args.preset not in set(available_presets()):
        print(f"[error] Unknown preset: {args.preset}")
        return 2

    cfg_base, preset_data = load_preset(args.preset, Config())
    cfg_base = apply_runtime_mode(cfg_base, args.mode)
    if args.device:
        cfg_base.DEVICE = args.device
    small_target = _resolve_small_target(args.small_target, preset_data)
    imgsz = args.imgsz if args.imgsz > 0 else int(cfg_base.IMG_SIZE)
    conf = args.conf if args.conf > 0 else float(cfg_base.CONF_THRESH)
    cfg_base = apply_runtime_preset(cfg_base, small_target_mode=small_target, imgsz=imgsz, conf=conf)

    sources = _parse_sources(args.sources)
    alphas = _parse_alphas(args.alphas)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    for alpha in alphas:
        for raw_source in sources:
            source = parse_video_source(_resolve_source_path(raw_source))
            cfg = Config(**cfg_base.__dict__)
            cfg.DISPLAY_BOX_ALPHA = float(alpha)
            result = _run_single(cfg, source, max_frames=max(0, int(args.max_frames)))
            row = {
                "alpha": round(float(alpha), 3),
                "source": str(source),
                **result,
            }
            row["score"] = round(_score(row), 4)
            rows.append(row)
            print(
                f"[ab] alpha={alpha:.2f} {Path(str(source)).name}: "
                f"idchg/min={row['target_switches_per_min']:.2f} "
                f"avg_lock={row['avg_lock_duration_frames']:.1f}f "
                f"fps={row['avg_fps']:.1f} score={row['score']:.2f}"
            )

    alpha_summary: dict[str, dict] = {}
    for alpha in sorted(set(float(r["alpha"]) for r in rows)):
        subset = [r for r in rows if float(r["alpha"]) == alpha]
        alpha_summary[f"{alpha:.2f}"] = {
            "mean_score": round(mean(float(r["score"]) for r in subset), 4),
            "mean_target_switches_per_min": round(mean(float(r["target_switches_per_min"]) for r in subset), 4),
            "mean_lock_switches_per_min": round(mean(float(r["lock_switches_per_min"]) for r in subset), 4),
            "mean_avg_lock_duration_frames": round(mean(float(r["avg_lock_duration_frames"]) for r in subset), 4),
            "mean_fps": round(mean(float(r["avg_fps"]) for r in subset), 4),
        }

    best_alpha = max(alpha_summary.items(), key=lambda x: x[1]["mean_score"])[0] if alpha_summary else "n/a"
    payload = {
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "preset": args.preset,
        "mode": args.mode,
        "device": cfg_base.DEVICE,
        "small_target_mode": small_target,
        "imgsz": cfg_base.IMG_SIZE,
        "conf": cfg_base.CONF_THRESH,
        "sources": [str(parse_video_source(_resolve_source_path(s))) for s in sources],
        "alphas": [round(a, 3) for a in alphas],
        "rows": rows,
        "alpha_summary": alpha_summary,
        "recommended_alpha": best_alpha,
    }

    stem = f"{args.tag}smoothness_ab_{args.preset}"
    out_json = args.out_dir / f"{stem}.json"
    out_csv = args.out_dir / f"{stem}.csv"
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_csv(out_csv, rows)

    print(f"[summary] json={out_json}")
    print(f"[summary] csv={out_csv}")
    print(f"[summary] recommended_alpha={best_alpha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
