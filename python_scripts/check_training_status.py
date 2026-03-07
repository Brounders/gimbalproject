#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
BATCH_RE = re.compile(r"\b(\d+)/(\d+)\s+\d+\.\d+G.*?(\d+)/(\d+)\b")
START_RE = re.compile(r"\[INFO\] start: ([0-9T:+-]+)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Show current YOLO training status from latest autosession log.")
    p.add_argument(
        "--logs-dir",
        type=Path,
        default=Path("/Users/bround/Documents/Projects/GimbalProject/runs/autosession_logs"),
    )
    p.add_argument("--hours", type=float, default=6.0, help="Configured training time budget in hours.")
    return p.parse_args()


def latest_log(logs_dir: Path) -> Path | None:
    logs = sorted(logs_dir.glob("*_fast_trainonly.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return logs[0] if logs else None


def process_active() -> bool:
    cp = subprocess.run(
        ["pgrep", "-f", "train_yolo_from_yaml.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return bool(cp.stdout.strip())


def main() -> int:
    args = parse_args()
    log = latest_log(args.logs_dir)
    if not log:
        print("[status] log_not_found")
        return 1

    raw = log.read_text(errors="ignore")
    text = ANSI_RE.sub("", raw)

    active = process_active()
    print(f"[status] active={str(active).lower()}")
    print(f"[status] log={log}")

    start_match = START_RE.search(text)
    if start_match:
        start = datetime.fromisoformat(start_match.group(1))
        now = datetime.now(start.tzinfo)
        elapsed = (now - start).total_seconds()
        budget_sec = max(1.0, float(args.hours) * 3600.0)
        pct = max(0.0, min(100.0, elapsed / budget_sec * 100.0))
        print(f"[status] time_elapsed_min={elapsed / 60.0:.1f}")
        print(f"[status] time_progress_pct={pct:.2f}")

    matches = BATCH_RE.findall(text)
    if matches:
        epoch, epoch_total, batch, batch_total = map(int, matches[-1])
        print(f"[status] epoch={epoch}/{epoch_total} ({epoch / epoch_total * 100.0:.2f}%)")
        print(f"[status] batch={batch}/{batch_total} ({batch / batch_total * 100.0:.2f}% of current epoch)")
    else:
        print("[status] batch_progress=not_available_yet")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
