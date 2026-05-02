"""Operator target override primitives.

This is the backend contract for future UI clicks/drag boxes.  The command is
pure data: UI code converts screen input to frame coordinates, then pipeline
applies it on the next frame when frame bounds are known.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


def _clip(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


@dataclass(frozen=True)
class OperatorTargetOverride:
    kind: str
    point: Optional[tuple[int, int]] = None
    bbox: Optional[tuple[int, int, int, int]] = None
    box_size: int = 64
    frame_index: Optional[int] = None
    reason: str = 'operator'

    @classmethod
    def from_click(
        cls,
        x: int,
        y: int,
        *,
        box_size: int = 64,
        frame_index: Optional[int] = None,
        reason: str = 'operator_click',
    ) -> 'OperatorTargetOverride':
        return cls(
            kind='click',
            point=(int(x), int(y)),
            box_size=max(2, int(box_size)),
            frame_index=frame_index,
            reason=reason,
        )

    @classmethod
    def from_bbox(
        cls,
        bbox: tuple[int, int, int, int],
        *,
        frame_index: Optional[int] = None,
        reason: str = 'operator_bbox',
    ) -> 'OperatorTargetOverride':
        x1, y1, x2, y2 = [int(v) for v in bbox]
        return cls(kind='bbox', bbox=(x1, y1, x2, y2), frame_index=frame_index, reason=reason)

    def to_bbox(self, frame_shape: tuple[int, ...]) -> Optional[tuple[int, int, int, int]]:
        """Return a clipped xyxy bbox in frame coordinates, or None if invalid."""
        if len(frame_shape) < 2:
            return None
        height, width = int(frame_shape[0]), int(frame_shape[1])
        if width <= 0 or height <= 0:
            return None

        if self.kind == 'bbox' and self.bbox is not None:
            x1, y1, x2, y2 = self.bbox
        elif self.kind == 'click' and self.point is not None:
            cx, cy = self.point
            half = max(1, int(self.box_size) // 2)
            x1, y1, x2, y2 = cx - half, cy - half, cx + half, cy + half
        else:
            return None

        x1 = _clip(x1, 0, width)
        x2 = _clip(x2, 0, width)
        y1 = _clip(y1, 0, height)
        y2 = _clip(y2, 0, height)
        if x2 <= x1 or y2 <= y1:
            return None
        return x1, y1, x2, y2


@dataclass(frozen=True)
class OperatorOverrideResult:
    applied: bool
    status: str
    active_id: Optional[int] = None
    bbox: Optional[tuple[int, int, int, int]] = None
