"""uav_tracker/continuity_tracker.py — Continuity and presence metrics.

Extracted from TrackerPipeline (A08 Stage 1).
Tracks active-target ID stability across frames to produce quality metrics.
"""
from __future__ import annotations

from typing import Optional

import numpy as np


class ContinuityTracker:
    """Accumulates per-frame active-target ID transitions for quality metrics.

    Call update() once per frame with the current active_id.
    Query score(), presence_rate(), median_reacquire_frames(), and id_changes
    at any time for the current accumulated values.
    """

    def __init__(self) -> None:
        self._prev_active_id: Optional[int] = None
        self._transitions: int = 0
        self._same_id_transitions: int = 0
        self._id_changes: int = 0
        self._active_frames: int = 0
        self._lost_run: int = 0
        self._reacquire_gaps: list[int] = []

    @property
    def id_changes(self) -> int:
        return self._id_changes

    def update(self, active_id: Optional[int]) -> None:
        """Register one frame with the given active target ID (or None if lost)."""
        if active_id is not None:
            self._active_frames += 1

        prev = self._prev_active_id
        if prev is not None and active_id is not None:
            self._transitions += 1
            if prev == active_id:
                self._same_id_transitions += 1
            else:
                self._id_changes += 1

        if active_id is None:
            self._lost_run += 1
        else:
            if self._lost_run > 0:
                self._reacquire_gaps.append(self._lost_run)
                self._lost_run = 0

        self._prev_active_id = active_id

    def score(self) -> float:
        """Fraction of consecutive-frame transitions with same active ID."""
        if self._transitions <= 0:
            return 1.0 if self._active_frames > 0 else 0.0
        return float(self._same_id_transitions) / float(self._transitions)

    def presence_rate(self, frame_counter: int) -> float:
        """Fraction of total frames where an active target was present."""
        if frame_counter <= 0:
            return 0.0
        return float(self._active_frames) / float(frame_counter)

    def median_reacquire_frames(self) -> float:
        """Median number of lost frames between consecutive active appearances."""
        if not self._reacquire_gaps:
            return 0.0
        return float(np.median(self._reacquire_gaps))
