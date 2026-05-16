"""TASK-103b — Unit tests for BboxStabilizer."""
from __future__ import annotations

import pytest

from uav_tracker.tracking.bbox_stability import BboxStabilizer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _area(bbox):
    x1, y1, x2, y2 = bbox
    return (x2 - x1) * (y2 - y1)


def _center(bbox):
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_none_passthrough():
    stab = BboxStabilizer()
    assert stab.update(None) is None


def test_first_frame_returns_raw():
    stab = BboxStabilizer()
    bbox = (10, 10, 30, 30)
    assert stab.update(bbox) == bbox


def test_center_preserved():
    """Stabilizer must keep center at same position as raw bbox."""
    stab = BboxStabilizer()
    stab.update((0, 0, 40, 40))  # seed
    raw = (20, 20, 60, 60)        # sudden jump in position, same size → center shifts
    out = stab.update(raw, conf=1.0)
    # center of output should match center of raw bbox
    assert _center(out) == pytest.approx(_center(raw), abs=1.5)


def test_rate_limit_caps_size_growth():
    """Single frame cannot grow size by more than max_rate."""
    stab = BboxStabilizer(max_rate=0.08)
    stab.update((0, 0, 100, 100))  # seed: 100×100
    # double size in one frame — should be capped
    out = stab.update((0, 0, 200, 200), conf=1.0)
    w = out[2] - out[0]
    h = out[3] - out[1]
    assert w <= 100 * 1.08 + 2     # +2 for int rounding
    assert h <= 100 * 1.08 + 2


def test_rate_limit_caps_size_shrink():
    """Single frame cannot shrink size by more than max_rate."""
    stab = BboxStabilizer(max_rate=0.08)
    stab.update((0, 0, 100, 100))  # seed
    out = stab.update((0, 0, 10, 10), conf=1.0)
    w = out[2] - out[0]
    h = out[3] - out[1]
    assert w >= 100 * 0.92 - 2
    assert h >= 100 * 0.92 - 2


def test_conf_braking_prevents_growth():
    """Low confidence → bbox cannot grow beyond current EMA."""
    stab = BboxStabilizer(max_rate=0.10, conf_threshold=0.4)
    stab.update((0, 0, 100, 100))  # seed
    out = stab.update((0, 0, 200, 200), conf=0.2)  # large but low conf
    w = out[2] - out[0]
    h = out[3] - out[1]
    # size should not exceed seed (no growth allowed at low conf)
    assert w <= 100 + 2
    assert h <= 100 + 2


def test_conf_braking_allows_shrink():
    """Low confidence should still allow shrink when within the area-ratio gate."""
    stab = BboxStabilizer(max_rate=0.10, conf_threshold=0.4, area_ratio_min=0.4)
    stab.update((0, 0, 100, 100))  # seed: area=10000
    # 70×70 = 4900, ratio=0.49 → within gate [0.4, 2.5]; conf=0.1 allows shrink
    out = stab.update((0, 0, 70, 70), conf=0.1)
    w = out[2] - out[0]
    h = out[3] - out[1]
    # EMA should have moved down from 100 (shrink allowed at low conf)
    assert w < 100


def test_area_ratio_gate_clamps_large_jump():
    """Raw bbox with area >2.5× EMA should be clamped to EMA size."""
    stab = BboxStabilizer(area_ratio_min=0.4, area_ratio_max=2.5)
    stab.update((0, 0, 100, 100))   # seed: area=10000
    # area 200×200 = 40000 → ratio=4.0 → gate rejects
    out = stab.update((0, 0, 200, 200), conf=1.0)
    area_out = _area(out)
    # output area should be close to EMA (not 40000)
    assert area_out < 15000


def test_area_ratio_gate_clamps_tiny_jump():
    """Raw bbox with area <0.4× EMA should be clamped."""
    stab = BboxStabilizer(area_ratio_min=0.4, area_ratio_max=2.5)
    stab.update((0, 0, 100, 100))   # seed: area=10000
    # area 10×10 = 100 → ratio=0.01 → gate rejects
    out = stab.update((0, 0, 10, 10), conf=1.0)
    area_out = _area(out)
    assert area_out > 1000


def test_reset_reseeds_on_next_frame():
    """After reset, the next update should return the raw bbox unchanged."""
    stab = BboxStabilizer()
    stab.update((0, 0, 100, 100))  # seed
    stab.reset()
    bbox = (20, 20, 80, 80)
    assert stab.update(bbox) == bbox


def test_convergence_over_many_frames():
    """EMA should converge to target size after enough frames."""
    stab = BboxStabilizer(max_rate=0.08)
    stab.update((0, 0, 100, 100))  # seed
    target = (0, 0, 140, 140)
    out = None
    for _ in range(100):
        out = stab.update(target, conf=1.0)
    # after 100 frames at 8%/frame the EMA should be close to 140
    w = out[2] - out[0]
    assert abs(w - 140) < 5


def test_cv_reduced_after_stabilization():
    """Stabilizer should reduce coefficient of variation of bbox areas."""
    import numpy as np
    stab = BboxStabilizer(max_rate=0.08)
    # Simulate alternating large/small raw detections
    sizes = [100, 180, 90, 200, 85, 190, 95]
    raw_areas = [s * s for s in sizes]
    stable_areas = []
    for s in sizes:
        out = stab.update((0, 0, s, s), conf=0.9)
        if out is not None:
            stable_areas.append(_area(out))

    raw_cv = np.std(raw_areas) / np.mean(raw_areas)
    stable_cv = np.std(stable_areas) / np.mean(stable_areas)
    assert stable_cv < raw_cv, f"Stabilizer should reduce CV ({raw_cv:.3f} → {stable_cv:.3f})"
