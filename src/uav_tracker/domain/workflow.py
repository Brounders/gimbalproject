from __future__ import annotations

from uav_tracker.display.frame_result import FrameOutput


def derive_operator_workflow_state(output: FrameOutput) -> str:
    """Map runtime tracker facts to the compact operator workflow state.

    This is presentation/telemetry language, not a replacement for the current
    low-level tracker state machine.
    """
    explicit_state = str(getattr(output, "operator_workflow_state", "") or "")
    if explicit_state:
        return explicit_state

    operator_status = str(output.operator_override_status or "none")
    mode = str(output.mode).split(".")[-1]
    has_track = output.active_id is not None or output.active_bbox is not None

    if operator_status == "verifying":
        return "VERIFYING"
    if mode == "LOST":
        return "LOST" if has_track else "SEARCH"
    if has_track:
        if output.lock_score >= 0.35 and output.display_confidence >= 0.35:
            return "TRACKING"
        if output.display_confidence > 0.0 or output.lock_score > 0.0:
            return "WEAK_TRACK"
        return "CANDIDATE"
    if int(output.visible_target_count) > 0 or int(output.target_count) > 0:
        return "CANDIDATE"
    return "SEARCH"
