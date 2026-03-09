from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Callable, Optional, Union

from uav_tracker.config import Config
from uav_tracker.pipeline import VideoSession, TrackerPipeline


@dataclass
class EvaluationReport:
    source: str
    runtime_mode: str
    total_frames: int
    gt_frames: int
    active_frames: int
    lock_frames: int
    visible_target_frames: int
    false_alarm_frames: int
    false_lock_frames: int
    false_lock_rate: float
    unverified_active_frames: int
    unverified_active_rate: float
    hits_iou_01: int
    hits_iou_03: int
    hits_iou_05: int
    avg_gt_iou: float
    avg_fps: float
    avg_lock_score: float
    continuity_score: float
    active_presence_rate: float
    active_id_changes: int
    active_id_changes_per_min: float
    median_reacquire_frames: float
    lock_switches: int
    lock_switches_per_min: float
    lock_event_counts: dict[str, int]
    mode_counts: dict[str, int]
    avg_budget_level: float
    avg_budget_load: float
    avg_budget_frame_ms: float
    elapsed_video_sec: float
    time_to_first_active: Optional[int]
    time_to_first_lock: Optional[int]
    longest_lock_streak: int
    scan_strategy_counts: dict[str, int]
    avg_stage_ms: dict[str, float]

    def to_dict(self) -> dict:
        data = asdict(self)
        # Contract aliases for downstream quality-gate tools.
        data["continuity"] = self.continuity_score
        data["active_presence"] = self.active_presence_rate
        data["id_changes"] = self.active_id_changes
        data["unverified_active"] = self.unverified_active_rate
        return data


