"""app/workers.py — Background QThread workers for tracking and evaluation.

Extracted from main_gui.py (T8a).
"""
import json
import threading
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from uav_tracker.config import Config
from uav_tracker.domain import (
    JsonlTelemetryWriter,
    frame_result_from_output,
    operator_hint_from_override,
)
from uav_tracker.evaluation import evaluate_source
from uav_tracker.exceptions import InferenceDeviceError, ModelNotFoundError, SourceOpenError
from uav_tracker.pipeline import TrackerPipeline, VideoSession
from uav_tracker.tracking.operator_override import OperatorTargetOverride


def _qimage_from_bgr_frame(frame) -> QImage | None:
    if frame is None or getattr(frame, "size", 0) == 0:
        return None
    if getattr(frame, "ndim", 0) != 3 or frame.shape[2] < 3:
        return None
    height, width = frame.shape[:2]
    rgb = frame[:, :, :3][:, :, ::-1].copy()
    return QImage(rgb.data, width, height, rgb.strides[0], QImage.Format_RGB888).copy()


def _display_targets_payload(pipeline: TrackerPipeline, limit: int = 3) -> list[dict]:
    targets = []
    active_id = pipeline.manager.active_id
    for target in pipeline.manager.display_targets():
        if target is None or target.bbox is None:
            continue
        x1, y1, x2, y2 = [int(v) for v in target.bbox[:4]]
        is_active = target.track_id == active_id
        score = float(target.drone_score) * 0.45 + float(target.conf) * 0.45 + min(1.0, float(target.hit_streak) / 10.0) * 0.10
        targets.append(
            {
                'id': int(target.track_id),
                'bbox': [x1, y1, x2, y2],
                'conf': round(float(target.conf), 4),
                'score': round(score, 4),
                'source': str(target.source),
                'active': bool(is_active),
                'lost_frames': int(target.lost_frames),
            }
        )
    targets.sort(key=lambda item: (not item['active'], -float(item['score']), int(item['lost_frames'])))
    return targets[:limit]


