from __future__ import annotations

import cv2
import numpy as np


def _clip_bbox(
    bbox: tuple[int, int, int, int],
    shape: tuple[int, int],
) -> tuple[int, int, int, int] | None:
    h, w = shape
    x1, y1, x2, y2 = [int(v) for v in bbox]
    x1 = max(0, min(w - 1, x1))
    y1 = max(0, min(h - 1, y1))
    x2 = max(0, min(w, x2))
    y2 = max(0, min(h, y2))
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None
    return x1, y1, x2, y2


def refine_operator_seed_bbox(
    frame: np.ndarray,
    bbox: tuple[int, int, int, int],
    *,
    padding: int = 18,
) -> tuple[int, int, int, int] | None:
    """Tighten an operator seed around the strongest local contrast blob.

    This is intentionally conservative.  If no useful blob is found, the
    original clipped bbox is returned.
    """
    clipped = _clip_bbox(bbox, frame.shape[:2])
    if clipped is None:
        return None
    x1, y1, x2, y2 = clipped
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return clipped

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
    if float(np.std(gray)) < 4.0:
        return clipped

    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _thr, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _hier = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return clipped

    crop_area = max(1, crop.shape[0] * crop.shape[1])
    best = None
    best_score = None
    center_x = crop.shape[1] / 2.0
    center_y = crop.shape[0] / 2.0
    for contour in contours:
        bx, by, bw, bh = cv2.boundingRect(contour)
        area = bw * bh
        if area < 4 or area > crop_area * 0.85:
            continue
        cx = bx + bw / 2.0
        cy = by + bh / 2.0
        center_dist = ((cx - center_x) ** 2 + (cy - center_y) ** 2) ** 0.5
        score = (-area, center_dist)
        if best_score is None or score < best_score:
            best_score = score
            best = (bx, by, bx + bw, by + bh)
    if best is None:
        return clipped

    pad = max(0, int(padding))
    bx1, by1, bx2, by2 = best
    refined = (x1 + bx1 - pad, y1 + by1 - pad, x1 + bx2 + pad, y1 + by2 + pad)
    return _clip_bbox(refined, frame.shape[:2]) or clipped
