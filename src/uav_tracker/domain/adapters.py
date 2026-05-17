from __future__ import annotations

import time
from typing import Any

from uav_tracker.display.frame_result import FrameOutput
from uav_tracker.tracking.operator_override import OperatorTargetOverride

from .types import Candidate, FrameResult, HealthStatus, OperatorHint, Track, TransitionEvent
from .workflow import derive_operator_workflow_state


def operator_hint_from_override(
    override: OperatorTargetOverride | None,
    *,
    frame_index: int | None = None,
) -> OperatorHint | None:
    if override is None:
        return None
    return OperatorHint(
        kind=str(override.kind),
        point=override.point,
        bbox=override.bbox,
        frame_index=override.frame_index if override.frame_index is not None else frame_index,
        reason=str(override.reason),
    )


def frame_result_from_output(
    output: FrameOutput,
    *,
    source: str,
    frame_width: int,
    frame_height: int,
    candidates_payload: list[dict[str, Any]] | None = None,
    operator_hint: OperatorHint | None = None,
    state_before: str | None = None,
) -> FrameResult:
    state_after = derive_operator_workflow_state(output)
    before = str(state_before if state_before is not None else state_after)
    candidates = tuple(_candidate_from_payload(item) for item in (candidates_payload or []))
    primary_track = Track(
        track_id=output.active_id,
        bbox=output.active_bbox,
        source=str(output.active_source),
        confidence=float(output.display_confidence),
        lock_score=float(output.lock_score),
        reliability=float(output.target_reliability),
        present_probability=float(output.target_p_present),
        operator_verified=str(output.active_source) == "operator",
    ) if output.active_id is not None else None
    transition_events = tuple(
        TransitionEvent(
            event=str(event),
            frame_index=int(output.frame_index),
            state_before=before,
            state_after=state_after,
            payload={
                "active_id": output.active_id,
                "lock_score": round(float(output.lock_score), 4),
            },
        )
        for event in output.lock_events
    )
    workflow_events = tuple(
        TransitionEvent(
            event=str(event),
            frame_index=int(output.frame_index),
            state_before=before,
            state_after=state_after,
            payload={
                "active_id": output.active_id,
                "operator_status": output.operator_override_status,
            },
        )
        for event in getattr(output, "operator_workflow_events", []) or []
    )
    dts_events = ()
    if output.operator_override_status in {"applied", "verifying"} and output.operator_override_bbox is not None:
        dts_events = (
            {
                "event": "operator_bbox",
                "bbox_xyxy": list(output.operator_override_bbox),
                "active_id": output.active_id,
                "operator_status": output.operator_override_status,
            },
        )

    return FrameResult(
        schema_version=1,
        frame_id=int(output.frame_index),
        timestamp_monotonic=time.monotonic(),
        source=str(source),
        source_mode=str(output.target_modality),
        frame_width=int(frame_width),
        frame_height=int(frame_height),
        state_before=before,
        state_after=state_after,
        candidates=candidates,
        primary_track=primary_track,
        operator_hint=operator_hint,
        transition_events=transition_events + workflow_events,
        metrics={
            "fps": float(output.fps),
            "target_count": int(output.target_count),
            "visible_target_count": int(output.visible_target_count),
            "scan_strategy": str(output.scan_strategy),
            "gt_visible": bool(output.gt_visible),
            "gt_iou": float(output.gt_iou),
            "lock_score": float(output.lock_score),
            "display_confidence": float(output.display_confidence),
            "continuity_score": float(output.continuity_score),
            "active_presence_rate": float(output.active_presence_rate),
            "active_id_changes": int(output.active_id_changes),
            "median_reacquire_frames": float(output.median_reacquire_frames),
            "lock_switch_count": int(output.lock_switch_count),
            "lock_switches_per_min": float(output.lock_switches_per_min),
            "budget_level": int(output.budget_level),
            "budget_load": float(output.budget_load),
            "budget_frame_ms": float(output.budget_frame_ms),
            "roi_budget_candidates": int(output.roi_budget_candidates),
            "night_skip": int(output.night_skip),
            "timings_ms": dict(output.timings_ms),
            "tracking_action": str(output.tracking_action),
            "decision_path": str(output.decision_path),
            "operator_override_status": str(output.operator_override_status),
            "operator_override_count": int(output.operator_override_count),
            "operator_workflow_state": str(getattr(output, "operator_workflow_state", state_after)),
            "operator_click_to_lock_frames": getattr(output, "operator_click_to_lock_frames", None),
            "operator_verify_age_frames": int(getattr(output, "operator_verify_age_frames", 0) or 0),
            "mode": str(getattr(output.mode, "value", output.mode)),
            "lock_event_counts": dict(output.lock_event_counts),
            "behavior_drop_count": int(getattr(output, "behavior_drop_count", 0)),
            "scene_label_runtime": str(getattr(output, "scene_label_runtime", "")),
            "scene_confidence_runtime": float(getattr(output, "scene_confidence_runtime", 1.0)),
            "proposal_count_by_source": dict(getattr(output, "proposal_count_by_source", {}) or {}),
            "bbox_area": int(getattr(output, "bbox_area", 0)),
        },
        health=HealthStatus(
            ok=True,
            fps_ok=float(output.fps) > 0.0,
            latency_ok=float(output.budget_frame_ms) >= 0.0,
        ),
        dts_events=dts_events,
    )


def _candidate_from_payload(item: dict[str, Any]) -> Candidate:
    bbox = item.get("bbox") or (0, 0, 0, 0)
    x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
    return Candidate(
        candidate_id=int(item.get("id", 0) or 0),
        bbox=(x1, y1, x2, y2),
        score=float(item.get("score", 0.0) or 0.0),
        confidence=float(item.get("conf", 0.0) or 0.0),
        source=str(item.get("source", "")),
        active=bool(item.get("active", False)),
        lost_frames=int(item.get("lost_frames", 0) or 0),
    )
