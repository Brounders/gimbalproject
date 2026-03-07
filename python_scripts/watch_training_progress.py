#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import subprocess
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live training monitor")
    parser.add_argument(
        "--run-dir",
        default="runs/detect/runs/drone_bird_v2",
        help="Ultralytics run directory",
    )
    parser.add_argument(
        "--process-pattern",
        default="train_drone_bird.py --dataset-root datasets/drone_bird_raw --workdir datasets/drone_bird_yolo --model",
        help="Substring to detect training process via pgrep -af",
    )
    parser.add_argument("--interval", type=float, default=5.0, help="Refresh interval in seconds")
    return parser.parse_args()


def read_total_epochs(args_yaml: Path) -> int:
    if not args_yaml.exists():
        return 0
    for line in args_yaml.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("epochs:"):
            try:
                return int(float(line.split(":", 1)[1].strip()))
            except ValueError:
                return 0
    return 0


def read_last_metrics(results_csv: Path) -> dict[str, str]:
    if not results_csv.exists() or results_csv.stat().st_size == 0:
        return {}
    with results_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else {}


def find_processes(pattern: str) -> list[str]:
    result = subprocess.run(["pgrep", "-af", pattern], capture_output=True, text=True)
    if result.returncode not in (0, 1):
        return []
    lines = []
    for line in result.stdout.splitlines():
        if "watch_training_progress.py" in line:
            continue
        lines.append(line)
    return lines


def file_mtime(path: Path) -> str:
    if not path.exists():
        return "missing"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(path.stat().st_mtime))


def clear() -> None:
    print("\033[2J\033[H", end="")


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)
    args_yaml = run_dir / "args.yaml"
    results_csv = run_dir / "results.csv"
    best_pt = run_dir / "weights" / "best.pt"
    last_pt = run_dir / "weights" / "last.pt"

    while True:
        total_epochs = read_total_epochs(args_yaml)
        last = read_last_metrics(results_csv)
        procs = find_processes(args.process_pattern)

        epoch_done = 0
        if last:
            try:
                epoch_done = int(float(last.get("epoch", "0")))
            except ValueError:
                epoch_done = 0

        percent = (epoch_done / total_epochs * 100.0) if total_epochs else 0.0

        clear()
        print("Drone Training Monitor")
        print(f"Run dir:        {run_dir}")
        print(f"Status:         {'RUNNING' if procs else 'STOPPED'}")
        print(f"Epochs:         {epoch_done}/{total_epochs} ({percent:.1f}%)")
        print(f"results.csv:    {file_mtime(results_csv)}")
        print(f"best.pt:        {file_mtime(best_pt)}")
        print(f"last.pt:        {file_mtime(last_pt)}")
        print()

        if last:
            print("Latest metrics")
            for key in [
                "train/box_loss",
                "train/cls_loss",
                "train/dfl_loss",
                "metrics/precision(B)",
                "metrics/recall(B)",
                "metrics/mAP50(B)",
                "metrics/mAP50-95(B)",
                "val/box_loss",
                "val/cls_loss",
                "val/dfl_loss",
            ]:
                if key in last:
                    print(f"  {key:22} {last[key]}")
            print()

        print("Processes")
        if procs:
            for line in procs:
                print(f"  {line}")
        else:
            print("  no matching training process found")
        print()
        print("Ctrl+C to exit monitor")
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