class Evaluator:
    def __init__(self, cfg: Config, source: Union[str, int], *, small_target_mode: bool = False):
        self.cfg = cfg
        self.source = source
        self.small_target_mode = small_target_mode

    def run(
        self,
        max_frames: int = 0,
        report_path: str = '',
        stop_checker: Optional[Callable[[], bool]] = None,
    ) -> EvaluationReport:
        session = VideoSession(self.cfg, self.source, manage_cv_windows=False)
        session.open()
        pipeline = TrackerPipeline(self.cfg)

        total_frames = 0
        gt_frames = 0
        active_frames = 0
        lock_frames = 0
        visible_target_frames = 0
        false_alarm_frames = 0
        false_lock_frames = 0
        unverified_active_frames = 0
        hits_iou_01 = 0
        hits_iou_03 = 0
        hits_iou_05 = 0
        time_to_first_active = None
        time_to_first_lock = None
        longest_lock_streak = 0
        current_lock_streak = 0
        fps_values: list[float] = []
        lock_scores: list[float] = []
        continuity_score = 0.0
        active_presence_rate = 0.0
        active_id_changes = 0
        median_reacquire_frames = 0.0
        lock_switches = 0
        lock_switches_per_min = 0.0
        lock_event_counts: Counter[str] = Counter()
        mode_counts: Counter[str] = Counter()
        budget_levels: list[float] = []
        budget_loads: list[float] = []
        budget_frame_ms: list[float] = []
        gt_ious: list[float] = []
        stage_samples: dict[str, list[float]] = {'global': [], 'lock': [], 'local': [], 'roi': [], 'night': [], 'draw': []}
        scan_strategy_counts: Counter[str] = Counter()
        elapsed_video_sec = 0.0

        try:
            while True:
                ret, frame, meta = session.read()
                if not ret:
                    break
                total_frames += 1
                result = pipeline.process_frame(
                    frame,
                    frame_index=int(meta.get('frame_index', total_frames - 1)),
                    gt_bbox=meta.get('gt_bbox'),
                    small_target_mode=self.small_target_mode,
                    render=False,
                    source_fps=meta.get('source_fps'),
                )
                fps_values.append(result.fps)
                source_fps = float(meta.get('source_fps') or 0.0)
                if source_fps > 1.0:
                    elapsed_video_sec += 1.0 / source_fps
                else:
                    elapsed_video_sec += 1.0 / max(1.0, float(result.fps))
                lock_scores.append(result.lock_score)
                continuity_score = float(result.continuity_score)
                active_presence_rate = float(result.active_presence_rate)
                active_id_changes = int(result.active_id_changes)
                median_reacquire_frames = float(result.median_reacquire_frames)
                lock_switches = result.lock_switch_count
                lock_switches_per_min = result.lock_switches_per_min
                for key, value in result.lock_event_counts.items():
                    lock_event_counts[key] = max(lock_event_counts[key], int(value))
                mode_counts[str(result.mode).upper()] += 1
                budget_levels.append(float(result.budget_level))
                budget_loads.append(float(result.budget_load))
                budget_frame_ms.append(float(result.budget_frame_ms))
                scan_strategy_counts[result.scan_strategy] += 1
                for key in stage_samples:
                    stage_samples[key].append(result.timings_ms.get(key, 0.0))

                gt_visible = bool(meta.get('gt_bbox'))
                if gt_visible:
                    gt_frames += 1
                    gt_ious.append(result.gt_iou)
                    if result.gt_iou >= 0.10:
                        hits_iou_01 += 1
                    if result.gt_iou >= 0.30:
                        hits_iou_03 += 1
                    if result.gt_iou >= 0.50:
                        hits_iou_05 += 1
                elif result.visible_target_count > 0:
                    false_alarm_frames += 1

                if result.visible_target_count > 0:
                    visible_target_frames += 1
                if result.active_id is not None:
                    active_frames += 1
                    if time_to_first_active is None:
                        time_to_first_active = total_frames
                    if gt_visible and result.gt_iou < 0.10:
                        false_lock_frames += 1
                    elif not gt_visible:
                        unverified_active_frames += 1
                if result.mode in {'TRACK', 'LOCK-FOCUS'}:
                    lock_frames += 1
                    current_lock_streak += 1
                    if time_to_first_lock is None:
                        time_to_first_lock = total_frames
                else:
                    longest_lock_streak = max(longest_lock_streak, current_lock_streak)
                    current_lock_streak = 0

                if max_frames > 0 and total_frames >= max_frames:
                    break
                if stop_checker is not None and stop_checker():
                    break
        finally:
            session.close()

        longest_lock_streak = max(longest_lock_streak, current_lock_streak)
        total_frames_safe = max(1, total_frames)
        non_gt_frames = max(0, total_frames - gt_frames)
        false_lock_rate = float(false_lock_frames) / float(max(1, gt_frames)) if gt_frames > 0 else 0.0
        unverified_active_rate = float(unverified_active_frames) / float(max(1, non_gt_frames)) if non_gt_frames > 0 else 0.0
        if elapsed_video_sec < 5.0:
            active_id_changes_per_min = 0.0
        else:
            active_id_changes_per_min = float(active_id_changes) * 60.0 / float(elapsed_video_sec)
        avg_stage_ms = {key: (mean(values) if values else 0.0) for key, values in stage_samples.items()}
        report = EvaluationReport(
            source=str(self.source),
            runtime_mode=self.cfg.RUNTIME_MODE,
            total_frames=total_frames,
            gt_frames=gt_frames,
            active_frames=active_frames,
            lock_frames=lock_frames,
            visible_target_frames=visible_target_frames,
            false_alarm_frames=false_alarm_frames,
            false_lock_frames=false_lock_frames,
            false_lock_rate=false_lock_rate,
            unverified_active_frames=unverified_active_frames,
            unverified_active_rate=unverified_active_rate,
            hits_iou_01=hits_iou_01,
            hits_iou_03=hits_iou_03,
            hits_iou_05=hits_iou_05,
            avg_gt_iou=mean(gt_ious) if gt_ious else 0.0,
            avg_fps=mean(fps_values) if fps_values else 0.0,
            avg_lock_score=mean(lock_scores) if lock_scores else 0.0,
            continuity_score=continuity_score,
            active_presence_rate=active_presence_rate,
            active_id_changes=active_id_changes,
            active_id_changes_per_min=active_id_changes_per_min,
            median_reacquire_frames=median_reacquire_frames,
            lock_switches=lock_switches,
            lock_switches_per_min=lock_switches_per_min,
            lock_event_counts=dict(lock_event_counts),
            mode_counts=dict(mode_counts),
            avg_budget_level=mean(budget_levels) if budget_levels else 0.0,
            avg_budget_load=mean(budget_loads) if budget_loads else 0.0,
            avg_budget_frame_ms=mean(budget_frame_ms) if budget_frame_ms else 0.0,
            elapsed_video_sec=elapsed_video_sec,
            time_to_first_active=time_to_first_active,
            time_to_first_lock=time_to_first_lock,
            longest_lock_streak=longest_lock_streak,
            scan_strategy_counts=dict(scan_strategy_counts),
            avg_stage_ms=avg_stage_ms,
        )
        if report_path:
            out = Path(report_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        return report


def evaluate_source(
    cfg: Config,
    source: Union[str, int],
    *,
    small_target_mode: bool = False,
    max_frames: int = 0,
    report_path: str = '',
    stop_checker: Optional[Callable[[], bool]] = None,
) -> EvaluationReport:
    evaluator = Evaluator(cfg, source, small_target_mode=small_target_mode)
    return evaluator.run(max_frames=max_frames, report_path=report_path, stop_checker=stop_checker)
