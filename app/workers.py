"""app/workers.py — Background QThread workers for tracking and evaluation.

Extracted from main_gui.py (T8a).
"""
import json
import threading
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from uav_tracker.config import Config
from uav_tracker.evaluation import evaluate_source
from uav_tracker.exceptions import InferenceDeviceError, ModelNotFoundError, SourceOpenError
from uav_tracker.pipeline import TrackerPipeline, VideoSession


class TrackerWorker(QThread):
    frame_ready = Signal(object)
    stats_ready = Signal(dict)
    log_ready = Signal(str)
    finished = Signal(str)  # stopped | eof
    failed = Signal(str)

    def __init__(self, cfg: Config, source, output_path: str, small_target_mode: bool, lock_log_path: str = ''):
        super().__init__()
        self.cfg = cfg
        self.source = source
        self.output_path = output_path
        self.small_target_mode = small_target_mode
        self.lock_log_path = lock_log_path.strip()
        self._stop_event = threading.Event()
        self._switch_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def request_switch_target(self):
        self._switch_event.set()

    def run(self):
        reason = 'stopped'
        session = VideoSession(self.cfg, self.source, output_path=self.output_path, manage_cv_windows=False)
        event_log_handle = None
        try:
            resolved_lock_log = self.lock_log_path
            if not resolved_lock_log and self.cfg.LOCK_EVENT_LOG_ENABLED and self.cfg.LOCK_EVENT_LOG_PATH:
                resolved_lock_log = str(self.cfg.LOCK_EVENT_LOG_PATH)
            if resolved_lock_log:
                lock_log_file = Path(resolved_lock_log)
                lock_log_file.parent.mkdir(parents=True, exist_ok=True)
                event_log_handle = lock_log_file.open('a', encoding='utf-8')
                self.log_ready.emit(f'Лог lock-событий: {resolved_lock_log}')

            session.open()
            self.log_ready.emit(f'Источник открыт: {self.source}')
            if session.gt is not None and session.gt.label_path is not None:
                self.log_ready.emit(f'Эталон GT подключен: {session.gt.label_path}')

            pipeline = TrackerPipeline(self.cfg)
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

                result = pipeline.process_frame(
                    frame,
                    frame_index=int(meta.get('frame_index', 0)),
                    gt_bbox=meta.get('gt_bbox'),
                    small_target_mode=self.small_target_mode,
                    render=True,
                    source_fps=meta.get('source_fps'),
                )
                if result.frame is not None:
                    session.write(result.frame)
                    self.frame_ready.emit(result.frame)

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

                self.stats_ready.emit(
                    {
                        'fps': result.fps,
                        'active_id': result.active_id,
                        'active_source': result.active_source,
                        'target_count': result.target_count,
                        'visible_target_count': result.visible_target_count,
                        'mode': result.mode,
                        'frame_index': result.frame_index,
                        'scan_strategy': result.scan_strategy,
                        'gt_visible': result.gt_visible,
                        'gt_iou': result.gt_iou,
                        'lock_score': result.lock_score,
                        'display_confidence': result.display_confidence,
                        'continuity_score': result.continuity_score,
                        'active_presence_rate': result.active_presence_rate,
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
