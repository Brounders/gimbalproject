from __future__ import annotations

import json

from uav_tracker.display.frame_result import FrameOutput
from uav_tracker.domain import (
    JsonlTelemetryWriter,
    derive_operator_workflow_state,
    OperatorHint,
    frame_result_from_output,
)
from uav_tracker.tracking.operator_override import OperatorTargetOverride
from uav_tracker.domain import operator_hint_from_override


def _frame_output(**overrides) -> FrameOutput:
    values = {
        "frame": None,
        "fps": 25.0,
        "active_id": 7,
        "active_source": "operator",
        "active_bbox": (10, 20, 30, 40),
        "target_count": 2,
        "visible_target_count": 2,
        "mode": "TRACK",
        "frame_index": 12,
        "scan_strategy": "OPERATOR-LOCK",
        "gt_visible": False,
        "gt_iou": 0.0,
        "lock_score": 0.81,
        "display_confidence": 0.74,
        "continuity_score": 0.66,
        "active_presence_rate": 0.70,
        "active_id_changes": 1,
        "median_reacquire_frames": 3.0,
        "lock_events": ["acquired"],
        "lock_switch_count": 1,
        "lock_switches_per_min": 2.0,
        "lock_event_counts": {"acquired": 1},
        "budget_level": 1,
        "budget_load": 0.2,
        "budget_frame_ms": 14.5,
        "roi_budget_candidates": 2,
        "night_skip": 0,
        "timings_ms": {"global": 4.0},
        "target_reliability": 0.82,
        "target_p_present": 0.91,
        "tracking_action": "hold",
        "target_modality": "rgb",
        "decision_path": "telemetry_only",
        "behavior_drop_count": 0,
        "operator_override_status": "applied",
        "operator_override_count": 1,
        "operator_override_bbox": (10, 20, 30, 40),
    }
    values.update(overrides)
    return FrameOutput(**values)


def test_operator_hint_from_click_override() -> None:
    override = OperatorTargetOverride.from_click(120, 80, frame_index=11)

    hint = operator_hint_from_override(override, frame_index=12)

    assert isinstance(hint, OperatorHint)
    assert hint.kind == "click"
    assert hint.point == (120, 80)
    assert hint.frame_index == 11
    assert hint.reason == "operator_click"


def test_frame_result_adapter_preserves_frame_facts() -> None:
    output = _frame_output()

    result = frame_result_from_output(
        output,
        source="clip.mp4",
        frame_width=640,
        frame_height=480,
        candidates_payload=[
            {"id": 7, "bbox": [10, 20, 30, 40], "conf": 0.7, "score": 0.8, "source": "operator", "active": True},
            {"id": 8, "bbox": [50, 60, 90, 100], "conf": 0.5, "score": 0.6, "source": "yolo", "active": False},
        ],
        operator_hint=OperatorHint(kind="click", point=(20, 30), frame_index=12),
        state_before="VERIFYING",
    )

    data = result.to_dict()
    assert data["frame_id"] == 12
    assert data["source"] == "clip.mp4"
    assert data["state_before"] == "VERIFYING"
    assert data["state_after"] == "TRACKING"
    assert data["primary_track"]["track_id"] == 7
    assert data["primary_track"]["operator_verified"] is True
    assert data["candidates"][1]["candidate_id"] == 8
    assert data["operator_hint"]["point"] == [20, 30]
    assert data["transition_events"][0]["event"] == "acquired"
    assert data["dts_events"][0]["event"] == "operator_bbox"
    assert data["metrics"]["scan_strategy"] == "OPERATOR-LOCK"


def test_workflow_state_reports_verifying_for_operator_hint() -> None:
    output = _frame_output(
        operator_override_status="verifying",
        lock_score=0.0,
        display_confidence=0.0,
    )

    assert derive_operator_workflow_state(output) == "VERIFYING"


def test_workflow_state_reports_candidate_for_visible_non_active_target() -> None:
    output = _frame_output(
        active_id=None,
        active_bbox=None,
        visible_target_count=1,
        target_count=1,
        operator_override_status="none",
    )

    assert derive_operator_workflow_state(output) == "CANDIDATE"


def test_frame_result_metrics_include_raw_mode() -> None:
    output = _frame_output(mode="TRACK")
    result = frame_result_from_output(output, source="clip.mp4", frame_width=640, frame_height=480)
    assert result.metrics["mode"] == "TRACK"


def test_frame_result_metrics_include_raw_mode_lost() -> None:
    output = _frame_output(mode="LOST")
    result = frame_result_from_output(output, source="clip.mp4", frame_width=640, frame_height=480)
    assert result.metrics["mode"] == "LOST"


def test_frame_result_metrics_include_lock_event_counts() -> None:
    output = _frame_output(lock_event_counts={"switch": 2, "lost": 1})
    result = frame_result_from_output(output, source="clip.mp4", frame_width=640, frame_height=480)
    assert result.metrics["lock_event_counts"] == {"switch": 2, "lost": 1}


def test_frame_result_metrics_include_behavior_drop_count() -> None:
    output = _frame_output(behavior_drop_count=3)
    result = frame_result_from_output(output, source="clip.mp4", frame_width=640, frame_height=480)
    assert result.metrics["behavior_drop_count"] == 3


def test_jsonl_telemetry_writer_writes_frame_result(tmp_path) -> None:
    output = _frame_output()
    result = frame_result_from_output(output, source="clip.mp4", frame_width=640, frame_height=480)
    path = tmp_path / "telemetry.jsonl"

    with JsonlTelemetryWriter(path, flush_every=1) as writer:
        writer.write_frame(result)
        writer.write_event("failure_event", {"frame_id": 12, "reason": "detector_timeout"})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["event"] == "frame_result"
    assert first["primary_track"]["bbox"] == [10, 20, 30, 40]
    assert second == {"event": "failure_event", "frame_id": 12, "reason": "detector_timeout"}
