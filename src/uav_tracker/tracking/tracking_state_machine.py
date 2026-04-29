"""uav_tracker/tracking_state_machine.py — SCAN/TRACK/LOST state machine.

Extracted from TrackerPipeline (A08 Stage 2).
Maintains target-presence streaks and emits stable tracking states,
plus a display-smoothed state that suppresses momentary downgrade flicker.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from uav_tracker.config import Config


class TrackingState(str, Enum):
    """Pipeline tracking state.  Inherits str so existing string comparisons work:
    ``TrackingState.TRACK == 'TRACK'`` is True.
    """
    SCAN = 'SCAN'
    TRACK = 'TRACK'
    LOST = 'LOST'


_STATE_ORDER = {TrackingState.SCAN: 0, TrackingState.LOST: 1, TrackingState.TRACK: 2}


class TrackingStateMachine:
    """Tracks SCAN / TRACK / LOST pipeline state across frames.

    Call update() once per frame with the active target's lost_frames count
    (or None if no active target).  Query state and display_state at any time.
    """

    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self.state: TrackingState = TrackingState.SCAN
        self._present_streak: int = 0
        self._missing_streak: int = 0
        self._had_target: bool = False
        self._display_state: TrackingState = TrackingState.SCAN
        self._display_state_hold: int = 0

    def update(self, lost_frames: Optional[int]) -> TrackingState:
        """Register one frame.  Returns the updated logical state.

        Args:
            lost_frames: active target's lost_frames counter, or None if no
                         active target.  A target is considered *present* when
                         lost_frames <= LOCK_LOST_GRACE.
        Returns:
            Current logical state string ('SCAN', 'TRACK', or 'LOST').
        """
        present = (
            lost_frames is not None
            and int(lost_frames) <= int(self._cfg.LOCK_LOST_GRACE)
        )
        acquire_frames = max(1, int(self._cfg.TRACK_STATE_ACQUIRE_FRAMES))
        lost_threshold = max(1, int(self._cfg.TRACK_STATE_LOST_FRAMES))
        reset_frames = max(lost_threshold + 1, int(self._cfg.TRACK_STATE_RESET_FRAMES))

        if present:
            self._present_streak += 1
            self._missing_streak = 0
            self._had_target = True
            if self.state != TrackingState.TRACK and self._present_streak >= acquire_frames:
                self.state = TrackingState.TRACK
        else:
            self._present_streak = 0
            self._missing_streak += 1
            if self.state == TrackingState.TRACK and self._missing_streak >= lost_threshold:
                self.state = TrackingState.LOST
            elif self.state == TrackingState.LOST and self._missing_streak >= reset_frames:
                self.state = TrackingState.SCAN
                self._had_target = False
            elif not self._had_target:
                self.state = TrackingState.SCAN

        if self.state == TrackingState.LOST and present and self._present_streak >= acquire_frames:
            self.state = TrackingState.TRACK

        return self.state

    @property
    def display_state(self) -> TrackingState:
        """Display-smoothed state.

        Upgrades (SCAN→TRACK) apply immediately.
        Downgrades are held for DISPLAY_STATE_HOLD_FRAMES frames to suppress
        visual flicker without affecting quality-gate metrics.
        """
        return self._display_state

    def update_display(self) -> TrackingState:
        """Sync display_state to current logical state.  Returns display_state."""
        hold = max(1, int(getattr(self._cfg, 'DISPLAY_STATE_HOLD_FRAMES', 3)))
        real_level = _STATE_ORDER.get(self.state, 0)
        disp_level = _STATE_ORDER.get(self._display_state, 0)
        if real_level >= disp_level:
            self._display_state = self.state
            self._display_state_hold = 0
        else:
            self._display_state_hold += 1
            if self._display_state_hold >= hold:
                self._display_state = self.state
                self._display_state_hold = 0
        return self._display_state
