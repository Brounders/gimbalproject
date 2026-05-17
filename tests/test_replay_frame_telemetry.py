"""Tests for FrameResult.from_dict, JsonlTelemetryReader, and replay report."""
from __future__ import annotations

import json
import pytest

from uav_tracker.domain.types import (
    Candidate,
    FrameResult,
    HealthStatus,
    OperatorHint,
    Track,
    TransitionEvent,
)
from uav_tracker.domain.telemetry import JsonlTelemetryReader, JsonlTelemetryWriter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_frame_result(**overrides) -> FrameResult:
    defaults = dict(
        schema_version=1,
        frame_id=5,
        timestamp_monotonic=1.23,
        source="clip.mp4",
        source_mode="rgb",
        frame_width=640,
        frame_height=480,
        state_before="SEARCH",
        state_after="TRACKING",
    )
    defaults.update(overrides)
    return FrameResult(**defaults)


def _write_jsonl(path, frames=(), extra_events=()):
    with JsonlTelemetryWriter(path, flush_every=1) as w:
        for fr in frames:
            w.write_frame(fr)
        for event_name, payload in extra_events:
            w.write_event(event_name, payload)


# ---------------------------------------------------------------------------
# FrameResult.to_dict / from_dict roundtrip
# ---------------------------------------------------------------------------

def test_roundtrip_bbox_is_tuple():
    fr = _minimal_frame_result(
        candidates=(
            Candidate(candidate_id=3, bbox=(10, 20, 30, 40), score=0.8, confidence=0.7, source="yolo"),
        ),
    )
    data = fr.to_dict()
    restored = FrameResult.from_dict(data)
    assert restored.candidates[0].bbox == (10, 20, 30, 40)
    assert isinstance(restored.candidates[0].bbox, tuple)


def test_roundtrip_primary_track_restored():
    track = Track(
        track_id=7,
        bbox=(10, 20, 50, 60),
        source="operator",
        confidence=0.9,
        lock_score=0.85,
        reliability=0.8,
        present_probability=0.95,
        operator_verified=True,
        lock_age=3,
    )
    fr = _minimal_frame_result(primary_track=track)
    restored = FrameResult.from_dict(fr.to_dict())
    assert restored.primary_track is not None
    assert restored.primary_track.track_id == 7
    assert restored.primary_track.bbox == (10, 20, 50, 60)
    assert restored.primary_track.operator_verified is True
    assert restored.primary_track.lock_age == 3


def test_roundtrip_transition_events_restored():
    te = TransitionEvent(
        event="acquired",
        frame_index=12,
        state_before="SEARCH",
        state_after="TRACKING",
        reason="lock_confirmed",
        payload={"active_id": 7},
    )
    fr = _minimal_frame_result(transition_events=(te,))
    restored = FrameResult.from_dict(fr.to_dict())
    assert len(restored.transition_events) == 1
    r_te = restored.transition_events[0]
    assert r_te.event == "acquired"
    assert r_te.frame_index == 12
    assert r_te.state_before == "SEARCH"
    assert r_te.payload == {"active_id": 7}


def test_roundtrip_health_restored():
    health = HealthStatus(ok=True, fps_ok=False, latency_ok=True, message="fps_warn")
    fr = _minimal_frame_result(health=health)
    restored = FrameResult.from_dict(fr.to_dict())
    assert restored.health.fps_ok is False
    assert restored.health.message == "fps_warn"


def test_roundtrip_dts_events_restored():
    dts = ({"event": "operator_bbox", "bbox_xyxy": [1, 2, 3, 4]},)
    fr = _minimal_frame_result(dts_events=dts)
    restored = FrameResult.from_dict(fr.to_dict())
    assert len(restored.dts_events) == 1
    assert restored.dts_events[0]["event"] == "operator_bbox"
    assert restored.dts_events[0]["bbox_xyxy"] == [1, 2, 3, 4]


def test_roundtrip_operator_hint_point_is_tuple():
    hint = OperatorHint(kind="click", point=(120, 80), frame_index=11)
    fr = _minimal_frame_result(operator_hint=hint)
    restored = FrameResult.from_dict(fr.to_dict())
    assert restored.operator_hint is not None
    assert restored.operator_hint.point == (120, 80)
    assert isinstance(restored.operator_hint.point, tuple)


