"""TASK-117 — Unit tests for NightSmallTargetDetector safety contracts."""
from __future__ import annotations

import numpy as np

from uav_tracker.config import Config
from uav_tracker.detectors.night_detector import NightSmallTargetDetector


def _cfg(**overrides) -> Config:
    base = dict(
        NIGHT_MOG2_HISTORY=3,
        NIGHT_MOG2_VAR_THRESH=8,
        NIGHT_BLUR_KERNEL=3,
        NIGHT_MORPH_KERNEL=3,
        NIGHT_GRID_CELL=16,
        NIGHT_MIN_AREA=1,
        NIGHT_MAX_AREA=400,
        NIGHT_MOT_THRESH=1,
        NIGHT_DIFF_THRESH=1,
        NIGHT_HIST_LEN=1,
        NIGHT_CONFIRM=1,
        NIGHT_BORDER=4,
        NIGHT_MAX_AR=4.0,
        NIGHT_TRACK_DIST=24,
        NIGHT_CONTOUR_ENABLED=False,
        NIGHT_HOTSPOT_ENABLED=False,
        NIGHT_PEAK_ENABLED=True,
        NIGHT_PEAK_THRESH=8,
        NIGHT_PEAK_BOX=10,
        NIGHT_PEAK_NMS_DIST=8,
        NIGHT_PEAK_TOP_K=5,
        NIGHT_PEAK_REQUIRE_MOTION=False,
        NIGHT_STICKY_ENABLED=False,
    )
    base.update(overrides)
    return Config(**base)


def _frame(width: int = 96, height: int = 72, dot: tuple[int, int] | None = None) -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    if dot is not None:
        cx, cy = dot
        frame[max(0, cy - 2): cy + 3, max(0, cx - 2): cx + 3] = 255
    return frame


def test_warmup_returns_no_detections_before_history_len():
    det = NightSmallTargetDetector(_cfg(NIGHT_HIST_LEN=3))

    assert det.detect(_frame()) == []
    assert det.detect(_frame(dot=(40, 30))) == []
    assert det.detect(_frame(dot=(42, 31))) == []


def test_peak_path_detects_small_bright_target_after_confirm():
    det = NightSmallTargetDetector(_cfg(NIGHT_CONFIRM=1))

    det.detect(_frame(dot=(40, 30)))
    out = det.detect(_frame(dot=(43, 32)))

    assert out
    best = out[0]
    assert best["source"] == "night"
    x1, y1, x2, y2 = best["bbox"]
    assert x1 <= 43 <= x2
    assert y1 <= 32 <= y2


def test_border_rejection_blocks_edge_targets():
    det = NightSmallTargetDetector(_cfg(NIGHT_BORDER=12))

    det.detect(_frame(dot=(5, 5)))
    assert det.detect(_frame(dot=(6, 6))) == []


def test_area_filter_rejects_peak_box_outside_allowed_range():
    det = NightSmallTargetDetector(_cfg(NIGHT_MIN_AREA=200, NIGHT_PEAK_BOX=10))

    det.detect(_frame(dot=(40, 30)))
    assert det.detect(_frame(dot=(42, 32))) == []


def test_candidate_key_collision_uses_distinct_sub_ids_in_same_grid_cell():
    det = NightSmallTargetDetector(_cfg(NIGHT_GRID_CELL=32, NIGHT_TRACK_DIST=4))
    used: set[tuple] = set()

    first = det._find_candidate_key(20, 20, used)
    assert first is not None
    used.add(first)
    det._candidates[first] = {"count": 1, "cx": 20, "cy": 20, "speed": 0.0}

    second = det._find_candidate_key(24, 20, used)

    assert second is not None
    assert second != first
    assert second[:2] == first[:2]


def test_sticky_selection_keeps_active_target_over_higher_score_jump():
    det = NightSmallTargetDetector(
        _cfg(NIGHT_STICKY_ENABLED=True, NIGHT_MAX_DETECTIONS=1, NIGHT_STICKY_RADIUS=50)
    )
    active_key = (1, 1, 0)
    jump_key = (5, 5, 0)
    det._active_key = active_key
    det._candidates[active_key] = {"count": 3, "cx": 30, "cy": 30, "speed": 0.0}
    det._candidates[jump_key] = {"count": 3, "cx": 80, "cy": 40, "speed": 0.0}
    detections = [
        {"_key": jump_key, "score": 100.0, "cx": 80, "cy": 40},
        {"_key": active_key, "score": 5.0, "cx": 31, "cy": 31},
    ]

    selected = det._select_sticky_detections(detections)

    assert selected == [detections[1]]
    assert det._active_key == active_key


def test_peak_rows_apply_top_k_and_nms():
    det = NightSmallTargetDetector(
        _cfg(NIGHT_PEAK_TOP_K=1, NIGHT_PEAK_NMS_DIST=10, NIGHT_PEAK_BOX=8)
    )
    top_hat = np.zeros((50, 50), dtype=np.uint8)
    top_hat[20, 20] = 60
    top_hat[22, 22] = 55
    top_hat[40, 40] = 50
    motion = np.zeros_like(top_hat)

    rows = det._peak_rows(top_hat, (50, 50, 3), motion)

    assert len(rows) == 1
    score, area, x, y, w, h = rows[0]
    assert score == 60.0
    assert area == 64.0
    assert (x, y, w, h) == (16, 16, 8, 8)
