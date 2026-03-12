#!/usr/bin/env python3
"""Compare two run_quick_kpi_smoke.py JSON snapshots and print a delta table."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

METRICS = [
    "false_lock_rate",
    "active_id_changes_per_min",
    "lock_switches_per_min",
    "continuity_score",
    "avg_fps",
]
LOWER_IS_BETTER = {"false_lock_rate", "active_id_changes_per_min", "lock_switches_per_min"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Compare two run_quick_kpi_smoke.py JSON snapshots and print a delta table."
    )
    p.add_argument("before", type=Path, help="Snapshot JSON taken before changes.")
    p.add_argument("after", type=Path, help="Snapshot JSON taken after changes.")
    p.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="Absolute delta threshold for marking significant change (default: 0.05).",
    )
    return p.parse_args()


def _load_rows(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(row["source"]): row for row in data.get("rows", [])}


def main() -> int:
    args = parse_args()
    if not args.before.exists():
        print(f"[error] before file not found: {args.before}", file=sys.stderr)
        return 2
    if not args.after.exists():
        print(f"[error] after file not found: {args.after}", file=sys.stderr)
        return 2

    before_rows = _load_rows(args.before)
    after_rows = _load_rows(args.after)
    sources = sorted(set(before_rows) & set(after_rows))
    if not sources:
        print("[error] No matching sources found in both snapshots.", file=sys.stderr)
        return 2

    col_src = 42
    col_metric = 35
    header = f"{'Source':<{col_src}}  {'Metric':<{col_metric}}  {'Before':>8}  {'After':>8}  {'Delta':>8}  OK?"
    sep = "-" * len(header)
    print(header)
    print(sep)

    for src in sources:
        br = before_rows[src]
        ar = after_rows[src]
        first = True
        for m in METRICS:
            b = float(br.get(m, 0.0))
            a = float(ar.get(m, 0.0))
            delta = a - b
            better = (m in LOWER_IS_BETTER and delta < 0) or (
                m not in LOWER_IS_BETTER and delta > 0
            )
            significant = abs(delta) >= args.threshold
            marker = "✓" if (significant and better) else ("✗" if (significant and not better) else " ")
            src_label = (src[-col_src:] if len(src) > col_src else src) if first else ""
            print(
                f"{src_label:<{col_src}}  {m:<{col_metric}}  {b:>8.4f}  {a:>8.4f}  {delta:>+8.4f}  {marker}"
            )
            first = False
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