def test_from_dict_missing_optional_fields_safe():
    minimal = {
        "schema_version": 1,
        "frame_id": 0,
        "timestamp_monotonic": 0.0,
        "source": "",
        "source_mode": "",
        "frame_width": 0,
        "frame_height": 0,
        "state_before": "",
        "state_after": "",
    }
    fr = FrameResult.from_dict(minimal)
    assert fr.detections == ()
    assert fr.candidates == ()
    assert fr.primary_track is None
    assert fr.operator_hint is None
    assert fr.transition_events == ()
    assert fr.metrics == {}
    assert fr.dts_events == ()


# ---------------------------------------------------------------------------
# JsonlTelemetryReader
# ---------------------------------------------------------------------------

def test_reader_yields_only_frame_result_events(tmp_path):
    path = tmp_path / "t.jsonl"
    fr = _minimal_frame_result()
    _write_jsonl(path, frames=[fr], extra_events=[("other_event", {"key": "value"})])

    results = list(JsonlTelemetryReader(path))
    assert len(results) == 1
    assert results[0].frame_id == 5


def test_reader_skips_corrupt_line_by_default(tmp_path):
    path = tmp_path / "t.jsonl"
    fr = _minimal_frame_result()
    with JsonlTelemetryWriter(path, flush_every=1) as w:
        w.write_frame(fr)
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"event": "frame_result", BROKEN\n')
        f.write(json.dumps({"event": "frame_result", **_minimal_frame_result(frame_id=99).to_dict()}) + "\n")

    results = list(JsonlTelemetryReader(path, strict=False))
    assert len(results) == 2
    assert results[1].frame_id == 99


def test_reader_strict_raises_on_corrupt_line(tmp_path):
    path = tmp_path / "t.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"event": "frame_result", NOT_JSON\n')

    with pytest.raises(ValueError, match="line 1"):
        list(JsonlTelemetryReader(path, strict=True))


def test_reader_skips_non_frame_result_events(tmp_path):
    path = tmp_path / "t.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"event": "failure_event", "reason": "timeout"}) + "\n")
        f.write(json.dumps({"event": "frame_result", **_minimal_frame_result(frame_id=1).to_dict()}) + "\n")

    results = list(JsonlTelemetryReader(path))
    assert len(results) == 1
    assert results[0].frame_id == 1


# ---------------------------------------------------------------------------
# build_replay_report
# ---------------------------------------------------------------------------

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).parent.parent / "python_scripts"))
from replay_frame_telemetry import build_replay_report, _percentile


def _make_test_jsonl(tmp_path) -> _Path:
    path = tmp_path / "telemetry.jsonl"
    frames = [
        _minimal_frame_result(
            frame_id=i,
            state_after="TRACKING" if i % 2 == 0 else "SEARCH",
            source_mode="rgb",
            transition_events=(
                TransitionEvent(event="acquired", frame_index=i, state_before="SEARCH", state_after="TRACKING"),
            ) if i == 0 else (),
            metrics={
                "fps": 25.0 + i,
                "budget_frame_ms": 10.0 + i,
                "mode": "TRACK" if i % 2 == 0 else "LOST",
                "behavior_drop_count": 1 if i == 1 else 0,
                "lock_event_counts": {"acquired": 1} if i == 0 else {},
            },
            operator_hint=OperatorHint(kind="click", point=(100, 80)) if i == 0 else None,
            dts_events=({"event": "operator_bbox"},) if i == 0 else (),
        )
        for i in range(4)
    ]
    _write_jsonl(path, frames=frames, extra_events=[("other", {"x": 1})])
    return path


def test_report_total_frames(tmp_path):
    path = _make_test_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["total_frames"] == 4


def test_report_state_counts(tmp_path):
    path = _make_test_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["state_counts"]["TRACKING"] == 2
    assert report["state_counts"]["SEARCH"] == 2


def test_report_raw_mode_counts(tmp_path):
    path = _make_test_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["raw_mode_counts"]["TRACK"] == 2
    assert report["raw_mode_counts"]["LOST"] == 2


def test_report_transition_counts(tmp_path):
    path = _make_test_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["transition_counts"].get("acquired", 0) == 1


def test_report_avg_fps(tmp_path):
    path = _make_test_jsonl(tmp_path)
    report = build_replay_report(path)
    # fps: 25, 26, 27, 28 → avg = 26.5
    assert abs(report["avg_fps"] - 26.5) < 0.01


def test_report_latency_percentiles(tmp_path):
    path = _make_test_jsonl(tmp_path)
    report = build_replay_report(path)
    # latency: 10, 11, 12, 13 sorted; p95 idx = max(0, int(4*95/100)-1) = 2 → 12.0
    assert report["latency_p95_ms"] is not None
    assert report["latency_p99_ms"] is not None


def test_report_behavior_drop_count_total(tmp_path):
    path = _make_test_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["behavior_drop_count_total"] == 1


