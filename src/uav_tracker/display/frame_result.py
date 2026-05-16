"""
uav_tracker/frame_result.py — FrameOutput dataclass.

Single frame result produced by TrackerPipeline.process_frame().
Extracted from pipeline.py (TASK-20260312-052).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class FrameOutput:
    frame: Optional[np.ndarray]
    fps: float
    active_id: Optional[int]
    active_source: str
    active_bbox: Optional[tuple[int, int, int, int]]
    target_count: int
    visible_target_count: int
    mode: str
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
    timings_ms: dict[str, float]
    # ALG-001 v1: detection-first telemetry (default-safe, telemetry only).
    target_reliability: float = 0.0
    target_p_present: float = 0.0
    tracking_action: str = 'global_rescan'
    # ALG-001 v1.1: guarded behavior wiring (default-safe, off-path).
    target_modality: str = 'rgb'
    decision_path: str = 'telemetry_only'
    behavior_drop_count: int = 0
    # Operator target override backend (default-safe until UI is wired).
    operator_override_status: str = 'none'
    operator_override_count: int = 0
    operator_override_bbox: Optional[tuple[int, int, int, int]] = None
    operator_workflow_state: str = ''
    operator_workflow_events: list[str] = field(default_factory=list)
    operator_click_to_lock_frames: Optional[int] = None
    operator_verify_age_frames: int = 0
    # TASK-103a Diagnostic Pack v1 (read-only telemetry).
    scene_label_runtime: str = ''
    scene_confidence_runtime: float = 1.0
    proposal_count_by_source: dict[str, int] = field(default_factory=dict)
    bbox_area: int = 0
    # TASK-103b: raw (pre-stabilization) bbox for recall computation.
    # active_bbox carries the display-smoothed version; this carries the
    # tracker's raw_bbox so diagnostics can compute IoU against GT correctly.
    active_bbox_raw: Optional[tuple[int, int, int, int]] = None
