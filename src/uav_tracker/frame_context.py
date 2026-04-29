"""FrameContext — immutable per-frame metadata passed through the pipeline.

Replaces ad-hoc positional arguments and allows pipeline stages to read
frame-level state (mode, budget, index) without touching shared mutable config.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameContext:
    """Immutable snapshot of per-frame runtime metadata.

    Attributes:
        frame_id:    Monotonically increasing frame counter (0-based).
        timestamp:   Wall-clock time at frame start (seconds, perf_counter).
        scene_mode:  Active scene mode string: 'day' | 'night' | 'ir' | 'auto'.
        budget_ok:   True when BudgetController allows full processing this frame.
    """

    frame_id: int
    timestamp: float
    scene_mode: str
    budget_ok: bool