class TrackerWorker(QThread):
    frame_ready = Signal(object)
    stats_ready = Signal(dict)
    log_ready = Signal(str)
    finished = Signal(str)  # stopped | eof
    failed = Signal(str)

    def __init__(
        self,
        cfg: Config,
        source,
        output_path: str,
        small_target_mode: bool,
        lock_log_path: str = '',
        render_overlays: bool = True,
    ):
        super().__init__()
        self.cfg = cfg
        self.source = source
        self.output_path = output_path
        self.small_target_mode = small_target_mode
        self.lock_log_path = lock_log_path.strip()
        self.render_overlays = bool(render_overlays)
        self._stop_event = threading.Event()
        self._switch_event = threading.Event()
        self._operator_lock = threading.Lock()
        self._pending_operator_override: OperatorTargetOverride | None = None
        self._operator_confirm_event = threading.Event()
        self._operator_release_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def request_switch_target(self):
        self._switch_event.set()

    def request_operator_target(self, frame_x: int, frame_y: int):
        with self._operator_lock:
            self._pending_operator_override = OperatorTargetOverride.from_click(
                int(frame_x),
                int(frame_y),
                box_size=int(getattr(self.cfg, 'OPERATOR_OVERRIDE_BOX_SIZE', 64)),
            )

    def request_operator_bbox(self, bbox: tuple[int, int, int, int]):
        with self._operator_lock:
            self._pending_operator_override = OperatorTargetOverride.from_bbox(bbox)

    def request_operator_confirm(self):
        self._operator_confirm_event.set()

    def request_operator_release(self):
        self._operator_release_event.set()

    def _pop_operator_override(self) -> OperatorTargetOverride | None:
        with self._operator_lock:
            override = self._pending_operator_override
            self._pending_operator_override = None
        return override

    def _pop_operator_confirm(self) -> bool:
        if not self._operator_confirm_event.is_set():
            return False
        self._operator_confirm_event.clear()
        return True

    def _pop_operator_release(self) -> bool:
        if not self._operator_release_event.is_set():
            return False
        self._operator_release_event.clear()
        return True

    def run(self):
        reason = 'stopped'
        session = VideoSession(self.cfg, self.source, output_path=self.output_path, manage_cv_windows=False)
        event_log_handle = None
        annotation_log_handle = None
        telemetry_writer = None
        try:
            resolved_lock_log = self.lock_log_path
            if not resolved_lock_log and self.cfg.LOCK_EVENT_LOG_ENABLED and self.cfg.LOCK_EVENT_LOG_PATH:
                resolved_lock_log = str(self.cfg.LOCK_EVENT_LOG_PATH)
            if resolved_lock_log:
                lock_log_file = Path(resolved_lock_log)
                lock_log_file.parent.mkdir(parents=True, exist_ok=True)
                event_log_handle = lock_log_file.open('a', encoding='utf-8')
                self.log_ready.emit(f'Лог lock-событий: {resolved_lock_log}')
            if self.cfg.OPERATOR_ANNOTATION_LOG_ENABLED and self.cfg.OPERATOR_ANNOTATION_LOG_PATH:
                annotation_log_file = Path(self.cfg.OPERATOR_ANNOTATION_LOG_PATH)
                annotation_log_file.parent.mkdir(parents=True, exist_ok=True)
                annotation_log_handle = annotation_log_file.open('a', encoding='utf-8')
                self.log_ready.emit(f'Лог operator-разметки: {annotation_log_file}')
            if self.cfg.FRAME_TELEMETRY_LOG_ENABLED and self.cfg.FRAME_TELEMETRY_LOG_PATH:
                telemetry_writer = JsonlTelemetryWriter(
                    self.cfg.FRAME_TELEMETRY_LOG_PATH,
                    flush_every=int(getattr(self.cfg, 'FRAME_TELEMETRY_FLUSH_EVERY', 30)),
                )
                telemetry_writer.open()
                self.log_ready.emit(f'Backend-телеметрия кадров: {self.cfg.FRAME_TELEMETRY_LOG_PATH}')

            session.open()
            self.log_ready.emit(f'Источник открыт: {self.source}')
            if session.gt is not None and session.gt.label_path is not None:
                self.log_ready.emit(f'Эталон GT подключен: {session.gt.label_path}')

            pipeline = TrackerPipeline(self.cfg)
            previous_tracking_mode = 'SCAN'
            while True:
                if self._stop_event.is_set():
                    reason = 'stopped'
                    break
                if self._switch_event.is_set():
                    self._switch_event.clear()
                    pipeline.manager.switch_target()
                ret, frame, meta = session.read()
                if not ret:
                    reason = 'eof'
                    break

                operator_override = self._pop_operator_override()
                operator_hint = operator_hint_from_override(
                    operator_override,
                    frame_index=int(meta.get('frame_index', 0)),
                )
                if operator_override is not None:
                    pipeline.request_operator_target(operator_override)
                    if operator_override.point is not None:
                        self.log_ready.emit(f'Оператор выбрал цель: x={operator_override.point[0]} y={operator_override.point[1]}')
                    else:
                        self.log_ready.emit(f'Оператор выделил цель: bbox={operator_override.bbox}')
                if self._pop_operator_confirm():
                    pipeline.request_operator_confirm()
                    self.log_ready.emit('Оператор подтвердил текущую цель')
                if self._pop_operator_release():
                    pipeline.request_operator_release()
                    self.log_ready.emit('Оператор сбросил текущую цель')

                result = pipeline.process_frame(
                    frame,
                    frame_index=int(meta.get('frame_index', 0)),
                    gt_bbox=meta.get('gt_bbox'),
                    small_target_mode=self.small_target_mode,
                    render=self.render_overlays,
                    source_fps=meta.get('source_fps'),
                )
                display_frame = result.frame if result.frame is not None else frame
                frame_width = int(display_frame.shape[1]) if display_frame is not None else 0
                frame_height = int(display_frame.shape[0]) if display_frame is not None else 0
                if display_frame is not None:
                    session.write(display_frame)
                    qimage = _qimage_from_bgr_frame(display_frame)
                    if qimage is not None:
                        self.frame_ready.emit(qimage)

                display_targets = _display_targets_payload(pipeline, limit=3)
                if telemetry_writer is not None:
                    frame_result = frame_result_from_output(
                        result,
                        source=str(self.source),
                        frame_width=frame_width,
                        frame_height=frame_height,
                        candidates_payload=display_targets,
                        operator_hint=operator_hint,
                        state_before=previous_tracking_mode,
                    )
                    telemetry_writer.write_frame(frame_result)
                previous_tracking_mode = str(result.mode)

                if event_log_handle is not None and result.lock_events:
                    for event in result.lock_events:
                        payload = {
                            'frame_index': int(result.frame_index),
                            'event': event,
                            'active_id': result.active_id,
                            'mode': result.mode,
                            'lock_score': round(float(result.lock_score), 4),
                            'lock_switches_per_min': round(float(result.lock_switches_per_min), 4),
                            'budget_level': int(result.budget_level),
                            'budget_load': round(float(result.budget_load), 4),
                        }
                        event_log_handle.write(json.dumps(payload, ensure_ascii=False) + '\n')
                if (
                    annotation_log_handle is not None
                    and result.operator_override_status in {'applied', 'verifying'}
                    and result.operator_override_bbox is not None
                ):
                    payload = {
                        'frame_index': int(result.frame_index),
                        'source': str(self.source),
                        'bbox_xyxy': list(result.operator_override_bbox),
                        'active_id': result.active_id,
                        'active_source': result.active_source,
                        'event': 'operator_bbox',
                        'operator_status': result.operator_override_status,
                    }
                    annotation_log_handle.write(json.dumps(payload, ensure_ascii=False) + '\n')
                    annotation_log_handle.flush()

                self.stats_ready.emit(
                    {
                        'fps': result.fps,
                        'active_id': result.active_id,
                        'active_bbox': result.active_bbox,
                        'active_source': result.active_source,
                        'display_targets': display_targets,
                        'target_count': result.target_count,
                        'visible_target_count': result.visible_target_count,
                        'mode': result.mode,
                        'operator_workflow_state': result.operator_workflow_state,
                        'operator_workflow_events': result.operator_workflow_events or [],
                        'operator_click_to_lock_frames': result.operator_click_to_lock_frames,
                        'operator_verify_age_frames': result.operator_verify_age_frames,
                        'frame_index': result.frame_index,
                        'frame_width': frame_width,
                        'frame_height': frame_height,
                        'scan_strategy': result.scan_strategy,
                        'gt_visible': result.gt_visible,
                        'gt_iou': result.gt_iou,
                        'lock_score': result.lock_score,
                        'display_confidence': result.display_confidence,
                        'continuity_score': result.continuity_score,
                        'active_presence_rate': result.active_presence_rate,
                        'target_reliability': result.target_reliability,
                        'target_p_present': result.target_p_present,
                        'target_modality': result.target_modality,
                        'tracking_action': result.tracking_action,
                        'decision_path': result.decision_path,
                        'active_id_changes': result.active_id_changes,
                        'median_reacquire_frames': result.median_reacquire_frames,
                        'lock_events': result.lock_events,
                        'lock_switch_count': result.lock_switch_count,
                        'lock_switches_per_min': result.lock_switches_per_min,
                        'lock_event_counts': result.lock_event_counts,
                        'budget_level': result.budget_level,
                        'budget_load': result.budget_load,
                        'budget_frame_ms': result.budget_frame_ms,
                        'roi_budget_candidates': result.roi_budget_candidates,
                        'night_skip': result.night_skip,
                        'timings_ms': result.timings_ms,
                        'operator_override_status': result.operator_override_status,
                        'operator_override_count': result.operator_override_count,
                        'operator_override_bbox': result.operator_override_bbox,
                    }
                )
        except ModelNotFoundError as exc:
            self.failed.emit(str(exc))  # BUG-008: specific model error message
            return
        except SourceOpenError as exc:
            self.failed.emit(str(exc))  # BUG-008: specific source error message
            return
        except InferenceDeviceError as exc:
            self.failed.emit(str(exc))  # BUG-008: specific device error message
            return
        except MemoryError:
            self.failed.emit("Недостаточно памяти для запуска трекера. Закройте другие приложения.")
            return
        except Exception as exc:
            self.failed.emit(f"Неожиданная ошибка: {type(exc).__name__}: {exc}")
            return
        finally:
            if event_log_handle is not None:
                event_log_handle.close()
            if annotation_log_handle is not None:
                annotation_log_handle.close()
            if telemetry_writer is not None:
                telemetry_writer.close()
            session.close()

        self.finished.emit(reason)


class EvaluationWorker(QThread):
    log_ready = Signal(str)
    report_ready = Signal(dict)
    finished = Signal(str)  # done | stopped
    failed = Signal(str)

    def __init__(self, cfg: Config, source, small_target_mode: bool, report_path: str, max_frames: int = 0):
        super().__init__()
        self.cfg = cfg
        self.source = source
        self.small_target_mode = small_target_mode
        self.report_path = report_path
        self.max_frames = max_frames
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        try:
            self.log_ready.emit(f'Оценка запущена: {self.source}')
            report = evaluate_source(
                self.cfg,
                self.source,
                small_target_mode=self.small_target_mode,
                max_frames=self.max_frames,
                report_path=self.report_path,
                stop_checker=self._stop_event.is_set,
            )
            self.report_ready.emit(report.to_dict())
            self.log_ready.emit(f'Отчет оценки сохранен: {self.report_path}')
            reason = 'stopped' if self._stop_event.is_set() else 'done'
            self.finished.emit(reason)
        except Exception as exc:
            self.failed.emit(str(exc))
