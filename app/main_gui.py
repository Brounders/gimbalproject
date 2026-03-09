import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import cv2
import numpy as np
from PySide6.QtCore import QSettings, QThread, Qt, Signal
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from uav_tracker.config import Config
from uav_tracker.evaluation import evaluate_source
from uav_tracker.modes import RUNTIME_MODES, apply_runtime_mode
from uav_tracker.pipeline import TrackerPipeline, VideoSession, apply_runtime_preset, parse_video_source
from uav_tracker.profile_io import apply_overrides, available_presets, load_preset, load_profile, save_profile
from app.ui import UIState, UIStateMachine, VideoStage
from app.ui.theme import UI_STATE_VIEW, build_app_stylesheet


SCENARIO_LABELS = {
    'default': 'Дневной (базовый)',
    'small_target': 'Малые цели',
    'night': 'Ночной режим',
    'fast': 'Fast (маневренные цели)',
    'operator_standard': 'Оператор (базовый)',
    'antiuav_thermal': 'Thermal / Anti-UAV',
    'rpi_hailo': 'RPi + Hailo',
    'custom': 'Пользовательский',
}

OPERATOR_ENV_LABELS = {
    'day': 'Day',
    'night': 'Night',
    'ir': 'IR',
}

OPERATOR_ENV_TO_PRESET = {
    'day': 'default',
    'night': 'night_ir_lock_v2',
    'ir': 'antiuav_thermal',
}

OPERATOR_TRACKING_PROFILE_LABELS = {
    'standard': 'Стандарт (0.40)',
    'fast': 'Fast (0.30)',
}