def test_report_lock_event_counts_total(tmp_path):
    path = _make_test_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["lock_event_counts_total"].get("acquired", 0) == 1


def test_percentile_p95_two_element_list():
    # ceil nearest-rank: ceil(0.95 * 2) - 1 = ceil(1.9) - 1 = 2 - 1 = 1 → 20.0
    assert _percentile([10.0, 20.0], 95) == 20.0


def test_percentile_p99_two_element_list():
    assert _percentile([10.0, 20.0], 99) == 20.0


def test_percentile_p50_four_elements():
    # ceil(0.50 * 4) - 1 = ceil(2.0) - 1 = 2 - 1 = 1 → sorted[1] = 20
    assert _percentile([10.0, 20.0, 30.0, 40.0], 50) == 20.0


def test_percentile_empty_returns_none():
    assert _percentile([], 95) is None


def test_report_empty_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    report = build_replay_report(path)
    assert report["total_frames"] == 0
    assert report["avg_fps"] is None
    assert report["latency_p95_ms"] is None
    assert report["first_frame_id"] is None
    assert report["last_frame_id"] is None


# ---------------------------------------------------------------------------
# Operator / DTS diagnostics
# ---------------------------------------------------------------------------

def _make_operator_jsonl(tmp_path) -> _Path:
    path = tmp_path / "op_telemetry.jsonl"
    frames = [
        # frame 0: applied override, confirmed event, click_to_lock=5, dts operator_bbox
        _minimal_frame_result(
            frame_id=0,
            metrics={
                "operator_override_status": "applied",
                "operator_workflow_events": ["confirmed"],
                "operator_click_to_lock_frames": 5,
            },
            dts_events=({"event": "operator_bbox", "bbox_xyxy": [1, 2, 3, 4]},),
        ),
        # frame 1: rejected override, lost event, no click_to_lock, no dts
        _minimal_frame_result(
            frame_id=1,
            metrics={
                "operator_override_status": "rejected",
                "operator_workflow_events": ["lost"],
            },
            dts_events=(),
        ),
        # frame 2: applied override again, click_to_lock=15, two dts events (one non-bbox)
        _minimal_frame_result(
            frame_id=2,
            metrics={
                "operator_override_status": "applied",
                "operator_click_to_lock_frames": 15,
            },
            dts_events=(
                {"event": "operator_bbox", "bbox_xyxy": [5, 6, 7, 8]},
                {"event": "operator_release"},
            ),
        ),
        # frame 3: no override status
        _minimal_frame_result(frame_id=3),
    ]
    _write_jsonl(path, frames=frames)
    return path


def test_operator_applied_count(tmp_path):
    path = _make_operator_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["operator_applied_count"] == 2


def test_operator_rejected_count(tmp_path):
    path = _make_operator_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["operator_rejected_count"] == 1


def test_operator_confirmed_count(tmp_path):
    path = _make_operator_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["operator_confirmed_count"] == 1


def test_operator_lost_count(tmp_path):
    path = _make_operator_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["operator_lost_count"] == 1


def test_dts_operator_bbox_count(tmp_path):
    path = _make_operator_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["dts_operator_bbox_count"] == 2


def test_avg_click_to_lock_frames(tmp_path):
    path = _make_operator_jsonl(tmp_path)
    report = build_replay_report(path)
    # values: [5, 15] → avg = 10.0
    assert abs(report["avg_click_to_lock_frames"] - 10.0) < 0.01


def test_median_click_to_lock_frames(tmp_path):
    path = _make_operator_jsonl(tmp_path)
    report = build_replay_report(path)
    # _percentile([5, 15], 50): ceil(0.5*2)-1=0 → 5.0
    assert report["median_click_to_lock_frames"] == 5.0


def test_max_click_to_lock_frames(tmp_path):
    path = _make_operator_jsonl(tmp_path)
    report = build_replay_report(path)
    assert report["max_click_to_lock_frames"] == 15.0


def test_operator_diagnostics_zero_when_no_overrides(tmp_path):
    path = tmp_path / "no_op.jsonl"
    _write_jsonl(path, frames=[_minimal_frame_result(frame_id=0)])
    report = build_replay_report(path)
    assert report["operator_applied_count"] == 0
    assert report["operator_rejected_count"] == 0
    assert report["operator_confirmed_count"] == 0
    assert report["operator_lost_count"] == 0
    assert report["dts_operator_bbox_count"] == 0
    assert report["avg_click_to_lock_frames"] is None
    assert report["median_click_to_lock_frames"] is None
    assert report["max_click_to_lock_frames"] is None
