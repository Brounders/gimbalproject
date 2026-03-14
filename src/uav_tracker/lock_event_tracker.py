"""uav_tracker/lock_event_tracker.py — Lock acquisition telemetry.

Extracted from TrackerPipeline (A08 Stage 5).
Detects ACQUIRE / REACQUIRE / LOST / SWITCH lock events from per-frame
focus-mode transitions and accumulates telemetry counters.
"""
from __future__ import annotations

from typing import Optional


class LockEventTracker:
    """Accumulates lock-event telemetry from per-frame focus-mode transitions.

    Call update() once per frame with the current focus_mode flag and active_id.
    Query event_counts, switch_count, and switches_per_min() at any time.
    """

    def __init__(self) -> None:
        self.switch_count: int = 0
        self.event_counts: dict[str, int] = {
            'acquired': 0, 'lost': 0, 'reacquired': 0, 'switch': 0,
        }
        self._had_lock_before: bool = False
        self._prev_focus_mode: bool = False
        self._prev_active_id: Optional[int] = None

    def update(self, focus_mode: bool, active_id: Optional[int]) -> list[str]:
        """Detect lock events from one frame's focus/id state.

        Args:
            focus_mode: True when manager is in focus/lock mode.
            active_id: current active target ID, or None.

        Returns:
            List of string event tags for this frame (may be empty).
        """
        events: list[str] = []

        if not self._prev_focus_mode and focus_mode:
            if self._had_lock_before:
                self.event_counts['reacquired'] += 1
                events.append(f'LOCK_REACQUIRED id={active_id}')
            else:
                self._had_lock_before = True
                self.event_counts['acquired'] += 1
                events.append(f'LOCK_ACQUIRED id={active_id}')

        if self._prev_focus_mode and not focus_mode:
            self.event_counts['lost'] += 1
            events.append(f'LOCK_LOST id={self._prev_active_id}')

        if (
            self._prev_focus_mode
            and focus_mode
            and self._prev_active_id is not None
            and active_id is not None
            and self._prev_active_id != active_id
        ):
            self.switch_count += 1
            self.event_counts['switch'] += 1
            events.append(f'LOCK_SWITCH {self._prev_active_id}->{active_id}')

        self._prev_focus_mode = focus_mode
        self._prev_active_id = active_id
        return events

    def switches_per_min(self, elapsed_sec: float) -> float:
        """Lock switches per minute; returns 0.0 until 5 s have elapsed."""
        if elapsed_sec < 5.0:
            return 0.0
        return self.switch_count * 60.0 / elapsed_sec
