#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWEEP_SCRIPT = ROOT / "python_scripts" / "run_scenario_sweep.py"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch scenario sweep over dataset videos.")
    p.add_argument("--dataset-root", type=Path, required=True, help="Path to dataset root.")
    p.add_argument(
        "--video-pattern",
        type=str,
        default="infrared.mp4",
        help="Glob filename pattern under dataset-root (default: infrared.mp4).",
    )
    p.add_argument("--presets", type=str, default="default,night,antiuav_thermal")
    p.add_argument("--max-frames", type=int, default=240)
    p.add_argument("--limit", type=int, default=60, help="Max number of videos to process (0 = all).")
    p.add_argument("--start-index", type=int, default=0)
    p.add_argument(
        "--report-dir",
        type=Path,
        default=Path("runs/evaluations/dataset_batch"),
        help="Output report folder.",
    )
    p.add_argument("--tag-prefix", type=str, default="rgbt_ir_")
    p.add_argument("--mode", type=str, default="")
    p.add_argument("--device", type=str, default="")
    p.add_argument("--imgsz", type=int, default=0)
    p.add_argument("--conf", type=float, default=0.0)
    p.add_argument("--small-target", type=str, default="auto", choices=["auto", "on", "off"])
    p.add_argument("--sort", type=str, default="score", choices=["score", "lock_rate", "fps", "swpm"])
    p.add_argument("--resume", action="store_true", help="Skip runs if summary file already exists.")
    p.add_argument(
        "--python-bin",
        type=str,
        default=sys.executable,
        help="Python executable to run sweep script.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not SWEEP_SCRIPT.exists():
        print(f"[error] Missing script: {SWEEP_SCRIPT}")
        return 2
    if not args.dataset_root.exists():
        print(f"[error] Dataset root not found: {args.dataset_root}")
        return 2

    videos = sorted(args.dataset_root.rglob(args.video_pattern))
    if not videos:
        print(f"[error] No videos found by pattern '{args.video_pattern}' in {args.dataset_root}")
        return 3

    start = max(0, int(args.start_index))
    videos = videos[start:]
    if args.limit > 0:
        videos = videos[: args.limit]
    total = len(videos)
    if total == 0:
        print("[error] Empty selection after start-index/limit.")
        return 3

    args.report_dir.mkdir(parents=True, exist_ok=True)
    print(f"[info] Dataset: {args.dataset_root}")
    print(f"[info] Videos selected: {total}")
    print(f"[info] Pattern: {args.video_pattern}")
    print(f"[info] Presets: {args.presets}")
    print(f"[info] max_frames={args.max_frames} report_dir={args.report_dir}")
    print(f"[info] python={args.python_bin}")

    started_at = time.time()
    completed = 0
    failed = 0

    for idx, video in enumerate(videos, start=1):
        rel = video.relative_to(args.dataset_root)
        source_stem = video.stem
        tag = f"{args.tag_prefix}{idx:04d}_"
        summary_json = args.report_dir / f"{tag}summary_{source_stem}.json"
        if args.resume and summary_json.exists():
            completed += 1
            progress = completed / total * 100.0
            print(f"[{completed}/{total} {progress:5.1f}%] skip (resume): {rel}")
            continue

        cmd = [
            args.python_bin,
            str(SWEEP_SCRIPT),
            "--source",
            str(video),
            "--presets",
            args.presets,
            "--max-frames",
            str(max(0, int(args.max_frames))),
            "--report-dir",
            str(args.report_dir),
            "--tag",
            tag,
            "--small-target",
            args.small_target,
            "--sort",
            args.sort,
        ]
        if args.mode:
            cmd.extend(["--mode", args.mode])
        if args.device:
            cmd.extend(["--device", args.device])
        if args.imgsz > 0:
            cmd.extend(["--imgsz", str(args.imgsz)])
        if args.conf > 0:
            cmd.extend(["--conf", str(args.conf)])

        before = time.time()
        progress_start = (idx - 1) / total * 100.0
        print(f"[{idx}/{total} {progress_start:5.1f}%] run: {rel}")
        result = subprocess.run(cmd, cwd=ROOT, text=True)
        took = time.time() - before
        if result.returncode == 0:
            completed += 1
            progress = completed / total * 100.0
            elapsed = time.time() - started_at
            avg_per_video = elapsed / max(completed + failed, 1)
            eta_seconds = max(0.0, avg_per_video * (total - (completed + failed)))
            eta_min = eta_seconds / 60.0
            print(
                f"[{completed + failed}/{total} {progress:5.1f}%] done in {took:.1f}s | "
                f"ETA {eta_min:.1f} min"
            )
        else:
            failed += 1
            processed = completed + failed
            progress = processed / total * 100.0
            print(f"[{processed}/{total} {progress:5.1f}%] fail rc={result.returncode} | {rel}")

    elapsed = time.time() - started_at
    print(
        f"[summary] total={total} completed={completed} failed={failed} "
        f"elapsed={elapsed/60.0:.1f} min report_dir={args.report_dir}"
    )
    return 0 if failed == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
