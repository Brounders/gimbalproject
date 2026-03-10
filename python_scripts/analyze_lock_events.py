#!/usr/bin/env python3
"""Analyze lock-event JSONL logs and produce a numerical summary.

Each line in a lock-event log is a JSON object written by run_tracker():
  {"frame_index": int, "event": str, "active_id": int|null, "mode": str,
   "lock_score": float, "lock_switches_per_min": float,
   "budget_level": int, "budget_load": float}

Event types: acquired, lost, reacquired, switch

Usage examples:
    ./tracker_env/bin/python python_scripts/analyze_lock_events.py \\
        runs/lock_events.jsonl

    ./tracker_env/bin/python python_scripts/analyze_lock_events.py \\
        runs/session_a.jsonl runs/session_b.jsonl \\
        --output-json runs/lock_summary.json \\
        --output-csv  runs/lock_summary.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Core logic (importable by tests without argument parsing)
# ---------------------------------------------------------------------------

KNOWN_EVENT_TYPES = ('acquired', 'lost', 'reacquired', 'switch')


def load_events(path: Path) -> list[dict]:
    """Parse a JSONL lock-event file and return list of event dicts."""
    events: list[dict] = []
    with path.open(encoding='utf-8') as fh:
        for lineno, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                print(f'  Warning: {path.name}:{lineno}: {exc}', file=sys.stderr)
    return events


def summarize(events: list[dict], source_name: str = '') -> dict:
    """Compute summary metrics from a list of lock-event dicts.

    Returns a dict with:
      source, total_events, acquired, lost, reacquired, switch,
      switches_per_min_mean, switches_per_min_max, frame_span
    """
    counts = {t: 0 for t in KNOWN_EVENT_TYPES}
    sw_per_min_values: list[float] = []
    frame_indices: list[int] = []

    for ev in events:
        etype = ev.get('event', '')
        if etype in counts:
            counts[etype] += 1
        spm = ev.get('lock_switches_per_min')
        if spm is not None:
            sw_per_min_values.append(float(spm))
        fi = ev.get('frame_index')
        if fi is not None:
            frame_indices.append(int(fi))

    frame_span = (max(frame_indices) - min(frame_indices) + 1) if len(frame_indices) > 1 else len(frame_indices)
    sw_mean = round(sum(sw_per_min_values) / len(sw_per_min_values), 4) if sw_per_min_values else 0.0
    sw_max = round(max(sw_per_min_values), 4) if sw_per_min_values else 0.0

    return {
        'source': source_name,
        'total_events': len(events),
        'acquired': counts['acquired'],
        'lost': counts['lost'],
        'reacquired': counts['reacquired'],
        'switch': counts['switch'],
        'switches_per_min_mean': sw_mean,
        'switches_per_min_max': sw_max,
        'frame_span': frame_span,
    }


def analyze_files(paths: list[Path]) -> list[dict]:
    """Load and summarize each file; return list of per-file summaries."""
    results = []
    for p in paths:
        if not p.exists():
            print(f'Error: file not found: {p}', file=sys.stderr)
            continue
        events = load_events(p)
        result = summarize(events, source_name=p.name)
        results.append(result)
    return results


def print_summary(summaries: list[dict]) -> None:
    """Print human-readable summary table to stdout."""
    if not summaries:
        print('No data.')
        return
    header = f"{'Source':<40} {'Events':>7} {'Acq':>5} {'Lost':>5} {'Reacq':>6} {'Switch':>7} {'Sw/min mean':>12} {'Sw/min max':>11} {'Frames':>8}"
    print(header)
    print('-' * len(header))
    for s in summaries:
        print(
            f"{s['source']:<40} "
            f"{s['total_events']:>7} "
            f"{s['acquired']:>5} "
            f"{s['lost']:>5} "
            f"{s['reacquired']:>6} "
            f"{s['switch']:>7} "
            f"{s['switches_per_min_mean']:>12.4f} "
            f"{s['switches_per_min_max']:>11.4f} "
            f"{s['frame_span']:>8}"
        )


def save_json(summaries: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'JSON saved: {path}')


def save_csv(summaries: list[dict], path: Path) -> None:
    if not summaries:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)
    print(f'CSV saved: {path}')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description='Analyze lock-event JSONL logs and print summary.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        'files',
        nargs='*',
        metavar='LOG',
        help='Path(s) to .jsonl lock-event log files.',
    )
    p.add_argument(
        '--output-json',
        metavar='PATH',
        default='',
        help='Save summary as JSON to this path.',
    )
    p.add_argument(
        '--output-csv',
        metavar='PATH',
        default='',
        help='Save summary as CSV to this path.',
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.files:
        parser.print_help()
        return 0

    paths = [Path(f) for f in args.files]
    summaries = analyze_files(paths)

    print_summary(summaries)

    if args.output_json:
        save_json(summaries, Path(args.output_json))
    if args.output_csv:
        save_csv(summaries, Path(args.output_csv))

    return 0


if __name__ == '__main__':
    sys.exit(main())
