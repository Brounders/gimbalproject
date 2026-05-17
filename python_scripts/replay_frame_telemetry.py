"""CLI tool: replay a frame telemetry JSONL and produce a summary report.

Usage:
    PYTHONPATH=src python python_scripts/replay_frame_telemetry.py \
        --input path/to/telemetry.jsonl [--output report.json] [--strict]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uav_tracker.domain.telemetry import JsonlTelemetryReader


def _percentile(values: list[float], p: int) -> float | None:
    if not values:
        return None
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    idx = max(0, math.ceil(p / 100 * n) - 1)
    return sorted_vals[min(idx, n - 1)]


def build_replay_report(path: str | Path, *, strict: bool = False) -> dict:
    path = Path(path)
    reader = JsonlTelemetryReader(path, strict=strict)

    total_frames = 0
    source_modes: dict[str, int] = {}
    state_counts: dict[str, int] = {}
    raw_mode_counts: dict[str, int] = {}
    transition_counts: dict[str, int] = {}
    operator_hint_count = 0
    operator_applied_count = 0
    operator_rejected_count = 0
    operator_confirmed_count = 0
    operator_lost_count = 0
    dts_event_count = 0
    dts_operator_bbox_count = 0
    click_to_lock_values: list[float] = []
    fps_values: list[float] = []
    latency_values: list[float] = []
    behavior_drop_count_total = 0
    lock_event_counts_total: dict[str, int] = {}
    first_frame_id: int | None = None
    last_frame_id: int | None = None

    for fr in reader:
        total_frames += 1

        source_modes[fr.source_mode] = source_modes.get(fr.source_mode, 0) + 1
        state_counts[fr.state_after] = state_counts.get(fr.state_after, 0) + 1

        raw_mode = fr.metrics.get("mode")
        if isinstance(raw_mode, str):
            raw_mode_counts[raw_mode] = raw_mode_counts.get(raw_mode, 0) + 1

        for te in fr.transition_events:
            transition_counts[te.event] = transition_counts.get(te.event, 0) + 1

        if fr.operator_hint is not None:
            operator_hint_count += 1

        op_status = fr.metrics.get("operator_override_status")
        if op_status == "applied":
            operator_applied_count += 1
        elif op_status == "rejected":
            operator_rejected_count += 1

        op_wf_events = fr.metrics.get("operator_workflow_events") or []
        if isinstance(op_wf_events, list):
            for ev in op_wf_events:
                if ev == "confirmed":
                    operator_confirmed_count += 1
                elif ev == "lost":
                    operator_lost_count += 1

        ctl = fr.metrics.get("operator_click_to_lock_frames")
        if isinstance(ctl, (int, float)) and ctl is not None:
            click_to_lock_values.append(float(ctl))

        dts_event_count += len(fr.dts_events)
        dts_operator_bbox_count += sum(
            1 for ev in fr.dts_events if isinstance(ev, dict) and ev.get("event") == "operator_bbox"
        )

        fps_val = fr.metrics.get("fps")
        if isinstance(fps_val, (int, float)):
            fps_values.append(float(fps_val))

        lat_val = fr.metrics.get("budget_frame_ms")
        if isinstance(lat_val, (int, float)):
            latency_values.append(float(lat_val))

        bdc = fr.metrics.get("behavior_drop_count")
        if isinstance(bdc, (int, float)):
            behavior_drop_count_total += int(bdc)

        lec = fr.metrics.get("lock_event_counts")
        if isinstance(lec, dict):
            for k, v in lec.items():
                lock_event_counts_total[k] = lock_event_counts_total.get(k, 0) + int(v)

        if first_frame_id is None:
            first_frame_id = fr.frame_id
        last_frame_id = fr.frame_id

    avg_fps = (sum(fps_values) / len(fps_values)) if fps_values else None

    return {
        "schema_version": 1,
        "input": str(path),
        "total_frames": total_frames,
        "source_modes": source_modes,
        "state_counts": state_counts,
        "raw_mode_counts": raw_mode_counts,
        "transition_counts": transition_counts,
        "operator_hint_count": operator_hint_count,
        "operator_applied_count": operator_applied_count,
        "operator_rejected_count": operator_rejected_count,
        "operator_confirmed_count": operator_confirmed_count,
        "operator_lost_count": operator_lost_count,
        "dts_event_count": dts_event_count,
        "dts_operator_bbox_count": dts_operator_bbox_count,
        "avg_click_to_lock_frames": (sum(click_to_lock_values) / len(click_to_lock_values)) if click_to_lock_values else None,
        "median_click_to_lock_frames": _percentile(click_to_lock_values, 50),
        "max_click_to_lock_frames": max(click_to_lock_values) if click_to_lock_values else None,
        "avg_fps": avg_fps,
        "latency_p95_ms": _percentile(latency_values, 95),
        "latency_p99_ms": _percentile(latency_values, 99),
        "behavior_drop_count_total": behavior_drop_count_total,
        "lock_event_counts_total": lock_event_counts_total,
        "first_frame_id": first_frame_id,
        "last_frame_id": last_frame_id,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Replay frame telemetry JSONL and produce a report.")
    parser.add_argument("--input", required=True, metavar="PATH", help="Input JSONL file")
    parser.add_argument("--output", metavar="PATH", help="Optional output JSON file")
    parser.add_argument("--strict", action="store_true", help="Raise on malformed lines")
    args = parser.parse_args(argv)

    report = build_replay_report(args.input, strict=args.strict)
    output_str = json.dumps(report, ensure_ascii=False, indent=2)
    print(output_str)

    if args.output:
        Path(args.output).write_text(output_str, encoding="utf-8")


if __name__ == "__main__":
    main()
