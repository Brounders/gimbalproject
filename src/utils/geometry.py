"""Утилиты геометрии для работы с bounding box."""

from __future__ import annotations


def iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    """Вычислить IoU (Intersection over Union) двух bounding box в формате xyxy.

    Args:
        a: Первый bbox (x1, y1, x2, y2).
        b: Второй bbox (x1, y1, x2, y2).

    Returns:
        Значение IoU в диапазоне [0.0, 1.0].
    """
    xi1, yi1 = max(a[0], b[0]), max(a[1], b[1])
    xi2, yi2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    if inter <= 0:
        return 0.0
    union_area = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union_area if union_area > 0 else 0.0
