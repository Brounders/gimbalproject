"""Operator seed bbox refinement tests."""
from __future__ import annotations

import numpy as np

from uav_tracker.tracking.operator_seed import refine_operator_seed_bbox


class TestOperatorSeedRefinement:
    def test_refines_large_seed_to_visible_contrast_object(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[42:54, 58:72] = 255

        result = refine_operator_seed_bbox(frame, (40, 30, 90, 80), padding=2)

        assert result is not None
        x1, y1, x2, y2 = result
        assert 55 <= x1 <= 58
        assert 40 <= y1 <= 42
        assert 72 <= x2 <= 75
        assert 54 <= y2 <= 57

    def test_returns_original_when_no_contrast_object_is_found(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        result = refine_operator_seed_bbox(frame, (10, 10, 40, 40), padding=2)

        assert result == (10, 10, 40, 40)
