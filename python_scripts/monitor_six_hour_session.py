#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Monitor six-hour training session progress.")
    p.add_argument("--hours", type=float, default=6.0, help="Session budget in hours.")
    p.add_argument("--run-name", type=str, default="drone_bird_night_6h")
    p.add_argument("--logs-dir", type=Path, default=Path("runs/autosession_logs"))
    p.add_argument("--results-csv", type=Path, default=None, help="Override results.csv path")
    return p.parse_args()


def _latest_log(logs_dir: Path) -> Path | None:
    logs = sorted(logs_dir.glob("*_session.log"), reverse=True)
    return logs[0] if logs else None


def _parse_start_time(log_path: Path) -> datetime | None:
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("[INFO] start: "):
            ts = line.split(": ", 1)[1].strip()
            try:
                return datetime.fromisoformat(ts)
            except ValueError:
                return None
    return None


def _read_last_metrics(results_csv: Path) -> dict | None:
    if not results_csv.exists():
        return None
    rows = []
    with results_csv.open("r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    if not rows:
        return None
    return rows[-1]


def _to_float(v: str | None) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None


def main() -> int:
    args = parse_args()
    log_path = _latest_log(args.logs_dir)
    if log_path is None:
        print("[monitor] session log not found.")
        return 2

    started = _parse_start_time(log_path)
    now = datetime.now(timezone.utc).astimezone()
    if started is None:
        print(f"[monitor] start timestamp not found in {log_path}")
        return 3

    elapsed_h = max(0.0, (now - started).total_seconds() / 3600.0)
    budget_h = max(0.01, float(args.hours))
    progress = min(100.0, (elapsed_h / budget_h) * 100.0)
    eta_h = max(0.0, budget_h - elapsed_h)

    results_csv = args.results_csv
    if results_csv is None:
        results_csv = Path("runs/detect/runs") / args.run_name / "results.csv"
    last = _read_last_metrics(results_csv)

    print(f"[monitor] log: {log_path}")
    print(f"[monitor] started: {started.isoformat()}")
    print(f"[monitor] elapsed: {elapsed_h:.2f}h / {budget_h:.2f}h ({progress:.1f}%)")
    print(f"[monitor] ETA by time budget: {eta_h:.2f}h")

    if last is None:
        print(f"[monitor] results.csv not ready: {results_csv}")
        return 0

    epoch = _to_float(last.get("epoch"))
    map50 = _to_float(last.get("metrics/mAP50(B)"))
    map5095 = _to_float(last.get("metrics/mAP50-95(B)"))
    precision = _to_float(last.get("metrics/precision(B)"))
    recall = _to_float(last.get("metrics/recall(B)"))
    train_loss = _to_float(last.get("train/box_loss"))
    val_loss = _to_float(last.get("val/box_loss"))

    print(f"[monitor] results: {results_csv}")
    if epoch is not None:
        print(f"[monitor] last_epoch: {int(epoch)}")
    print(
        "[monitor] metrics: "
        f"mAP50={map50 if map50 is not None else 'n/a'} "
        f"mAP50-95={map5095 if map5095 is not None else 'n/a'} "
        f"P={precision if precision is not None else 'n/a'} "
        f"R={recall if recall is not None else 'n/a'}"
    )
    print(
        "[monitor] losses: "
        f"train_box={train_loss if train_loss is not None else 'n/a'} "
        f"val_box={val_loss if val_loss is not None else 'n/a'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
