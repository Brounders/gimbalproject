"""dts_diagnostics.py — build diagnostics.md for a DTS candidate compare result.

Pure functions; no Qt, no subprocess, no file I/O except in the caller.
"""
from __future__ import annotations

from typing import Optional

_FALSE_LOCK_THRESHOLD = 0.55
_LATENCY_P99_THRESHOLD_MS = 50.0


def _detect_compare_risks(gate_decision: dict, telemetry: Optional[dict]) -> list[str]:
    risks: list[str] = []

    for ctx in gate_decision.get("contexts", []):
        fl = ctx.get("false_lock_rate")
        if isinstance(fl, (int, float)) and float(fl) > _FALSE_LOCK_THRESHOLD:
            risks.append(
                f"false-lock risk in {ctx.get('context', '?')}: {fl:.3f} > {_FALSE_LOCK_THRESHOLD}"
            )

    if telemetry:
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


def _fmt(value, fmt: str = ".4f", fallback: str = "n/a") -> str:
    if value is None:
        return fallback
    try:
        return format(float(value), fmt)
    except (TypeError, ValueError):
        return str(value)


def build_compare_diagnostics_md(
    gate_decision: dict,
    telemetry: Optional[dict],
    summary_rows: Optional[list[dict]] = None,
) -> str:
    risks = _detect_compare_risks(gate_decision, telemetry)

    gate_status = gate_decision.get("gate_status", "unknown")
    candidate_pass = gate_decision.get("candidate_pass", "?")
    candidate_total = gate_decision.get("candidate_total", "?")
    accept_allowed = gate_decision.get("accept_allowed", False)
    generated_at = gate_decision.get("generated_at_utc", "")
    contexts = gate_decision.get("contexts", [])

    lines: list[str] = []

    # Summary
    lines.append("# Diagnostics Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Gate**: {gate_status}")
    lines.append(f"- **Candidate**: {candidate_pass}/{candidate_total} contexts passed")
    lines.append(f"- **Accept allowed**: {'yes' if accept_allowed else 'no'}")
    if generated_at:
        lines.append(f"- **Generated**: {generated_at}")
    lines.append("")

    # Candidate Gate
    lines.append("## Candidate Gate")
    lines.append("")
    if contexts:
        lines.append("| Context | Result | presence | false_lock | id/min |")
        lines.append("|---------|--------|----------|------------|--------|")
        for ctx in contexts:
            name = ctx.get("context", ctx.get("name", "?"))
            passed = "PASS" if ctx.get("passed") or ctx.get("candidate_passed") else "FAIL"
            pres = _fmt(ctx.get("active_presence_rate", ctx.get("presence")), ".3f")
            fl = _fmt(ctx.get("false_lock_rate", ctx.get("false_lock")), ".3f")
            idchg = _fmt(ctx.get("active_id_changes_per_min", ctx.get("id_changes")), ".1f")
            lines.append(f"| {name} | {passed} | {pres} | {fl} | {idchg} |")
    elif summary_rows:
        candidate_rows = [r for r in summary_rows if r.get("model", "") != "baseline"]
        if candidate_rows:
            lines.append("| Context | Result | presence | false_lock | id/min |")
            lines.append("|---------|--------|----------|------------|--------|")
            for row in candidate_rows:
                name = row.get("context", "?")
                passed = "PASS" if row.get("passed", "").lower() in {"1", "true", "yes", "pass", "passed"} else "FAIL"
                pres = _fmt(row.get("active_presence_rate"), ".3f")
                fl = _fmt(row.get("false_lock_rate"), ".3f")
                idchg = _fmt(row.get("active_id_changes_per_min"), ".1f")
                lines.append(f"| {name} | {passed} | {pres} | {fl} | {idchg} |")
        else:
            lines.append("_No candidate rows in summary._")
    else:
        lines.append("_No context data available._")
    lines.append("")

    # Operator / DTS Telemetry
    lines.append("## Operator / DTS Telemetry")
    lines.append("")
    if telemetry is None:
        lines.append("Frame telemetry not available.")
    else:
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| operator_hint_count | {telemetry.get('operator_hint_count', 0)} |")
        lines.append(f"| operator_applied_count | {telemetry.get('operator_applied_count', 0)} |")
        lines.append(f"| operator_confirmed_count | {telemetry.get('operator_confirmed_count', 0)} |")
        lines.append(f"| operator_rejected_count | {telemetry.get('operator_rejected_count', 0)} |")
        lines.append(f"| operator_lost_count | {telemetry.get('operator_lost_count', 0)} |")
        lines.append(f"| avg_click_to_lock_frames | {_fmt(telemetry.get('avg_click_to_lock_frames'), '.1f')} |")
        lines.append(f"| median_click_to_lock_frames | {_fmt(telemetry.get('median_click_to_lock_frames'), '.1f')} |")
        lines.append(f"| max_click_to_lock_frames | {_fmt(telemetry.get('max_click_to_lock_frames'), '.1f')} |")
        lines.append(f"| dts_event_count | {telemetry.get('dts_event_count', 0)} |")
        lines.append(f"| dts_operator_bbox_count | {telemetry.get('dts_operator_bbox_count', 0)} |")
        lines.append(f"| latency_p95_ms | {_fmt(telemetry.get('latency_p95_ms'), '.1f')} |")
        lines.append(f"| latency_p99_ms | {_fmt(telemetry.get('latency_p99_ms'), '.1f')} |")
    lines.append("")

    # Next Action
    lines.append("## Next Action")
    lines.append("")
    if risks:
        for risk in risks:
            lines.append(f"- {risk}")
    else:
        lines.append("- No immediate diagnostic risk")
    lines.append("")

    return "\n".join(lines)
