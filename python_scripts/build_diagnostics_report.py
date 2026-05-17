"""build_diagnostics_report.py — combine quality gate + frame telemetry into a
human-readable diagnostics markdown report.

Read-only: reads two JSON files, writes markdown (and optionally JSON). Does not
run any pipeline or gate commands.

Usage::

    python python_scripts/build_diagnostics_report.py \\
        --quality-json path/to/quality_gate.json \\
        --telemetry-json path/to/telemetry_report.json \\
        --output report.md \\
        --json-output combined.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Risk detection
# ---------------------------------------------------------------------------

_FALSE_LOCK_THRESHOLD = 0.55
_LATENCY_P99_THRESHOLD_MS = 50.0


def _detect_risks(quality: dict, telemetry: dict) -> list[str]:
    risks: list[str] = []

    false_lock = quality.get("mean", {}).get("false_lock_rate")
    if false_lock is None:
        false_lock = quality.get("false_lock_rate")
    if isinstance(false_lock, (int, float)) and float(false_lock) > _FALSE_LOCK_THRESHOLD:
        risks.append(f"false-lock risk: false_lock_rate={false_lock:.3f} > {_FALSE_LOCK_THRESHOLD}")

    hint_count = telemetry.get("operator_hint_count", 0)
    confirmed = telemetry.get("operator_confirmed_count", 0)
    if hint_count > 0 and confirmed == 0:
        risks.append(f"click hints not converting: {hint_count} hint(s), 0 confirmed")

    bbox_count = telemetry.get("dts_operator_bbox_count", 0)
    if hint_count > 0 and bbox_count == 0:
        risks.append(f"DTS capture missing: {hint_count} hint(s) but 0 operator_bbox events")

    lat_p99 = telemetry.get("latency_p99_ms")
    if isinstance(lat_p99, (int, float)) and float(lat_p99) > _LATENCY_P99_THRESHOLD_MS:
        risks.append(f"latency risk: latency_p99_ms={lat_p99:.1f} > {_LATENCY_P99_THRESHOLD_MS}")

    return risks


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _fmt(value, fmt: str = ".4f", fallback: str = "n/a") -> str:
    if value is None:
        return fallback
    try:
        return format(float(value), fmt)
    except (TypeError, ValueError):
        return str(value)


def _row(label: str, value) -> str:
    return f"| {label} | {value} |"


def build_diagnostics_report(quality: dict, telemetry: dict) -> tuple[str, list[str]]:
    """Return (markdown_text, risks_list)."""
    risks = _detect_risks(quality, telemetry)

    mean = quality.get("mean", {})
    gate_passed = quality.get("gate_passed")
    preset = quality.get("preset", "")
    total_clips = len(quality.get("rows", []))
    failures = quality.get("failures", [])

    false_lock_rate = mean.get("false_lock_rate", quality.get("false_lock_rate"))
    active_presence_rate = mean.get("active_presence_rate", quality.get("active_presence_rate"))
    continuity_score = mean.get("continuity_score", quality.get("continuity_score"))
    id_changes_per_min = mean.get("active_id_changes_per_min", quality.get("active_id_changes_per_min"))
    lat_p95 = telemetry.get("latency_p95_ms")
    lat_p99 = telemetry.get("latency_p99_ms")

    lines: list[str] = []

    # Summary
    gate_status = "PASS" if gate_passed else ("FAIL" if gate_passed is False else "unknown")
    lines.append("# Diagnostics Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Gate**: {gate_status}")
    if preset:
        lines.append(f"- **Preset**: {preset}")
    lines.append(f"- **Clips evaluated**: {total_clips}")
    lines.append(f"- **Total frames (telemetry)**: {telemetry.get('total_frames', 'n/a')}")
    if failures:
        lines.append(f"- **Gate failures**: {', '.join(str(f) for f in failures)}")
    lines.append("")

    # Tracking Quality
    lines.append("## Tracking Quality")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(_row("false_lock_rate", _fmt(false_lock_rate)))
    lines.append(_row("active_presence_rate", _fmt(active_presence_rate)))
    lines.append(_row("continuity_score", _fmt(continuity_score)))
    lines.append(_row("active_id_changes_per_min", _fmt(id_changes_per_min)))
    lines.append(_row("latency_p95_ms", _fmt(lat_p95, ".1f")))
    lines.append(_row("latency_p99_ms", _fmt(lat_p99, ".1f")))
    lines.append("")

    # Operator Click Flow
    lines.append("## Operator Click Flow")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(_row("operator_hint_count", telemetry.get("operator_hint_count", 0)))
    lines.append(_row("operator_applied_count", telemetry.get("operator_applied_count", 0)))
    lines.append(_row("operator_confirmed_count", telemetry.get("operator_confirmed_count", 0)))
    lines.append(_row("operator_rejected_count", telemetry.get("operator_rejected_count", 0)))
    lines.append(_row("operator_lost_count", telemetry.get("operator_lost_count", 0)))
    lines.append(_row("avg_click_to_lock_frames", _fmt(telemetry.get("avg_click_to_lock_frames"), ".1f")))
    lines.append(_row("median_click_to_lock_frames", _fmt(telemetry.get("median_click_to_lock_frames"), ".1f")))
    lines.append(_row("max_click_to_lock_frames", _fmt(telemetry.get("max_click_to_lock_frames"), ".1f")))
    lines.append("")

    # DTS Events
    lines.append("## DTS Events")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(_row("dts_event_count", telemetry.get("dts_event_count", 0)))
    lines.append(_row("dts_operator_bbox_count", telemetry.get("dts_operator_bbox_count", 0)))
    lines.append("")

    # Risks / Next Action
    lines.append("## Risks / Next Action")
    lines.append("")
    if risks:
        for risk in risks:
            lines.append(f"- {risk}")
    else:
        lines.append("- No immediate diagnostic risk")
    lines.append("")

    return "\n".join(lines), risks


def build_combined_json(quality: dict, telemetry: dict, risks: list[str]) -> dict:
    return {
        "quality": quality,
        "telemetry": telemetry,
        "risks": risks,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--quality-json", required=True, type=Path, metavar="PATH",
                   help="JSON output from run_quality_gate.py")
    p.add_argument("--telemetry-json", required=True, type=Path, metavar="PATH",
                   help="JSON output from replay_frame_telemetry.py")
    p.add_argument("--output", required=True, type=Path, metavar="PATH",
                   help="Output markdown report path")
    p.add_argument("--json-output", type=Path, metavar="PATH",
                   help="Optional combined JSON output path")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    quality = json.loads(args.quality_json.read_text(encoding="utf-8"))
    telemetry = json.loads(args.telemetry_json.read_text(encoding="utf-8"))

    markdown, risks = build_diagnostics_report(quality, telemetry)
    args.output.write_text(markdown, encoding="utf-8")
    print(f"Report: {args.output}")

    if args.json_output:
        combined = build_combined_json(quality, telemetry, risks)
        args.json_output.write_text(json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"JSON:   {args.json_output}")

    if risks:
        for risk in risks:
            print(f"[risk] {risk}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