OPERATOR_TRACKING_PROFILE_TO_PRESET = {
    'standard': 'operator_standard',
    'fast': 'fast',
}


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
        self._stop_requested = False
        self._switch_target_requested = False

    def stop(self):
        self._stop_requested = True

    def request_switch_target(self):
        self._switch_target_requested = True

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
                if self._stop_requested:
                    reason = 'stopped'
                    break
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
                if self._switch_target_requested:
                    pipeline.request_manual_target_switch()
                    self._switch_target_requested = False
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
                        'active_cycle_index': result.active_cycle_index,
                        'active_cycle_total': result.active_cycle_total,
                        'target_count': result.target_count,
                        'visible_target_count': result.visible_target_count,
                        'mode': result.mode,
                        'lock_confirmed': result.lock_confirmed,
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
                        'ir_noise_level': result.ir_noise_level,
                        'ir_noise_gate_active': result.ir_noise_gate_active,
                        'lock_confirm_frames_effective': result.lock_confirm_frames_effective,
                        'timings_ms': result.timings_ms,
                    }
                )
        except Exception as exc:
            self.failed.emit(str(exc))
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
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self):
        try:
            self.log_ready.emit(f'Оценка запущена: {self.source}')
            report = evaluate_source(
                self.cfg,
                self.source,
                small_target_mode=self.small_target_mode,
                max_frames=self.max_frames,
                report_path=self.report_path,
                stop_checker=lambda: self._stop_requested,
            )
            self.report_ready.emit(report.to_dict())
            self.log_ready.emit(f'Отчет оценки сохранен: {self.report_path}')
            reason = 'stopped' if self._stop_requested else 'done'
            self.finished.emit(reason)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: TrackerWorker | None = None
        self.eval_worker: EvaluationWorker | None = None
        self._profile_extras: dict[str, Any] = {}
        self._updating_controls = False
        self._is_closing = False
        self._job_state = 'idle'
        self._state_machine = UIStateMachine()
        self._last_active_id: int | None = None
        self._target_present_latched = False
        self._target_missing_streak = 0
        self._had_target_in_session = False

        self._session_history: list[str] = []
        self._recent_sources: list[str] = []
        self._evaluation_reports: list[str] = []
        self._log_count = 0
        self._preview_pixmap: QPixmap | None = None
        self._header_meta_full_text = 'Источник: CAM 0'
        self._header_meta_tooltip = 'Источник: CAM 0'
        self._operator_env_last_resolved = 'day'
        self._runtime_selected_preset = 'default'
        self._runtime_selected_env = 'day'
        self._runtime_env_note = ''
        self._runtime_tracking_profile = 'standard'
        self._last_target_count = 0
        self._lock_started_at_monotonic: float | None = None

        self.settings = QSettings('GimbalProject', 'UAVTrackerApp')
        self.ui_v2_enabled = self._to_bool(self.settings.value('ui/ui_v2_enabled', 'true'), default=True)

        self.setWindowTitle('Система сопровождения БПЛА')
        self.resize(1520, 980)
        self.setMinimumSize(1360, 860)
        self.setStyleSheet(build_app_stylesheet(self.ui_v2_enabled))
        self._build_ui()
        self._wire_actions()
        self._apply_defaults()
        self._load_app_settings()

    @staticmethod
    def _to_bool(value: Any, default: bool = False) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {'1', 'true', 'yes', 'on'}:
            return True
        if text in {'0', 'false', 'no', 'off'}:
            return False
        return default

    def _build_ui(self):
        central = QWidget()
        central.setObjectName('CentralRoot')
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self._workspace_order = ['operator']
        self.workspace_indexes = {'operator': 0}
        self.sidebar_buttons = {}

        root.addWidget(self.build_header())

        body_splitter = QSplitter(Qt.Horizontal)
        body_splitter.setChildrenCollapsible(False)
        body_splitter.addWidget(self.build_left_rail())
        body_splitter.addWidget(self.build_video_stage())
        body_splitter.setStretchFactor(0, 0)
        body_splitter.setStretchFactor(1, 1)
        body_splitter.setSizes([280, 1080])
        root.addWidget(body_splitter, 1)

        root.addWidget(self.build_bottom_console())

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.document().setMaximumBlockCount(500)
        self.logs_workspace_view = self.log_view

        self.build_expert_dialog()
        self._refresh_workspace_overviews()

        self.ui_v2_action = QAction('UI v2', self)
        self.ui_v2_action.setCheckable(True)
        self.ui_v2_action.setChecked(self.ui_v2_enabled)
        self.ui_v2_action.toggled.connect(self._set_ui_v2_enabled)
        self.menuBar().addAction(self.ui_v2_action)

        quit_action = QAction('Выход', self)
        quit_action.triggered.connect(self.close)
        self.menuBar().addAction(quit_action)

    def build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName('HeaderBar')
        header.setMinimumHeight(60)
        header.setMaximumHeight(60)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        self.header_title_label = QLabel('Система сопровождения БПЛА')
        self.header_title_label.setObjectName('WindowTitle')
        layout.addWidget(self.header_title_label)

        layout.addSpacing(6)
        self.top_state_badge = QLabel('IDLE')
        self.top_state_badge.setObjectName('HeaderStatus')
        self.top_state_badge.setProperty('state', 'idle')
        layout.addWidget(self.top_state_badge)

        self.header_source_label = QLabel('Источник: CAM 0 · Режим: Day')
        self.header_source_label.setObjectName('HeaderMeta')
        layout.addWidget(self.header_source_label, 1)

        self.record_indicator_label = QLabel('REC OFF')
        self.record_indicator_label.setObjectName('RecordIndicator')
        self.record_indicator_label.setProperty('recording', False)
        layout.addWidget(self.record_indicator_label)

        self.start_btn = QPushButton('Start')
        self.start_btn.setProperty('variant', 'primary')
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton('Stop')
        self.stop_btn.setProperty('variant', 'destructive')
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        self.next_target_btn = QPushButton('Next Target')
        self.next_target_btn.setProperty('variant', 'ghost')
        self.next_target_btn.setToolTip('Переключить lock на следующий ID из фоновых целей')
        self.next_target_btn.setEnabled(False)
        layout.addWidget(self.next_target_btn)

        self.expert_btn = QPushButton('Expert')
        self.expert_btn.setProperty('variant', 'ghost')
        layout.addWidget(self.expert_btn)

        return header

    def build_left_rail(self) -> QWidget:
        rail = QFrame()
        rail.setObjectName('LeftControlRail')
        rail.setMinimumWidth(280)
        rail.setMaximumWidth(300)
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel('Управление')
        title.setObjectName('RailSectionTitle')
        layout.addWidget(title)

        primary_card = QFrame()
        primary_card.setObjectName('PrimaryControlCard')
        primary_layout = QVBoxLayout(primary_card)
        primary_layout.setContentsMargins(8, 8, 8, 8)
        primary_layout.setSpacing(6)
        primary_layout.addWidget(QLabel('Режим камеры', objectName='RailSectionTitle'))

        self.operator_env_combo = QComboBox()
        self.operator_env_combo.addItem('Day', 'day')
        self.operator_env_combo.addItem('Night', 'night')
        self.operator_env_combo.addItem('IR', 'ir')
        self.operator_env_combo.setToolTip('Режим камеры: Day / Night / IR')
        primary_layout.addWidget(self.operator_env_combo)

        self.operator_env_hint = QLabel('Режим: Day')
        self.operator_env_hint.setObjectName('InspectorValueSub')
        self.operator_env_hint.setWordWrap(True)
        primary_layout.addWidget(self.operator_env_hint)

        # Скрытый контрол для обратной совместимости профилей.
        self.operator_profile_label = QLabel('Профиль сопровождения')
        self.operator_profile_label.setObjectName('RailSectionTitle')
        self.operator_profile_label.setVisible(False)
        primary_layout.addWidget(self.operator_profile_label)

        self.operator_profile_combo = QComboBox()
        self.operator_profile_combo.addItem(OPERATOR_TRACKING_PROFILE_LABELS['standard'], 'standard')
        self.operator_profile_combo.addItem(OPERATOR_TRACKING_PROFILE_LABELS['fast'], 'fast')
        self.operator_profile_combo.setVisible(False)
        primary_layout.addWidget(self.operator_profile_combo)
        layout.addWidget(primary_card)

        source_card = QFrame()
        source_card.setObjectName('SecondaryControlCard')
        source_layout = QVBoxLayout(source_card)
        source_layout.setContentsMargins(8, 8, 8, 8)
        source_layout.setSpacing(6)
        source_layout.addWidget(QLabel('Источник', objectName='RailSectionTitle'))

        self.source_type_combo = QComboBox()
        self.source_type_combo.addItem('Camera', 'camera')
        self.source_type_combo.addItem('Video', 'video')
        self.source_type_combo.addItem('Stream', 'stream')
        source_layout.addWidget(self.source_type_combo)

        self.camera_index_spin = QSpinBox()
        self.camera_index_spin.setRange(0, 16)
        self.camera_index_spin.setValue(0)
        source_layout.addWidget(self.camera_index_spin)

        self.source_path_label = QLabel('Видео файл')
        self.source_path_label.setObjectName('RailSectionTitle')
        source_layout.addWidget(self.source_path_label)

        self.source_path_edit = QLineEdit('')
        self.source_path_edit.setPlaceholderText('/путь/к/видео.mp4')
        source_layout.addWidget(self.source_path_edit)

        self.source_browse_btn = QPushButton('Выбрать...')
        source_layout.addWidget(self.source_browse_btn)
        layout.addWidget(source_card)

        session_card = QFrame()
        session_card.setObjectName('TertiaryControlCard')
        session_layout = QVBoxLayout(session_card)
        session_layout.setContentsMargins(8, 8, 8, 8)
        session_layout.setSpacing(6)
        session_layout.addWidget(QLabel('Сессия', objectName='RailSectionTitle'))

        self.record_check = QCheckBox('Сохранять видео')
        self.record_check.setChecked(True)
        session_layout.addWidget(self.record_check)

        self.output_path_label = QLabel('Выход')
        self.output_path_label.setObjectName('RailSectionTitle')
        session_layout.addWidget(self.output_path_label)

        self.output_edit = QLineEdit(str(ROOT / 'runs' / 'gui_output.mp4'))
        session_layout.addWidget(self.output_edit)

        self.output_browse_btn = QPushButton('Куда сохранить...')
        session_layout.addWidget(self.output_browse_btn)

        self.eval_btn = QPushButton('Evaluate')
        self.eval_btn.setProperty('variant', 'ghost')
        session_layout.addWidget(self.eval_btn)
        layout.addWidget(session_card)

        layout.addStretch(1)
        return rail

    def build_video_stage(self) -> QWidget:
        self.video_stage = VideoStage()
        self.video_label = self.video_stage.surface
        self.target_info_card = self.build_target_info_card()
        self.video_stage.set_overlay_widget(self.target_info_card)
        return self.video_stage

    def build_target_info_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName('TargetInfoCard')
        layout = QGridLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(4)

        self.target_info_state = QLabel('IDLE')
        self.target_info_state.setObjectName('TargetInfoState')
        self.target_info_state.setProperty('state', 'idle')
        layout.addWidget(self.target_info_state, 0, 0, 1, 2)

        id_title = QLabel('ID')
        id_title.setObjectName('TargetInfoTitle')
        self.target_info_id = QLabel('—')
        self.target_info_id.setObjectName('TargetInfoValue')
        layout.addWidget(id_title, 1, 0)
        layout.addWidget(self.target_info_id, 1, 1)

        conf_title = QLabel('БПЛА')
        conf_title.setObjectName('TargetInfoTitle')
        self.target_info_confidence = QLabel('0%')
        self.target_info_confidence.setObjectName('TargetInfoValue')
        layout.addWidget(conf_title, 2, 0)
        layout.addWidget(self.target_info_confidence, 2, 1)

        lock_title = QLabel('Захват')
        lock_title.setObjectName('TargetInfoTitle')
        self.target_info_lock_time = QLabel('00:00')
        self.target_info_lock_time.setObjectName('TargetInfoValue')
        layout.addWidget(lock_title, 3, 0)
        layout.addWidget(self.target_info_lock_time, 3, 1)

        fps_title = QLabel('FPS')
        fps_title.setObjectName('TargetInfoTitle')
        self.target_info_fps = QLabel('0.0')
        self.target_info_fps.setObjectName('TargetInfoValue')
        layout.addWidget(fps_title, 4, 0)
        layout.addWidget(self.target_info_fps, 4, 1)

        return card

    def build_bottom_console(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName('BottomConsole')
        bar.setMinimumHeight(30)
        bar.setMaximumHeight(32)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        self.bottom_console_label = QLabel('$ готово к запуску')
        self.bottom_console_label.setObjectName('BottomConsoleText')
        self.bottom_console_label.setWordWrap(False)
        layout.addWidget(self.bottom_console_label, 1)
        return bar

    def _build_compact_diag_card(self, title: str) -> tuple[QFrame, QLabel, QLabel]:
        card = QFrame()
        card.setObjectName('InspectorCompactCard')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        header = QLabel(title)
        header.setObjectName('InspectorTitle')
        layout.addWidget(header)

        main_value = QLabel('—')
        main_value.setObjectName('InspectorValueMain')
        main_value.setWordWrap(False)
        layout.addWidget(main_value)

        sub_value = QLabel('—')
        sub_value.setObjectName('InspectorValueSub')
        sub_value.setWordWrap(False)
        layout.addWidget(sub_value)
        return card, main_value, sub_value

    def build_compact_diagnostics(self) -> QWidget:
        body = QGroupBox('Данные цели')
        body.setObjectName('CompactDiagnostics')
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(8, 8, 8, 8)
        body_layout.setSpacing(6)

        state_card, self.compact_state_main, self.compact_state_sub = self._build_compact_diag_card('Состояние')
        target_card, self.compact_target_main, self.compact_target_sub = self._build_compact_diag_card('Цель')
        prob_card, self.compact_probability_main, self.compact_probability_sub = self._build_compact_diag_card('Класс')
        runtime_card, self.compact_runtime_main, self.compact_runtime_sub = self._build_compact_diag_card('Захват / FPS')

        self._set_compact_label_text(self.compact_state_main, 'IDLE')
        self._set_compact_label_text(self.compact_state_sub, 'Ожидание цели')
        self._set_compact_label_text(self.compact_target_main, 'ID —')
        self._set_compact_label_text(self.compact_target_sub, 'Фоновых: 0')
        self._set_compact_label_text(self.compact_probability_main, 'БПЛА 0%')
        self._set_compact_label_text(self.compact_probability_sub, 'Подтверждение: 0/0')
        self._set_compact_label_text(self.compact_runtime_main, 'Захват 00:00')
        self._set_compact_label_text(self.compact_runtime_sub, 'FPS 0.0')

        body_layout.addWidget(state_card)
        body_layout.addWidget(target_card)
        body_layout.addWidget(prob_card)
        body_layout.addWidget(runtime_card)
        return body

    def build_diagnostics_dialog(self) -> None:
        # Диалог диагностики удален из операторского контура.
        return

    def build_expert_dialog(self) -> None:
        self.expert_dialog = QDialog(self)
        self.expert_dialog.setWindowTitle('Экспертные настройки')
        self.expert_dialog.resize(860, 620)
        self.expert_dialog.finished.connect(self._on_expert_dialog_closed)

        root = QVBoxLayout(self.expert_dialog)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        scroller = QScrollArea()
        scroller.setWidgetResizable(True)
        root.addWidget(scroller, 1)

        content = QWidget()
        scroller.setWidget(content)
        layout = QGridLayout(content)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        self.scenario_combo = QComboBox()
        self._fill_scenarios()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(available_presets() + ['custom'])
        self.apply_preset_btn = QPushButton('Применить preset')
        self.profile_load_btn = QPushButton('Загрузить профиль')
        self.profile_save_btn = QPushButton('Сохранить профиль')

        self.model_edit = QLineEdit('runs/detect/runs/drone_bird_probe_fast/weights/best.pt')
        self.model_browse_btn = QPushButton('Модель...')

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(list(RUNTIME_MODES))
        self.device_combo = QComboBox()
        self.device_combo.addItems(['mps', 'cpu', 'hailo'])

        self.imgsz_spin = QSpinBox()
        self.imgsz_spin.setRange(160, 2048)
        self.imgsz_spin.setSingleStep(32)
        self.imgsz_spin.setValue(640)
        self.conf_spin = QDoubleSpinBox()
        self.conf_spin.setRange(0.01, 0.99)
        self.conf_spin.setSingleStep(0.01)
        self.conf_spin.setDecimals(2)
        self.conf_spin.setValue(0.30)
        self.rescan_spin = QSpinBox()
        self.rescan_spin.setRange(1, 60)
        self.rescan_spin.setValue(6)

        self.small_target_check = QCheckBox('Малые цели')
        self.adaptive_scan_check = QCheckBox('Adaptive scan')
        self.adaptive_scan_check.setChecked(True)
        self.lock_tracker_check = QCheckBox('Lock tracker')
        self.lock_tracker_check.setChecked(True)
        self.night_check = QCheckBox('Night detector')
        self.night_check.setChecked(True)
        self.roi_check = QCheckBox('ROI assist')
        self.roi_check.setChecked(True)
        self.show_gt_check = QCheckBox('Показывать GT')
        self.show_gt_check.setChecked(True)
        self.timing_check = QCheckBox('Показывать timing')
        self.timing_check.setChecked(True)
        self.show_trails_check = QCheckBox('Показывать траектории')
        self.show_trails_check.setChecked(True)

        row = 0
        layout.addWidget(QLabel('Сценарий'), row, 0)
        layout.addWidget(self.scenario_combo, row, 1, 1, 3)
        row += 1

        layout.addWidget(QLabel('Профиль'), row, 0)
        layout.addWidget(self.preset_combo, row, 1)
        layout.addWidget(self.apply_preset_btn, row, 2)
        layout.addWidget(self.profile_load_btn, row, 3)
        layout.addWidget(self.profile_save_btn, row, 4)
        row += 1

        layout.addWidget(QLabel('Модель'), row, 0)
        layout.addWidget(self.model_edit, row, 1, 1, 3)
        layout.addWidget(self.model_browse_btn, row, 4)
        row += 1

        layout.addWidget(QLabel('Mode'), row, 0)
        layout.addWidget(self.mode_combo, row, 1)
        layout.addWidget(QLabel('Device'), row, 2)
        layout.addWidget(self.device_combo, row, 3)
        row += 1

        layout.addWidget(QLabel('imgsz'), row, 0)
        layout.addWidget(self.imgsz_spin, row, 1)
        layout.addWidget(QLabel('conf'), row, 2)
        layout.addWidget(self.conf_spin, row, 3)
        layout.addWidget(QLabel('rescan'), row, 4)
        layout.addWidget(self.rescan_spin, row, 5)
        row += 1

        layout.addWidget(self.small_target_check, row, 0)
        layout.addWidget(self.adaptive_scan_check, row, 1)
        layout.addWidget(self.lock_tracker_check, row, 2)
        layout.addWidget(self.night_check, row, 3)
        layout.addWidget(self.roi_check, row, 4)
        row += 1

        layout.addWidget(self.show_gt_check, row, 0)
        layout.addWidget(self.timing_check, row, 1)
        layout.addWidget(self.show_trails_check, row, 2)

        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self._hide_expert_dialog)
        root.addWidget(close_btn, 0, Qt.AlignRight)

    def _on_expert_dialog_closed(self, _result: int | None = None):
        self.expert_btn.setProperty('variant', 'ghost')
        self._refresh_widget_style(self.expert_btn)

    def _hide_expert_dialog(self):
        self.expert_dialog.hide()
        self._on_expert_dialog_closed()

    def _set_ui_v2_enabled(self, enabled: bool) -> None:
        self.ui_v2_enabled = bool(enabled)
        self.setStyleSheet(build_app_stylesheet(self.ui_v2_enabled))
        self._refresh_header_state()
        if hasattr(self, 'ui_v2_action') and self.ui_v2_action.isChecked() != self.ui_v2_enabled:
            self.ui_v2_action.blockSignals(True)
            self.ui_v2_action.setChecked(self.ui_v2_enabled)
            self.ui_v2_action.blockSignals(False)

    def _toggle_diagnostics_dialog(self) -> None:
        return

    @staticmethod
    def _compact_source_short(source_type: str, source_hint: str, source_display: str) -> str:
        if source_type == 'video':
            return Path(source_hint).name or source_display
        if source_type != 'stream':
            return source_display
        parsed = urlparse(source_hint)
        if parsed.scheme and parsed.netloc:
            path_part = parsed.path.rstrip('/').split('/')[-1] if parsed.path else ''
            if path_part:
                return f'{parsed.scheme}://{parsed.netloc}/.../{path_part}'
            return f'{parsed.scheme}://{parsed.netloc}'
        text = source_hint.strip()
        if len(text) <= 44:
            return text
        return f'{text[:20]}...{text[-16:]}'

    def _apply_header_meta_text(self) -> None:
        if not hasattr(self, 'header_source_label'):
            return
        metrics = self.header_source_label.fontMetrics()
        width = max(120, self.header_source_label.width() - 8)
        elided = metrics.elidedText(self._header_meta_full_text, Qt.ElideRight, width)
        self.header_source_label.setText(elided)
        self.header_source_label.setToolTip(self._header_meta_tooltip)

    @staticmethod
    def _set_compact_label_text(label: QLabel, text: str) -> None:
        width = max(60, label.width() - 6)
        metrics = label.fontMetrics()
        elided = metrics.elidedText(text, Qt.ElideRight, width)
        label.setText(elided)
        label.setToolTip(text)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _refresh_record_controls(self):
        recording_enabled = self.record_check.isChecked()
        controls_enabled = recording_enabled and self._job_state == 'idle'
        self.output_path_label.setVisible(recording_enabled)
        self.output_edit.setVisible(recording_enabled)
        self.output_browse_btn.setVisible(recording_enabled)
        self.output_edit.setEnabled(controls_enabled)
        self.output_browse_btn.setEnabled(controls_enabled)

    def _build_workspaces(self):
        return

    def _on_workspace_selected(self, key: str):
        _ = key

    def _current_workspace_key(self) -> str:
        return 'operator'

    def _refresh_sidebar_meta(self):
        return

    def _refresh_workspace_overviews(self):
        return

    @staticmethod
    def _operator_env_to_preset(env_key: str) -> str:
        return OPERATOR_ENV_TO_PRESET.get(env_key, 'default')

    @staticmethod
    def _operator_tracking_profile_to_preset(profile_key: str) -> str:
        return OPERATOR_TRACKING_PROFILE_TO_PRESET.get(profile_key, 'operator_standard')

    def _detect_operator_environment(self, source: Any, source_type: str) -> tuple[str, str]:
        # Conservative auto-switch based on first frames brightness/saturation.
        # It runs once before tracking start and does not change runtime logic mid-session.
        frames: list[np.ndarray] = []

        if source_type == 'video':
            src_path = Path(str(source))
            if src_path.exists() and src_path.is_dir():
                image_files = sorted(
                    [
                        p
                        for p in src_path.iterdir()
                        if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}
                    ]
                )
                for path in image_files[:18]:
                    frame = cv2.imread(str(path))
                    if frame is not None:
                        frames.append(frame)
            else:
                cap = cv2.VideoCapture(source)
                if cap.isOpened():
                    for _ in range(18):
                        ok, frame = cap.read()
                        if not ok or frame is None:
                            break
                        frames.append(frame)
                cap.release()
        else:
            cap = cv2.VideoCapture(source)
            if cap.isOpened():
                for _ in range(18):
                    ok, frame = cap.read()
                    if not ok or frame is None:
                        break
                    frames.append(frame)
            cap.release()

        if not frames:
            return 'day', 'авто: нет данных для анализа, выбран День'

        v_values = []
        s_values = []
        for frame in frames:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            v_values.append(float(np.mean(hsv[:, :, 2])))
            s_values.append(float(np.mean(hsv[:, :, 1])))

        v_mean = float(np.mean(v_values))
        s_mean = float(np.mean(s_values))
        if v_mean < 82.0 or (v_mean < 102.0 and s_mean < 46.0):
            return 'night', f'авто: V={v_mean:.1f}, S={s_mean:.1f} -> Ночь'
        return 'day', f'авто: V={v_mean:.1f}, S={s_mean:.1f} -> День'

    def _resolve_operator_env_for_start(self, source: Any, source_type: str) -> tuple[str, str]:
        env_key = str(self.operator_env_combo.currentData() or 'day')
        if env_key in {'day', 'night', 'ir'}:
            return env_key, f'ручной режим: {OPERATOR_ENV_LABELS.get(env_key, env_key)}'
        return self._detect_operator_environment(source, source_type)

    def _on_operator_env_changed(self) -> None:
        if self._updating_controls:
            return
        env_key = str(self.operator_env_combo.currentData() or 'day')
        preset_key = self._operator_env_to_preset(env_key)
        if self.scenario_combo.findData(preset_key) >= 0:
            self._apply_scenario_preset(preset_key)
        profile_key = str(self.operator_profile_combo.currentData() or 'standard')
        profile_preset = self._operator_tracking_profile_to_preset(profile_key)
        if profile_preset in set(available_presets()):
            _cfg, overlay_data = load_preset(profile_preset, Config())
            self._profile_extras.update(overlay_data)
        self._runtime_tracking_profile = profile_key
        self.operator_env_hint.setText(f'Ручной режим: {OPERATOR_ENV_LABELS.get(env_key, env_key)}')
        self._refresh_header_state()

    def _on_operator_profile_changed(self) -> None:
        if self._updating_controls:
            return
        env_key = str(self.operator_env_combo.currentData() or 'day')
        if env_key in {'day', 'night', 'ir'}:
            preset_key = self._operator_env_to_preset(env_key)
            if self.scenario_combo.findData(preset_key) >= 0:
                self._apply_scenario_preset(preset_key)
        profile_key = str(self.operator_profile_combo.currentData() or 'standard')
        profile_preset = self._operator_tracking_profile_to_preset(profile_key)
        if profile_preset in set(available_presets()):
            _cfg, overlay_data = load_preset(profile_preset, Config())
            self._profile_extras.update(overlay_data)
        self._runtime_tracking_profile = profile_key
        try:
            self.settings.setValue('ui/profile_json', json.dumps(self._collect_profile(), ensure_ascii=False))
        except Exception:
            pass
        self._refresh_header_state()

    def _fill_scenarios(self):
        available = set(available_presets())
        ordered = [
            'default',
            'operator_standard',
            'fast',
            'small_target',
            'night',
            'antiuav_thermal',
            'rpi_hailo',
        ]
        for key in ordered:
            if key in available:
                self.scenario_combo.addItem(SCENARIO_LABELS.get(key, key), key)
        for key in sorted(available):
            if key not in ordered:
                self.scenario_combo.addItem(SCENARIO_LABELS.get(key, key), key)
        self.scenario_combo.addItem(SCENARIO_LABELS['custom'], 'custom')

    def _wire_actions(self):
        self.source_type_combo.currentIndexChanged.connect(self._on_source_type_changed)
        self.source_browse_btn.clicked.connect(self._browse_source)
        self.output_browse_btn.clicked.connect(self._browse_output)
        self.record_check.stateChanged.connect(self._refresh_record_controls)
        self.record_check.stateChanged.connect(self._refresh_header_state)
        self.camera_index_spin.valueChanged.connect(self._refresh_header_state)
        self.source_path_edit.textChanged.connect(self._refresh_header_state)

        self.expert_btn.clicked.connect(self._toggle_expert_mode)
        self.model_browse_btn.clicked.connect(self._browse_model)
        self.operator_env_combo.currentIndexChanged.connect(self._on_operator_env_changed)
        self.operator_profile_combo.currentIndexChanged.connect(self._on_operator_profile_changed)

        self.scenario_combo.currentIndexChanged.connect(self._on_scenario_changed)
        self.mode_combo.currentTextChanged.connect(self._apply_runtime_mode_controls)
        self.apply_preset_btn.clicked.connect(self._apply_selected_preset)
        self.profile_load_btn.clicked.connect(self._load_profile_from_disk)
        self.profile_save_btn.clicked.connect(self._save_profile_to_disk)

        self.start_btn.clicked.connect(self._start)
        self.stop_btn.clicked.connect(self._stop)
        self.eval_btn.clicked.connect(self._evaluate)
        self.next_target_btn.clicked.connect(self._switch_target)

        self.command_palette_shortcut = QShortcut(QKeySequence('Ctrl+K'), self)
        self.command_palette_shortcut.activated.connect(self._open_command_palette)
        self.next_target_shortcut = QShortcut(QKeySequence('N'), self)
        self.next_target_shortcut.activated.connect(self._switch_target)

    def _apply_defaults(self):
        self.mode_combo.setCurrentText('operator')
        self._apply_runtime_mode_controls('operator')
        idx = self.scenario_combo.findData('default')
        if idx >= 0:
            self.scenario_combo.setCurrentIndex(idx)
            self._on_scenario_changed()
        env_idx = self.operator_env_combo.findData('day')
        if env_idx >= 0:
            self.operator_env_combo.setCurrentIndex(env_idx)
            self._on_operator_env_changed()
        profile_idx = self.operator_profile_combo.findData('standard')
        if profile_idx >= 0:
            self.operator_profile_combo.setCurrentIndex(profile_idx)
            self._on_operator_profile_changed()
        self._refresh_record_controls()
        self._on_source_type_changed()
        self._refresh_header_state()
        self._on_workspace_selected('operator')
        self._refresh_workspace_overviews()
        self._refresh_sidebar_meta()
        self._log('Интерфейс готов.')

    def _set_sidebar_active(self, active_btn: QPushButton):
        for btn in self.sidebar_buttons.values():
            btn.setChecked(btn is active_btn)

    def _show_help(self):
        QMessageBox.information(
            self,
            'Справка',
            'Быстрый сценарий:\n'
            '1) Выберите источник (камера/видео/поток).\n'
            '2) Выберите режим камеры (Day/Night/IR).\n'
            '3) При необходимости включите запись.\n'
            '4) Нажмите Старт.\n\n'
            'Карточка цели находится в правом верхнем углу видео.\n'
            'Горячая клавиша: N — следующая цель.\n'
            'Экспертные настройки открываются отдельным окном.',
        )

    def _open_command_palette(self):
        items = ['Старт', 'Стоп', 'Оценка', 'Следующая цель', 'Экспертные настройки']
        selected, ok = QInputDialog.getItem(self, 'Командная палитра', 'Выберите действие', items, 0, False)
        if not ok or not selected:
            return

        if selected == 'Старт':
            self._start()
            return
        if selected == 'Стоп':
            self._stop()
            return
        if selected == 'Оценка':
            self._evaluate()
            return
        if selected == 'Следующая цель':
            self._switch_target()
            return
        if selected == 'Экспертные настройки':
            self._toggle_expert_mode()
            return

    def _refresh_widget_style(self, widget: QWidget):
        style = widget.style()
        if style is not None:
            style.unpolish(widget)
            style.polish(widget)
        widget.update()

    def _refresh_header_state(self):
        scenario_key = str(self.scenario_combo.currentData() or 'custom')
        scenario_label = SCENARIO_LABELS.get(scenario_key, scenario_key)
        env_key = str(self.operator_env_combo.currentData() or 'day')
        operator_scene_label = OPERATOR_ENV_LABELS.get(env_key, env_key)
        tracking_profile = str(self.operator_profile_combo.currentData() or 'standard')
        tracking_profile_label = OPERATOR_TRACKING_PROFILE_LABELS.get(tracking_profile, tracking_profile)

        source_type = str(self.source_type_combo.currentData() or 'camera')
        if source_type == 'camera':
            source_display = f"CAM {self.camera_index_spin.value()}"
        elif source_type == 'stream':
            source_display = 'ПОТОК'
        else:
            source_display = 'ВИДЕО'
        source_hint = str(self.source_path_edit.text().strip() or source_display)
        source_short = self._compact_source_short(source_type, source_hint, source_display)

        self._header_meta_full_text = f"Источник: {source_short} · Режим: {operator_scene_label}"
        self._header_meta_tooltip = (
            f"Режим оператора: {operator_scene_label}\n"
            f"Профиль сопровождения: {tracking_profile_label}\n"
            f"Сценарий: {scenario_label}\n"
            f"Источник: {source_hint}"
        )
        self._apply_header_meta_text()

        state_meta = UI_STATE_VIEW.get(self._state_machine.state, UI_STATE_VIEW[UIState.IDLE])
        state_text = state_meta['badge']
        state_name = state_meta['state']
        self.top_state_badge.setText(state_text)
        self.top_state_badge.setProperty('state', state_name)
        self._refresh_widget_style(self.top_state_badge)

        recording = self._job_state in {'tracking', 'stopping'} and self.record_check.isChecked()
        if recording:
            self.record_indicator_label.setText('REC ON')
        elif self.record_check.isChecked():
            self.record_indicator_label.setText('REC READY')
        else:
            self.record_indicator_label.setText('REC OFF')
        self.record_indicator_label.setProperty('recording', recording)
        self._refresh_widget_style(self.record_indicator_label)

    def _video_idle_text(self, detail: str | None = None) -> str:
        base = 'Операторская сцена пока не активна'
        steps = '1) Выбери источник\n2) Выбери режим камеры\n3) Нажми Старт'
        if detail:
            return f'{detail}\n\n{steps}'
        return f'{base}\n\n{steps}'

    def _set_video_idle_state(self, detail: str | None = None) -> None:
        self._preview_pixmap = None
        self.video_label.clear()
        self.video_label.setText(self._video_idle_text(detail))
        self._set_target_info_values('IDLE', '—', '0%', '00:00', '0.0')

    def _render_preview_pixmap(self) -> None:
        if self._preview_pixmap is None:
            return
        self.video_label.setPixmap(
            self._preview_pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def _split_source(self, source: Any) -> tuple[str, int, str]:
        if isinstance(source, int):
            return 'camera', int(source), ''
        text = str(source).strip()
        if text.isdigit():
            return 'camera', int(text), ''
        lowered = text.lower()
        if lowered.startswith(('rtsp://', 'http://', 'https://', 'udp://', 'tcp://')):
            return 'stream', 0, text
        return 'video', 0, text

    def _source_from_controls(self):
        source_type = self.source_type_combo.currentData()
        if source_type == 'camera':
            return int(self.camera_index_spin.value())
        return self.source_path_edit.text().strip()

    def _on_source_type_changed(self):
        if self._updating_controls:
            return
        source_type = self.source_type_combo.currentData()
        is_camera = source_type == 'camera'
        controls_enabled = self._job_state == 'idle'
        self.camera_index_spin.setEnabled(is_camera and controls_enabled)
        self.camera_index_spin.setVisible(is_camera)
        show_path = source_type in {'video', 'stream'}
        self.source_path_label.setVisible(show_path)
        self.source_path_edit.setVisible(show_path)
        self.source_browse_btn.setVisible(show_path)
        self.source_path_edit.setEnabled(show_path and controls_enabled)
        self.source_browse_btn.setEnabled(show_path and controls_enabled)
        if is_camera:
            self.source_path_edit.setPlaceholderText('Для камеры путь не нужен')
            self.source_browse_btn.setText('Выбрать...')
        elif source_type == 'video':
            self.source_path_label.setText('Видео файл')
            self.source_path_edit.setPlaceholderText('/путь/к/видео.mp4')
            self.source_browse_btn.setText('Выбрать...')
        else:
            self.source_path_label.setText('URL потока')
            self.source_path_edit.setPlaceholderText('rtsp://...')
            self.source_browse_btn.setText('Подключить...')
        self._refresh_header_state()
        self._refresh_workspace_overviews()

    def _browse_source(self):
        source_type = self.source_type_combo.currentData()
        if source_type == 'stream':
            url, ok = QInputDialog.getText(self, 'Подключение к потоку', 'Введите URL потока:', text=self.source_path_edit.text())
            if ok and url.strip():
                self.source_path_edit.setText(url.strip())
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            'Выберите видео',
            str(ROOT / 'test_videos'),
            'Видео (*.mp4 *.mov *.avi *.mkv);;Все файлы (*)',
        )
        if path:
            self.source_path_edit.setText(path)

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Куда сохранить видео', self.output_edit.text(), 'MP4 (*.mp4)')
        if path:
            self.output_edit.setText(path)

    def _browse_model(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Выберите модель', str(ROOT), 'Модель (*.pt *.hef);;Все файлы (*)')
        if path:
            self.model_edit.setText(path)

    def _toggle_expert_mode(self):
        if self.expert_dialog.isVisible():
            self._hide_expert_dialog()
            return
        self.expert_dialog.show()
        self.expert_dialog.raise_()
        self.expert_dialog.activateWindow()
        self.expert_btn.setProperty('variant', 'primary')
        self._refresh_widget_style(self.expert_btn)

    def _on_scenario_changed(self):
        if self._updating_controls:
            self._refresh_header_state()
            return
        key = self.scenario_combo.currentData()
        self._refresh_header_state()
        self._refresh_workspace_overviews()
        if key in (None, 'custom'):
            return
        self._apply_scenario_preset(key)

    def _apply_quick_profile(self, preset_key: str):
        idx = self.scenario_combo.findData(preset_key)
        if idx >= 0:
            self.scenario_combo.setCurrentIndex(idx)
            return
        self._log(f'Preset недоступен: {preset_key}')

    def _apply_scenario_preset(self, preset_key: str):
        cfg, data = load_preset(preset_key, Config())
        profile = {
            'preset': preset_key,
            'operator_env_mode': str(self.operator_env_combo.currentData() or 'day'),
            'operator_profile_mode': str(self.operator_profile_combo.currentData() or 'standard'),
            'runtime_mode': cfg.RUNTIME_MODE,
            'model_path': cfg.MODEL_PATH,
            'device': cfg.DEVICE,
            'imgsz': cfg.IMG_SIZE,
            'conf_thresh': cfg.CONF_THRESH,
            'small_target_mode': bool(data.get('small_target_mode', False)),
            'adaptive_scan_enabled': cfg.ADAPTIVE_SCAN_ENABLED,
            'global_scan_interval': cfg.GLOBAL_SCAN_INTERVAL,
            'lock_tracker_enabled': cfg.LOCK_TRACKER_ENABLED,
            'night_enabled': cfg.NIGHT_ENABLED,
            'roi_assist_enabled': cfg.ROI_ASSIST_ENABLED,
            'show_gt_overlay': cfg.SHOW_GT_OVERLAY,
            'show_debug_timings': cfg.SHOW_DEBUG_TIMINGS,
            'show_trails': cfg.SHOW_TRAILS,
        }
        profile.update({k: v for k, v in data.items() if k not in profile})
        self._set_controls_from_profile(profile, preserve_source=True)
        self._log(f'Сценарий применен: {SCENARIO_LABELS.get(preset_key, preset_key)}')

    def _apply_runtime_mode_controls(self, mode: str):
        if self._updating_controls:
            return
        cfg = apply_runtime_mode(Config(), mode)
        self.show_gt_check.setChecked(cfg.SHOW_GT_OVERLAY)
        self.timing_check.setChecked(cfg.SHOW_DEBUG_TIMINGS)
        self.show_trails_check.setChecked(cfg.SHOW_TRAILS)
        self.adaptive_scan_check.setChecked(cfg.ADAPTIVE_SCAN_ENABLED)
        self.lock_tracker_check.setChecked(cfg.LOCK_TRACKER_ENABLED)
        self.night_check.setChecked(cfg.NIGHT_ENABLED)
        self.roi_check.setChecked(cfg.ROI_ASSIST_ENABLED)
        self.rescan_spin.setValue(cfg.GLOBAL_SCAN_INTERVAL)

    def _set_controls_from_profile(self, profile: dict[str, Any], preserve_source: bool = False):
        self._updating_controls = True
        try:
            preset = profile.get('preset', 'custom')
            pidx = self.preset_combo.findText(str(preset))
            if pidx >= 0:
                self.preset_combo.setCurrentIndex(pidx)
            else:
                custom_pidx = self.preset_combo.findText('custom')
                if custom_pidx >= 0:
                    self.preset_combo.setCurrentIndex(custom_pidx)
            scenario_idx = self.scenario_combo.findData(preset if preset is not None else 'custom')
            if scenario_idx >= 0:
                self.scenario_combo.setCurrentIndex(scenario_idx)
            else:
                custom_idx = self.scenario_combo.findData('custom')
                if custom_idx >= 0:
                    self.scenario_combo.setCurrentIndex(custom_idx)

            if not preserve_source:
                source_type, cam_idx, source_path = self._split_source(profile.get('source', 0))
                st_idx = self.source_type_combo.findData(source_type)
                if st_idx >= 0:
                    self.source_type_combo.setCurrentIndex(st_idx)
                self.camera_index_spin.setValue(cam_idx)
                self.source_path_edit.setText(source_path)

            mode = str(profile.get('runtime_mode', self.mode_combo.currentText()))
            if self.mode_combo.findText(mode) >= 0:
                self.mode_combo.setCurrentText(mode)
            op_env = str(profile.get('operator_env_mode', self.operator_env_combo.currentData() or 'day'))
            env_idx = self.operator_env_combo.findData(op_env)
            if env_idx >= 0:
                self.operator_env_combo.setCurrentIndex(env_idx)
            op_profile = str(profile.get('operator_profile_mode', self.operator_profile_combo.currentData() or 'standard'))
            profile_idx = self.operator_profile_combo.findData(op_profile)
            if profile_idx >= 0:
                self.operator_profile_combo.setCurrentIndex(profile_idx)

            device = str(profile.get('device', self.device_combo.currentText()))
            if self.device_combo.findText(device) >= 0:
                self.device_combo.setCurrentText(device)

            self.model_edit.setText(str(profile.get('model_path', self.model_edit.text())))
            self.imgsz_spin.setValue(int(profile.get('imgsz', self.imgsz_spin.value())))
            self.conf_spin.setValue(float(profile.get('conf_thresh', self.conf_spin.value())))
            self.rescan_spin.setValue(int(profile.get('global_scan_interval', self.rescan_spin.value())))

            self.small_target_check.setChecked(bool(profile.get('small_target_mode', self.small_target_check.isChecked())))
            self.adaptive_scan_check.setChecked(bool(profile.get('adaptive_scan_enabled', self.adaptive_scan_check.isChecked())))
            self.lock_tracker_check.setChecked(bool(profile.get('lock_tracker_enabled', self.lock_tracker_check.isChecked())))
            self.night_check.setChecked(bool(profile.get('night_enabled', self.night_check.isChecked())))
            self.roi_check.setChecked(bool(profile.get('roi_assist_enabled', self.roi_check.isChecked())))
            self.show_gt_check.setChecked(bool(profile.get('show_gt_overlay', self.show_gt_check.isChecked())))
            self.timing_check.setChecked(bool(profile.get('show_debug_timings', self.timing_check.isChecked())))
            self.show_trails_check.setChecked(bool(profile.get('show_trails', self.show_trails_check.isChecked())))

            self.record_check.setChecked(bool(profile.get('record_output', self.record_check.isChecked())))
            self.output_edit.setText(str(profile.get('output_path', self.output_edit.text())))

            ignored = {
                'preset', 'runtime_mode', 'source', 'model_path', 'device', 'imgsz', 'conf_thresh',
                'small_target_mode', 'adaptive_scan_enabled', 'global_scan_interval', 'lock_tracker_enabled',
                'night_enabled', 'roi_assist_enabled', 'show_gt_overlay', 'show_debug_timings', 'show_trails',
                'record_output', 'output_path', 'operator_env_mode', 'operator_profile_mode'
            }
            self._profile_extras = {k: v for k, v in profile.items() if k not in ignored}
        finally:
            self._updating_controls = False
            self._refresh_record_controls()
            self._on_source_type_changed()
            self._refresh_workspace_overviews()
            self._refresh_sidebar_meta()
            self._refresh_header_state()

    def _apply_selected_preset(self):
        if self._updating_controls:
            return
        preset_name = self.preset_combo.currentText()
        if preset_name == 'custom':
            self._profile_extras = {}
            self._log('Preset: custom')
            return
        self._apply_scenario_preset(preset_name)

    def _collect_profile(self) -> dict[str, Any]:
        source = self._source_from_controls()
        preset_key = self.scenario_combo.currentData() or 'custom'
        profile = {
            'preset': preset_key,
            'operator_env_mode': str(self.operator_env_combo.currentData() or 'day'),
            'operator_profile_mode': str(self.operator_profile_combo.currentData() or 'standard'),
            'runtime_mode': self.mode_combo.currentText(),
            'source': str(source),
            'model_path': self.model_edit.text().strip(),
            'device': self.device_combo.currentText(),
            'imgsz': int(self.imgsz_spin.value()),
            'conf_thresh': float(self.conf_spin.value()),
            'small_target_mode': self.small_target_check.isChecked(),
            'adaptive_scan_enabled': self.adaptive_scan_check.isChecked(),
            'global_scan_interval': int(self.rescan_spin.value()),
            'lock_tracker_enabled': self.lock_tracker_check.isChecked(),
            'night_enabled': self.night_check.isChecked(),
            'roi_assist_enabled': self.roi_check.isChecked(),
            'show_gt_overlay': self.show_gt_check.isChecked(),
            'show_debug_timings': self.timing_check.isChecked(),
            'show_trails': self.show_trails_check.isChecked(),
            'record_output': self.record_check.isChecked(),
            'output_path': self.output_edit.text().strip(),
        }
        profile.update(self._profile_extras)
        return profile

    def _load_profile_from_disk(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Загрузить профиль', str(ROOT / 'configs'), 'YAML (*.yaml *.yml)')
        if not path:
            return
        profile = load_profile(path)
        self._set_controls_from_profile(profile)
        self._log(f'Профиль загружен: {path}')

    def _save_profile_to_disk(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Сохранить профиль', str(ROOT / 'configs' / 'custom_profile.yaml'), 'YAML (*.yaml *.yml)')
        if not path:
            return
        save_profile(path, self._collect_profile())
        self._log(f'Профиль сохранен: {path}')

    def _build_config(self) -> tuple[Config, Any, bool, str]:
        source = parse_video_source(self._source_from_controls())
        small_target_mode = self.small_target_check.isChecked()
        source_type = self.source_type_combo.currentData()

        resolved_env, env_note = self._resolve_operator_env_for_start(source, str(source_type))
        preset_key = self._operator_env_to_preset(resolved_env)
        tracking_profile_key = str(self.operator_profile_combo.currentData() or 'standard')
        tracking_profile_preset = self._operator_tracking_profile_to_preset(tracking_profile_key)
        available = set(available_presets())
        if preset_key in available:
            cfg, _preset_data = load_preset(preset_key, Config())
        else:
            cfg = Config()
            preset_key = 'custom'
        if tracking_profile_preset in available:
            cfg, _tracking_overrides = load_preset(tracking_profile_preset, cfg)

        self._runtime_selected_preset = preset_key
        self._runtime_selected_env = resolved_env
        self._runtime_env_note = env_note
        self._runtime_tracking_profile = tracking_profile_key
        self._operator_env_last_resolved = resolved_env
        self.operator_env_hint.setText(env_note)

        if preset_key != 'custom':
            self._updating_controls = True
            try:
                idx = self.scenario_combo.findData(preset_key)
                if idx >= 0:
                    self.scenario_combo.setCurrentIndex(idx)
                pidx = self.preset_combo.findText(preset_key)
                if pidx >= 0:
                    self.preset_combo.setCurrentIndex(pidx)
            finally:
                self._updating_controls = False

        cfg = apply_runtime_mode(cfg, self.mode_combo.currentText())
        cfg.MODEL_PATH = self.model_edit.text().strip() or cfg.MODEL_PATH
        cfg.DEVICE = self.device_combo.currentText()
        cfg.NIGHT_ENABLED = self.night_check.isChecked()
        cfg.ROI_ASSIST_ENABLED = self.roi_check.isChecked()
        cfg.ADAPTIVE_SCAN_ENABLED = self.adaptive_scan_check.isChecked()
        cfg.LOCK_TRACKER_ENABLED = self.lock_tracker_check.isChecked()
        cfg.GLOBAL_SCAN_INTERVAL = int(self.rescan_spin.value())
        cfg.SHOW_GT_OVERLAY = self.show_gt_check.isChecked()
        cfg.SHOW_DEBUG_TIMINGS = self.timing_check.isChecked()
        cfg.SHOW_TRAILS = self.show_trails_check.isChecked()

        cfg = apply_overrides(cfg, self._profile_extras)
        cfg = apply_runtime_preset(
            cfg,
            small_target_mode=small_target_mode,
            imgsz=int(self.imgsz_spin.value()),
            conf=float(self.conf_spin.value()),
        )
        output_path = self.output_edit.text().strip() if self.record_check.isChecked() else ''

        if source_type != 'camera':
            source_text = str(source).strip()
            if not source_text:
                raise ValueError('Не указан источник: выберите видеофайл или URL потока.')
            if source_type == 'video' and not Path(source_text).exists():
                raise ValueError(f'Источник не найден: {source_text}')
        if self.record_check.isChecked() and not output_path:
            raise ValueError('Укажите путь сохранения выходного видео.')

        return cfg, source, small_target_mode, output_path

    def _set_job_state(self, state: str):
        self._job_state = state
        if state == 'idle':
            self._state_machine.set(UIState.IDLE)
        elif state == 'tracking':
            self._state_machine.set(UIState.RUNNING)
        elif state == 'stopping':
            self._state_machine.set(UIState.CHECKING)
        elif state == 'evaluating':
            self._state_machine.set(UIState.EVALUATION)

        tracking_active = state in {'tracking', 'stopping'}
        evaluating_active = state == 'evaluating'
        busy = tracking_active or evaluating_active

        self.start_btn.setEnabled(self._state_machine.can_start() and not busy)
        self.eval_btn.setEnabled(self._state_machine.can_evaluate() and not busy)
        self.stop_btn.setEnabled(self._state_machine.can_stop())

        for widget in [
            self.scenario_combo,
            self.operator_env_combo,
            self.operator_profile_combo,
            self.source_type_combo,
            self.camera_index_spin,
            self.source_path_edit,
            self.source_browse_btn,
            self.record_check,
            self.output_edit,
            self.output_browse_btn,
            self.expert_btn,
        ]:
            widget.setEnabled(not busy)
        self.next_target_btn.setEnabled(tracking_active and self._last_target_count > 1)
        self._refresh_record_controls()

        if state == 'idle':
            self._target_present_latched = False
            self._target_missing_streak = 0
            self._had_target_in_session = False
            self._lock_started_at_monotonic = None
            self._last_target_count = 0
            self._set_target_info_values('IDLE', '—', '0%', '00:00', '0.0')

        self._on_source_type_changed()
        self._refresh_header_state()

    def _start(self):
        if self.worker is not None and self.worker.isRunning():
            return
        if self.eval_worker is not None and self.eval_worker.isRunning():
            return

        try:
            cfg, source, small_target_mode, output_path = self._build_config()
        except Exception as exc:
            QMessageBox.critical(self, 'Ошибка конфигурации', str(exc))
            return

        base_preset = str(self._runtime_selected_preset or self.scenario_combo.currentData() or 'custom')
        scenario_key = f'{base_preset}_{self._runtime_tracking_profile}'
        source_name = Path(str(source)).stem if isinstance(source, str) and str(source) else f'camera_{source}'
        safe_source = ''.join(ch if ch.isalnum() or ch in {'-', '_'} else '_' for ch in source_name)[:40] or 'source'
        ts = time.strftime('%Y%m%d_%H%M%S')
        lock_log_path = ROOT / 'runs' / 'lock_events' / f'{ts}_{scenario_key}_{safe_source}.jsonl'
        cfg.LOCK_EVENT_LOG_ENABLED = True
        cfg.LOCK_EVENT_LOG_PATH = str(lock_log_path)

        self.worker = TrackerWorker(cfg, source, output_path, small_target_mode, lock_log_path=str(lock_log_path))
        self.worker.frame_ready.connect(self._update_frame)
        self.worker.stats_ready.connect(self._update_stats)
        self.worker.log_ready.connect(self._log)
        self.worker.finished.connect(self._on_tracking_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

        self._set_job_state('tracking')
        self._set_video_idle_state('Подключение к источнику...')
        source_descriptor = f"camera:{source}" if isinstance(source, int) else str(source)
        self._session_history.append(f"{ts} | {scenario_key} | {source_descriptor}")
        if source_descriptor not in self._recent_sources:
            self._recent_sources.append(source_descriptor)
        self._refresh_workspace_overviews()
        self._refresh_sidebar_meta()
        self._log(
            f'Старт: source={source} env={self._runtime_selected_env} profile={self._runtime_tracking_profile} preset={scenario_key} '
            f'mode={cfg.RUNTIME_MODE} device={cfg.DEVICE} '
            f'imgsz={cfg.IMG_SIZE} conf={cfg.CONF_THRESH:.2f} '
            f'adaptive={cfg.ADAPTIVE_SCAN_ENABLED} lock_tracker={cfg.LOCK_TRACKER_ENABLED}'
        )
        if self._runtime_env_note:
            self._log(self._runtime_env_note)
        self._log(f'Lock events -> {lock_log_path}')

    def _stop(self):
        if self.worker is not None and self.worker.isRunning():
            self._set_job_state('stopping')
            self.worker.stop()
            self._log('Остановка сессии запрошена...')
            return
        if self.eval_worker is not None and self.eval_worker.isRunning():
            self._set_job_state('stopping')
            self.eval_worker.stop()
            self._log('Остановка оценки запрошена...')

    def _switch_target(self):
        if self.worker is None or not self.worker.isRunning():
            return
        self.worker.request_switch_target()
        self._log('Запрошено переключение на следующий ID.')

    def _evaluate(self):
        if self.worker is not None and self.worker.isRunning():
            return
        if self.eval_worker is not None and self.eval_worker.isRunning():
            return

        try:
            cfg, source, small_target_mode, _output_path = self._build_config()
        except Exception as exc:
            QMessageBox.critical(self, 'Ошибка конфигурации', str(exc))
            return

        source_name = Path(str(source)).stem if isinstance(source, str) else f'camera_{source}'
        report_path = str(ROOT / 'runs' / 'evaluations' / f'{source_name}_{cfg.RUNTIME_MODE}.json')

        self.eval_worker = EvaluationWorker(cfg, source, small_target_mode, report_path, max_frames=0)
        self.eval_worker.log_ready.connect(self._log)
        self.eval_worker.report_ready.connect(self._on_eval_report)
        self.eval_worker.finished.connect(self._on_eval_finished)
        self.eval_worker.failed.connect(self._on_failed)
        self.eval_worker.start()

        self._set_job_state('evaluating')

    def _on_tracking_finished(self, reason: str):
        if reason == 'stopped':
            self._log('Сессия остановлена пользователем.')
            self._set_video_idle_state('Сессия остановлена. Поток не активен.')
        elif reason == 'eof':
            self._log('Сессия завершена: поток закончился.')
            self._set_video_idle_state('Источник закончился. Поток не активен.')
        else:
            self._log(f'Сессия завершена: {reason}')
            self._set_video_idle_state(f'Сессия завершена: {reason}')
        self.worker = None
        self._set_job_state('idle')

    def _on_eval_finished(self, reason: str):
        self.eval_worker = None
        self._set_job_state('idle')
        if reason == 'stopped':
            self._log('Оценка остановлена пользователем.')
            self._set_video_idle_state('Оценка остановлена. Поток не активен.')
        else:
            self._log('Оценка завершена.')
            self._set_video_idle_state('Оценка завершена. Поток не активен.')

    def _on_failed(self, message: str):
        self.worker = None
        self.eval_worker = None
        self._set_job_state('idle')
        self._state_machine.set(UIState.ERROR)
        self._refresh_header_state()
        self._set_video_idle_state('Ошибка потока. Проверь журнал и конфигурацию.')
        self._log(f'Ошибка: {message}')
        if not self._is_closing:
            QMessageBox.critical(self, 'Ошибка', message)

    def _on_eval_report(self, report: dict):
        self._evaluation_reports.append(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} | frames={report.get('total_frames', 0)} | "
            f"lock={report.get('lock_frames', 0)} | fps={report.get('avg_fps', 0.0):.1f}"
        )
        self._refresh_workspace_overviews()
        self._refresh_sidebar_meta()
        self._log(json.dumps(report, indent=2, ensure_ascii=False))

    def _update_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self._preview_pixmap = QPixmap.fromImage(image)
        self._render_preview_pixmap()

    def _update_stats(self, stats: dict):
        timings = stats.get('timings_ms', {})
        active_id = stats.get('active_id')
        active_source = str(stats.get('active_source', '-'))
        tracker_mode = str(stats.get('mode', 'SCAN')).upper()
        lock_confirmed = bool(stats.get('lock_confirmed', False))
        frame_index = int(stats.get('frame_index', 0))
        fps = float(stats.get('fps') or 0.0)
        gt_visible = bool(stats.get('gt_visible', False))
        gt_iou = float(stats.get('gt_iou') or 0.0)
        lock_score = float(stats.get('lock_score') or 0.0)
        display_confidence = max(0.0, min(1.0, float(stats.get('display_confidence') or 0.0)))
        continuity_score = max(0.0, min(1.0, float(stats.get('continuity_score') or 0.0)))
        active_presence_rate = max(0.0, min(1.0, float(stats.get('active_presence_rate') or 0.0)))
        lock_switches_per_min = float(stats.get('lock_switches_per_min') or 0.0)
        lock_switch_count = int(stats.get('lock_switch_count', 0))
        lock_confirm_frames_effective = int(stats.get('lock_confirm_frames_effective', 0))
        ir_noise_level = float(stats.get('ir_noise_level') or 0.0)
        ir_noise_gate_active = bool(stats.get('ir_noise_gate_active', False))
        cycle_index = int(stats.get('active_cycle_index', 0))
        cycle_total = int(stats.get('active_cycle_total', 0))

        if tracker_mode == 'TRACK':
            self._target_present_latched = True
            self._target_missing_streak = 0
            self._had_target_in_session = True
        elif tracker_mode == 'LOST':
            self._target_present_latched = True
            self._target_missing_streak += 1
        elif self._target_present_latched:
            self._target_missing_streak += 1
            if self._target_missing_streak >= 8:
                self._target_present_latched = False
        target_present = tracker_mode in {'TRACK', 'LOST'}

        if self._job_state == 'tracking':
            if tracker_mode == 'TRACK':
                if lock_confirmed:
                    self._state_machine.set(UIState.LOCK)
                else:
                    self._state_machine.set(UIState.RUNNING)
            elif tracker_mode == 'LOST':
                self._state_machine.set(UIState.LOST)
            else:
                self._state_machine.set(UIState.RUNNING)
        elif self._job_state == 'evaluating':
            self._state_machine.set(UIState.EVALUATION)
        elif self._job_state == 'stopping':
            self._state_machine.set(UIState.CHECKING)
        else:
            self._state_machine.set(UIState.IDLE)
        self._last_active_id = active_id

        target_count = int(stats.get('target_count', 0))
        visible_count = int(stats.get('visible_target_count', 0))
        bg_visible = max(0, visible_count - (1 if active_id is not None else 0))
        self._last_target_count = target_count
        self.next_target_btn.setEnabled(self._job_state == 'tracking' and target_count > 1)

        if active_id is not None:
            target_value = f'ID {active_id}'
        elif tracker_mode == 'LOST':
            target_value = 'Потеря'
        else:
            target_value = 'Нет цели'

        operator_mode_map = {
            'TRACK': 'Сопровождение (LOCK)' if lock_confirmed else 'Сопровождение (кандидат)',
            'LOST': 'Повторный захват',
            'SCAN': 'Сканирование',
        }
        operator_mode = operator_mode_map.get(tracker_mode, 'Сканирование')

        confidence_pct = int(round(display_confidence * 100.0))
        if tracker_mode == 'TRACK' and lock_confirmed:
            if self._lock_started_at_monotonic is None:
                self._lock_started_at_monotonic = time.monotonic()
        else:
            self._lock_started_at_monotonic = None
        lock_elapsed = 0.0 if self._lock_started_at_monotonic is None else max(0.0, time.monotonic() - self._lock_started_at_monotonic)
        lock_mm = int(lock_elapsed // 60)
        lock_ss = int(lock_elapsed % 60)

        state_card_main = 'LOCK' if (tracker_mode == 'TRACK' and lock_confirmed) else 'IDLE'
        target_card_main = target_value if target_value else '—'
        probability_main = f'{confidence_pct}%'
        runtime_main = f'{lock_mm:02d}:{lock_ss:02d}'
        fps_main = f'{fps:.1f}'
        self._set_target_info_values(state_card_main, target_card_main, probability_main, runtime_main, fps_main)

        for event in stats.get('lock_events', []):
            self._log(f"[f{frame_index + 1}] {event}")

        self._refresh_header_state()

    def _set_target_info_values(self, state_text: str, target_text: str, confidence_text: str, lock_text: str, fps_text: str) -> None:
        self.target_info_state.setText(state_text)
        self.target_info_state.setProperty('state', 'lock' if state_text == 'LOCK' else 'idle')
        self._refresh_widget_style(self.target_info_state)
        self.target_info_id.setText(target_text)
        self.target_info_confidence.setText(confidence_text)
        self.target_info_lock_time.setText(lock_text)
        self.target_info_fps.setText(fps_text)

    def _log(self, message: str):
        self.log_view.appendPlainText(message)
        ts = time.strftime('%H:%M:%S')
        line = f'{ts}  {message}'
        self.bottom_console_label.setText(line[:220])
        self._log_count += 1
        self._refresh_sidebar_meta()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_header_meta_text()
        if self._preview_pixmap is not None:
            self._render_preview_pixmap()

    def _save_app_settings(self):
        self.settings.setValue('window/geometry', self.saveGeometry())
        self.settings.setValue('ui/scenario', self.scenario_combo.currentData())
        self.settings.setValue('ui/workspace', self._current_workspace_key())
        self.settings.setValue('ui/source_type', self.source_type_combo.currentData())
        self.settings.setValue('ui/camera_index', self.camera_index_spin.value())
        self.settings.setValue('ui/source_path', self.source_path_edit.text())
        self.settings.setValue('ui/record_output', self.record_check.isChecked())
        self.settings.setValue('ui/output_path', self.output_edit.text())
        self.settings.setValue('ui/profile_json', json.dumps(self._collect_profile(), ensure_ascii=False))
        self.settings.setValue('ui/ui_v2_enabled', self.ui_v2_enabled)
        self.settings.sync()

    def _load_app_settings(self):
        geometry = self.settings.value('window/geometry')
        if geometry is not None:
            self.restoreGeometry(geometry)

        profile_json = self.settings.value('ui/profile_json', '')
        if profile_json:
            try:
                profile = json.loads(str(profile_json))
                self._set_controls_from_profile(profile)
            except Exception:
                pass

        self._updating_controls = True
        try:
            source_type = self.settings.value('ui/source_type', self.source_type_combo.currentData())
            idx = self.source_type_combo.findData(source_type)
            if idx >= 0:
                self.source_type_combo.setCurrentIndex(idx)

            self.camera_index_spin.setValue(int(self.settings.value('ui/camera_index', self.camera_index_spin.value())))
            self.source_path_edit.setText(str(self.settings.value('ui/source_path', self.source_path_edit.text())))
            self.record_check.setChecked(str(self.settings.value('ui/record_output', 'true')).lower() == 'true')
            self.output_edit.setText(str(self.settings.value('ui/output_path', self.output_edit.text())))

            scenario = self.settings.value('ui/scenario', None)
            if scenario is not None:
                sidx = self.scenario_combo.findData(scenario)
                if sidx >= 0:
                    self.scenario_combo.setCurrentIndex(sidx)

            ui_v2_value = self._to_bool(self.settings.value('ui/ui_v2_enabled', self.ui_v2_enabled), default=self.ui_v2_enabled)
            self._set_ui_v2_enabled(ui_v2_value)
        finally:
            self._updating_controls = False
            self._refresh_record_controls()
            self._on_source_type_changed()
            self._refresh_workspace_overviews()
            self._refresh_sidebar_meta()
            self._refresh_header_state()
            workspace_key = str(self.settings.value('ui/workspace', 'operator'))
            if workspace_key not in self.workspace_indexes:
                workspace_key = 'operator'
            self._on_workspace_selected(workspace_key)

    def closeEvent(self, event):
        self._is_closing = True
        self._save_app_settings()
        self._shutdown_workers()
        event.accept()

    def _shutdown_workers(self):
        if self.worker is not None:
            self.worker.stop()
            deadline = time.monotonic() + 15.0
            while not self.worker.isFinished() and time.monotonic() < deadline:
                self.worker.wait(120)
            if not self.worker.isFinished():
                self.worker.terminate()
                self.worker.wait(1000)

        if self.eval_worker is not None:
            self.eval_worker.stop()
            deadline = time.monotonic() + 20.0
            while not self.eval_worker.isFinished() and time.monotonic() < deadline:
                self.eval_worker.wait(120)
            if not self.eval_worker.isFinished():
                self.eval_worker.terminate()
                self.eval_worker.wait(1000)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    app.aboutToQuit.connect(window._shutdown_workers)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
