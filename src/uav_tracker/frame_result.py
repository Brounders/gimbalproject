from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class FrameOutput:
    frame: Optional[np.ndarray]
    fps: float
    active_id: Optional[int]
    active_source: str
    active_bbox: Optional[tuple[int, int, int, int]]
    active_cycle_index: int
    active_cycle_total: int
    target_count: int
    visible_target_count: int
    mode: str
    lock_confirmed: bool
    frame_index: int
    scan_strategy: str
    gt_visible: bool
    gt_iou: float
    lock_score: float
    display_confidence: float
    continuity_score: float
    active_presence_rate: float
    active_id_changes: int
    median_reacquire_frames: float
    lock_events: list[str]
    lock_switch_count: int
    lock_switches_per_min: float
    lock_event_counts: dict[str, int]
    budget_level: int
    budget_load: float
    budget_frame_ms: float
    roi_budget_candidates: int
    night_skip: int
    ir_noise_level: float
    ir_noise_gate_active: bool
    lock_confirm_frames_effective: int
    timings_ms: dict[str, float]
