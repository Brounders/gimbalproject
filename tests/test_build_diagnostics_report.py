"""Tests for build_diagnostics_report.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).parent.parent / "python_scripts"))
from build_diagnostics_report import build_combined_json, build_diagnostics_report


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _quality(*, false_lock_rate: float = 0.1) -> dict:
    return {
        "report_type": "quality_gate",
        "gate_passed": True,
        "preset": "day",
        "rows": [{"clip": "a.mp4"}, {"clip": "b.mp4"}],
        "failures": [],
        "mean": {
            "false_lock_rate": false_lock_rate,
            "active_presence_rate": 0.85,
            "continuity_score": 0.92,
            "active_id_changes_per_min": 3.5,
        },
    }


def _telemetry(
    *,
    hint_count: int = 0,
    applied: int = 0,
    confirmed: int = 0,
    rejected: int = 0,
    lost: int = 0,
    dts_event_count: int = 0,
    dts_bbox_count: int = 0,
    avg_ctl: float | None = None,
    median_ctl: float | None = None,
    max_ctl: float | None = None,
    latency_p99: float | None = None,
    latency_p95: float | None = None,
    total_frames: int = 100,
) -> dict:
    return {
        "total_frames": total_frames,
        "operator_hint_count": hint_count,
        "operator_applied_count": applied,
        "operator_confirmed_count": confirmed,
        "operator_rejected_count": rejected,
        "operator_lost_count": lost,
        "dts_event_count": dts_event_count,
        "dts_operator_bbox_count": dts_bbox_count,
        "avg_click_to_lock_frames": avg_ctl,
        "median_click_to_lock_frames": median_ctl,
        "max_click_to_lock_frames": max_ctl,
        "latency_p95_ms": latency_p95,
        "latency_p99_ms": latency_p99,
    }


# ---------------------------------------------------------------------------
# Section presence
# ---------------------------------------------------------------------------

def test_markdown_contains_all_sections():
    md, _ = build_diagnostics_report(_quality(), _telemetry())
    for section in ("## Summary", "## Tracking Quality", "## Operator Click Flow",
                    "## DTS Events", "## Risks / Next Action"):
        assert section in md, f"Missing section: {section}"


def test_markdown_tracking_quality_contains_metrics():
    md, _ = build_diagnostics_report(_quality(), _telemetry(latency_p99=30.0, latency_p95=20.0))
    assert "false_lock_rate" in md
    assert "active_presence_rate" in md
    assert "continuity_score" in md
    assert "active_id_changes_per_min" in md
    assert "latency_p95_ms" in md
    assert "latency_p99_ms" in md


def test_markdown_operator_click_flow_contains_metrics():
    md, _ = build_diagnostics_report(
        _quality(),
        _telemetry(hint_count=3, applied=2, confirmed=1, rejected=1, lost=0,
                   avg_ctl=8.0, median_ctl=7.0, max_ctl=12.0),
    )
    assert "operator_hint_count" in md
    assert "operator_applied_count" in md
    assert "operator_confirmed_count" in md
    assert "operator_rejected_count" in md
    assert "operator_lost_count" in md
    assert "avg_click_to_lock_frames" in md
    assert "median_click_to_lock_frames" in md
    assert "max_click_to_lock_frames" in md


def test_markdown_dts_events_contains_metrics():
    md, _ = build_diagnostics_report(
        _quality(), _telemetry(dts_event_count=5, dts_bbox_count=3),
    )
    assert "dts_event_count" in md
    assert "dts_operator_bbox_count" in md


# ---------------------------------------------------------------------------
# Risk detection
# ---------------------------------------------------------------------------

def test_risk_false_lock():
    _, risks = build_diagnostics_report(_quality(false_lock_rate=0.7), _telemetry())
    assert any("false-lock" in r for r in risks)


def test_risk_click_not_converting():
    _, risks = build_diagnostics_report(
        _quality(),
        _telemetry(hint_count=5, confirmed=0),
    )
    assert any("click hints not converting" in r for r in risks)


def test_risk_dts_capture_missing():
    _, risks = build_diagnostics_report(
        _quality(),
        _telemetry(hint_count=4, dts_bbox_count=0),
    )
    assert any("DTS capture missing" in r for r in risks)


def test_risk_latency():
    _, risks = build_diagnostics_report(
        _quality(),
        _telemetry(latency_p99=80.0),
    )
    assert any("latency risk" in r for r in risks)


def test_no_risks():
    _, risks = build_diagnostics_report(
        _quality(false_lock_rate=0.1),
        _telemetry(),
    )
    assert risks == []


def test_no_risks_message_in_markdown():
    md, _ = build_diagnostics_report(_quality(false_lock_rate=0.1), _telemetry())
    assert "No immediate diagnostic risk" in md


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def test_json_output_expected_keys(tmp_path):
    quality = _quality()
    telemetry = _telemetry()
    _, risks = build_diagnostics_report(quality, telemetry)
    combined = build_combined_json(quality, telemetry, risks)

    assert "quality" in combined
    assert "telemetry" in combined
    assert "risks" in combined
    assert combined["quality"] is quality
    assert combined["telemetry"] is telemetry
    assert isinstance(combined["risks"], list)


def test_json_output_written_to_file(tmp_path):
    quality = _quality(false_lock_rate=0.8)
    telemetry = _telemetry(hint_count=2, confirmed=0, dts_bbox_count=0, latency_p99=60.0)
    md, risks = build_diagnostics_report(quality, telemetry)
    combined = build_combined_json(quality, telemetry, risks)

    json_path = tmp_path / "combined.json"
    json_path.write_text(json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")

    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert "quality" in loaded
    assert "telemetry" in loaded
    assert len(loaded["risks"]) >= 3  # false-lock + click + dts + latency
