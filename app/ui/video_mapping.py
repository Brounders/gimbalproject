from __future__ import annotations

from typing import Optional


def map_widget_point_to_frame(
    *,
    widget_size: tuple[int, int],
    frame_size: tuple[int, int],
    point: tuple[int, int],
) -> Optional[tuple[int, int]]:
    """Map QLabel/widget coordinates to original frame coordinates.

    The video preview is rendered with Qt.KeepAspectRatio.  That means the
    displayed frame can be letterboxed horizontally or vertically; clicks in
    those margins must not select a target.
    """
    widget_w, widget_h = [int(v) for v in widget_size]
    frame_w, frame_h = [int(v) for v in frame_size]
    px, py = [int(v) for v in point]

    if widget_w <= 0 or widget_h <= 0 or frame_w <= 0 or frame_h <= 0:
        return None

    scale = min(widget_w / float(frame_w), widget_h / float(frame_h))
    scaled_w = int(round(frame_w * scale))
    scaled_h = int(round(frame_h * scale))
    if scaled_w <= 0 or scaled_h <= 0:
        return None

    x0 = (widget_w - scaled_w) // 2
    y0 = (widget_h - scaled_h) // 2
    x1 = x0 + scaled_w
    y1 = y0 + scaled_h
    if px < x0 or px >= x1 or py < y0 or py >= y1:
        return None

    fx = int((px - x0) / scale)
    fy = int((py - y0) / scale)
    return min(frame_w - 1, max(0, fx)), min(frame_h - 1, max(0, fy))
