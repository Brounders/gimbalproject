from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from uav_tracker.config import Config
from uav_tracker.tracking.tracked_target import TrackedTarget


class OperatorWorkflowState(str, Enum):
    SEARCH = "SEARCH"
    CANDIDATE = "CANDIDATE"
    VERIFYING = "VERIFYING"
    TRACKING = "TRACKING"
    WEAK_TRACK = "WEAK_TRACK"
    LOST = "LOST"


@dataclass(frozen=True)
class OperatorWorkflowResult:
    state: OperatorWorkflowState
    events: list[str]
    click_to_lock_frames: int | None = None
    verify_age_frames: int = 0


class OperatorWorkflowMachine:
    """Operator-facing tracking workflow.

    This machine does not replace the legacy SCAN/TRACK/LOST state.  It is the
    product-level contract for UI, telemetry, DTS and future quality gates.
    """

    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self.state = OperatorWorkflowState.SEARCH
        self._verify_start_frame: int | None = None
        self._last_click_to_lock_frames: int | None = None

    def update(
        self,
        *,
        frame_index: int,
        active: TrackedTarget | None,
        visible_count: int,
        operator_override_status: str,
        lock_score: float,
        display_confidence: float,
        low_level_mode: str,
    ) -> OperatorWorkflowResult:
        previous = self.state
        events: list[str] = []
        status = str(operator_override_status or "none")

        if status in {"verifying", "applied"}:
            self._verify_start_frame = int(frame_index)
            self._last_click_to_lock_frames = None
            self.state = OperatorWorkflowState.VERIFYING
            events.append("OPERATOR_HINT")
        else:
            self.state = self._derive_state(
                active=active,
                visible_count=visible_count,
                lock_score=float(lock_score),
                display_confidence=float(display_confidence),
                low_level_mode=str(low_level_mode),
            )

        if self.state == OperatorWorkflowState.TRACKING and previous == OperatorWorkflowState.VERIFYING:
            if self._verify_start_frame is not None:
                self._last_click_to_lock_frames = max(0, int(frame_index) - int(self._verify_start_frame))
            events.append("LOCK_CONFIRMED")
            self._verify_start_frame = None
        elif self.state == OperatorWorkflowState.LOST and previous in {
            OperatorWorkflowState.VERIFYING,
            OperatorWorkflowState.TRACKING,
            OperatorWorkflowState.WEAK_TRACK,
        }:
            events.append("TARGET_LOST")
            self._verify_start_frame = None
        elif self.state != previous and not events:
            events.append(f"{previous.value}_TO_{self.state.value}")

        verify_age = 0
        if self.state == OperatorWorkflowState.VERIFYING and self._verify_start_frame is not None:
            verify_age = max(0, int(frame_index) - int(self._verify_start_frame))

        return OperatorWorkflowResult(
            state=self.state,
            events=events,
            click_to_lock_frames=self._last_click_to_lock_frames,
            verify_age_frames=verify_age,
        )

    def _derive_state(
        self,
        *,
        active: TrackedTarget | None,
        visible_count: int,
        lock_score: float,
        display_confidence: float,
        low_level_mode: str,
    ) -> OperatorWorkflowState:
        if active is None:
            return OperatorWorkflowState.CANDIDATE if visible_count > 0 else OperatorWorkflowState.SEARCH

        if low_level_mode == "LOST" or int(active.lost_frames) > int(self._cfg.TRACK_STATE_LOST_FRAMES):
            return OperatorWorkflowState.LOST

        confirm_frames = max(1, int(self._cfg.LOCK_CONFIRM_FRAMES))
        is_confirmed = int(active.hit_streak) >= confirm_frames
        is_stable = lock_score >= 0.35 or display_confidence >= 0.35

        if not is_confirmed:
            if self.state == OperatorWorkflowState.VERIFYING:
                return OperatorWorkflowState.VERIFYING
            return OperatorWorkflowState.CANDIDATE
        if is_stable:
            return OperatorWorkflowState.TRACKING
        return OperatorWorkflowState.WEAK_TRACK
