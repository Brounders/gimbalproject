import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import cv2
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


APP_STYLESHEET = """
QMainWindow {
    background: #23272B;
    color: #E6EBEF;
}
QWidget {
    color: #E6EBEF;
    font-size: 13px;
    font-family: "Segoe UI", "Noto Sans", "Inter", sans-serif;
}
QWidget#CentralRoot {
    background: #23272B;
}
QMenuBar {
    background: #2B3136;
    color: #AAB4BE;
    border-bottom: 1px solid #3E474F;
}
QMenuBar::item:selected {
    background: #31383E;
}

QFrame#HeaderBar {
    background: #2B3136;
    border: 1px solid #3E474F;
    border-radius: 10px;
}
QLabel#WindowTitle {
    font-size: 17px;
    font-weight: 600;
    color: #E6EBEF;
}
QLabel#HeaderMeta {
    color: #AAB4BE;
    font-size: 13px;
}
QLabel#HeaderStatus {
    border: 1px solid #3E474F;
    border-radius: 8px;
    padding: 5px 10px;
    background: #31383E;
    color: #E6EBEF;
    font-weight: 600;
}
QLabel#HeaderStatus[state="idle"] { background: #31383E; }
QLabel#HeaderStatus[state="running"] { background: #3F5A4C; }
QLabel#HeaderStatus[state="lock"] { background: #5B7183; }
QLabel#HeaderStatus[state="lost"] { background: #9A7B3F; }
QLabel#HeaderStatus[state="stopping"] { background: #5D4F3A; }
QLabel#HeaderStatus[state="evaluating"] { background: #5B7183; }
QLabel#HeaderStatus[state="error"] { background: #7A4141; }

QLabel#RecordIndicator {
    border: 1px solid #3E474F;
    border-radius: 8px;
    padding: 5px 10px;
    background: #31383E;
    color: #AAB4BE;
}
QLabel#RecordIndicator[recording="true"] {
    background: #A24A4A;
    color: #E6EBEF;
    border-color: #A24A4A;
}

QFrame#LeftControlRail {
    background: #2B3136;
    border: 1px solid #3E474F;
    border-radius: 10px;
}
QLabel#RailSectionTitle {
    color: #AAB4BE;
    font-size: 12px;
    font-weight: 600;
}
QLabel#BottomConsoleText {
    color: #AAB4BE;
    font-family: "Consolas", "JetBrains Mono", monospace;
}
QFrame#BottomConsole {
    background: #2B3136;
    border: 1px solid #3E474F;
    border-radius: 8px;
}

QGroupBox {
    border: 1px solid #3E474F;
    border-radius: 10px;
    margin-top: 10px;
    padding-top: 12px;
    background: #2B3136;
    color: #E6EBEF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #AAB4BE;
    font-weight: 600;
    font-size: 12px;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
    background: #31383E;
    color: #E6EBEF;
    border: 1px solid #3E474F;
    border-radius: 8px;
    padding: 6px 8px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {
    border-color: #5B7183;
}

QPushButton {
    background: #31383E;
    color: #E6EBEF;
    border: 1px solid #3E474F;
    border-radius: 8px;
    padding: 7px 11px;
    font-weight: 600;
}
QPushButton:hover { background: #3A4248; }
QPushButton:disabled {
    background: #2A2F34;
    color: #7C8792;
    border-color: #384047;
}
QPushButton[variant="primary"] {
    background: #35654C;
    border-color: #35654C;
}
QPushButton[variant="primary"]:hover {
    background: #3D7358;
}
QPushButton[variant="destructive"] {
    background: #7A4141;
    border-color: #7A4141;
}
QPushButton[variant="destructive"]:hover {
    background: #8B4A4A;
}
QPushButton[variant="ghost"] {
    background: transparent;
    border-color: #3E474F;
    color: #AAB4BE;
}
QPushButton[variant="ghost"]:hover {
    background: #31383E;
    color: #E6EBEF;
}

QCheckBox {
    spacing: 7px;
    color: #E6EBEF;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #3E474F;
    border-radius: 4px;
    background: #31383E;
}
QCheckBox::indicator:checked {
    background: #5B7183;
    border-color: #5B7183;
}

QFrame#VideoStage {
    background: #2B3136;
    border: 1px solid #3E474F;
    border-radius: 10px;
    padding: 8px;
}

QLabel#VideoSurface {
    background: #1F2428;
    color: #AAB4BE;
    border: 1px solid #3E474F;
    border-radius: 10px;
    font-size: 14px;
}

QFrame#InspectorCard {
    background: #31383E;
    border: 1px solid #3E474F;
    border-radius: 8px;
}
QLabel#InspectorTitle {
    color: #AAB4BE;
    font-size: 12px;
    font-weight: 600;
}
QLabel#InspectorValue {
    color: #E6EBEF;
    font-size: 13px;
}

QFrame#TargetInfoCard {
    background: rgba(35, 39, 43, 210);
    border: 1px solid rgba(62, 71, 79, 180);
    border-radius: 8px;
}
QLabel#TargetCardRow {
    color: #E6EBEF;
    font-size: 12px;
}
QLabel#TargetCardState {
    color: #E6EBEF;
    font-size: 12px;
    font-weight: 700;
}
QLabel#TargetCardState[state="lock"] { color: #7FBFAA; }
QLabel#TargetCardState[state="lost"] { color: #CFA85A; }
QLabel#TargetCardState[state="idle"] { color: #AAB4BE; }

QPushButton[active="true"] {
    background: #3F5A4C;
    border-color: #4A7A62;
    color: #E6EBEF;
}
QPushButton[active="true"]:hover {
    background: #4A6B5A;
}
"""

# Canonical operator modes: shown as quick-access buttons in the left rail.
# Mapping: label → (preset_key, night_enabled_override)
# None override means "keep preset default".
CANONICAL_OPERATOR_MODES: dict[str, tuple[str, bool | None]] = {
    'auto':  ('default', None),   # full adaptive detection (night on per default.yaml)
    'day':   ('default', False),  # explicit day-only (night detector disabled)
    'night': ('night', None),     # night preset (force operator display mode)
    'ir':    ('antiuav_thermal', None),  # thermal / anti-UAV preset
}

SCENARIO_LABELS = {
    'default': 'Дневной (базовый)',
    'small_target': 'Малые цели',
    'night': 'Ночной режим',
    'antiuav_thermal': 'Thermal / Anti-UAV',
    'rpi_hailo': 'RPi + Hailo',
    'custom': 'Пользовательский',
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
                if self._switch_target_requested:
                    self._switch_target_requested = False
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
        self._auto_scene_detect_enabled = False
        self._target_lock_start: float | None = None

        self._session_history: list[str] = []
        self._recent_sources: list[str] = []
        self._evaluation_reports: list[str] = []
        self._log_count = 0
        self._preview_pixmap: QPixmap | None = None

        self.settings = QSettings('GimbalProject', 'UAVTrackerApp')

        self.setWindowTitle('Система сопровождения БПЛА')
        self.resize(1520, 980)
        self.setMinimumSize(1360, 860)
        self.setStyleSheet(APP_STYLESHEET)
        self._build_ui()
        self._wire_actions()
        self._apply_defaults()
        self._load_app_settings()

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
        body_splitter.setSizes([280, 1040])
        root.addWidget(body_splitter, 1)

        root.addWidget(self.build_bottom_console())

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.document().setMaximumBlockCount(500)
        self.logs_workspace_view = self.log_view

        self.top_scenario_label = self.header_source_label
        self.console_status_label = self.bottom_console_label

        self.build_expert_dialog()
        self._refresh_workspace_overviews()

        quit_action = QAction('Выход', self)
        quit_action.triggered.connect(self.close)
        self.menuBar().addAction(quit_action)

    def build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName('HeaderBar')
        header.setMinimumHeight(60)
        header.setMaximumHeight(66)

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

        self.header_source_label = QLabel('Источник: CAM 0')
        self.header_source_label.setObjectName('HeaderMeta')
        layout.addWidget(self.header_source_label, 1)

        self.record_indicator_label = QLabel('REC OFF')
        self.record_indicator_label.setObjectName('RecordIndicator')
        self.record_indicator_label.setProperty('recording', False)
        layout.addWidget(self.record_indicator_label)

        self.next_target_btn = QPushButton('Следующая цель')
        self.next_target_btn.setProperty('variant', 'ghost')
        self.next_target_btn.setToolTip('Переключить на следующую доступную цель')
        self.next_target_btn.setEnabled(False)
        layout.addWidget(self.next_target_btn)

        self.expert_btn = QPushButton('Эксперт')
        self.expert_btn.setProperty('variant', 'ghost')
        layout.addWidget(self.expert_btn)

        self.expert_badge = QLabel('EXP')
        self.expert_badge.setObjectName('HeaderMeta')
        self.expert_badge.setVisible(False)
        layout.addWidget(self.expert_badge)

        self.fullscreen_btn = QPushButton('⛶')
        self.fullscreen_btn.setFixedWidth(34)
        self.fullscreen_btn.setProperty('variant', 'ghost')
        self.fullscreen_btn.setToolTip('Полный экран')
        layout.addWidget(self.fullscreen_btn)

        self.start_btn = QPushButton('Старт')
        self.start_btn.setProperty('variant', 'primary')
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton('Стоп')
        self.stop_btn.setProperty('variant', 'destructive')
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        return header

    def build_left_rail(self) -> QWidget:
        rail = QFrame()
        rail.setObjectName('LeftControlRail')
        rail.setMinimumWidth(280)
        rail.setMaximumWidth(310)
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel('Операционное управление')
        title.setObjectName('RailSectionTitle')
        layout.addWidget(title)

        self.quick_auto_btn = QPushButton('Авто')
        self.quick_auto_btn.setProperty('variant', 'ghost')
        self.quick_day_btn = QPushButton('День')
        self.quick_day_btn.setProperty('variant', 'ghost')
        self.quick_night_btn = QPushButton('Ночь')
        self.quick_night_btn.setProperty('variant', 'ghost')
        self.quick_ir_btn = QPushButton('IR')
        self.quick_ir_btn.setProperty('variant', 'ghost')
        self.quick_auto_btn.setToolTip('Авто: адаптивный день/ночь (default preset, ночной детектор вкл.)')
        self.quick_day_btn.setToolTip('День: только дневной режим (ночной детектор выкл.)')
        self.quick_night_btn.setToolTip('Ночь: ночной preset в операторском режиме')
        self.quick_ir_btn.setToolTip('IR: thermal / Anti-UAV preset')

        quick_row = QHBoxLayout()
        quick_row.setContentsMargins(0, 0, 0, 0)
        quick_row.setSpacing(4)
        quick_row.addWidget(self.quick_auto_btn)
        quick_row.addWidget(self.quick_day_btn)
        quick_row.addWidget(self.quick_night_btn)
        quick_row.addWidget(self.quick_ir_btn)
        layout.addLayout(quick_row)

        self.source_type_combo = QComboBox()
        self.source_type_combo.addItem('Камера', 'camera')
        self.source_type_combo.addItem('Видео', 'video')
        self.source_type_combo.addItem('Поток', 'stream')
        layout.addWidget(self.source_type_combo)

        self.camera_index_spin = QSpinBox()
        self.camera_index_spin.setRange(0, 16)
        self.camera_index_spin.setValue(0)
        layout.addWidget(self.camera_index_spin)

        self.source_path_label = QLabel('Видео файл')
        self.source_path_label.setObjectName('RailSectionTitle')
        layout.addWidget(self.source_path_label)

        self.source_path_edit = QLineEdit('')
        self.source_path_edit.setPlaceholderText('/путь/к/видео.mp4')
        layout.addWidget(self.source_path_edit)

        self.source_browse_btn = QPushButton('Выбрать...')
        layout.addWidget(self.source_browse_btn)

        self.record_check = QCheckBox('Сохранять видео')
        self.record_check.setChecked(True)
        layout.addWidget(self.record_check)

        self.output_path_label = QLabel('Выход')
        self.output_path_label.setObjectName('RailSectionTitle')
        layout.addWidget(self.output_path_label)

        self.output_edit = QLineEdit(str(ROOT / 'runs' / 'gui_output.mp4'))
        layout.addWidget(self.output_edit)

        self.output_browse_btn = QPushButton('Куда сохранить...')
        layout.addWidget(self.output_browse_btn)

        self.eval_btn = QPushButton('Оценка')
        layout.addWidget(self.eval_btn)

        self.inspector_module = self.build_inspector_drawer()
        self.inspector_module.setVisible(False)
        layout.addWidget(self.inspector_module, 1)

        layout.addStretch(1)
        return rail

    def build_video_stage(self) -> QWidget:
        self.video_stage = VideoStage()
        self.video_label = self.video_stage.surface
        self.target_info_card = self._build_target_info_card()
        self.video_stage.add_overlay_top_right(self.target_info_card)
        return self.video_stage

    def _build_target_info_card(self) -> QFrame:
        from PySide6.QtWidgets import QGridLayout
        card = QFrame()
        card.setObjectName('TargetInfoCard')
        card.setMinimumWidth(170)
        grid = QGridLayout(card)
        grid.setContentsMargins(10, 8, 10, 8)
        grid.setSpacing(3)

        def _row(label_text: str):
            lbl = QLabel(label_text)
            lbl.setObjectName('TargetCardRow')
            val = QLabel('—')
            val.setObjectName('TargetCardRow')
            return lbl, val

        lbl_id, self._tc_id = _row('Цель')
        lbl_conf, self._tc_conf = _row('Уверенность')
        lbl_fps, self._tc_fps = _row('FPS')
        lbl_time, self._tc_time = _row('На цели')

        self._tc_state = QLabel('IDLE')
        self._tc_state.setObjectName('TargetCardState')
        self._tc_state.setProperty('state', 'idle')

        for row_i, (lbl, val) in enumerate([(lbl_id, self._tc_id), (lbl_conf, self._tc_conf),
                                             (lbl_fps, self._tc_fps), (lbl_time, self._tc_time)]):
            grid.addWidget(lbl, row_i, 0)
            grid.addWidget(val, row_i, 1)
        grid.addWidget(self._tc_state, 4, 0, 1, 2)
        return card

    def build_bottom_console(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName('BottomConsole')
        bar.setMinimumHeight(32)
        bar.setMaximumHeight(36)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        self.bottom_console_label = QLabel('$ готово к запуску')
        self.bottom_console_label.setObjectName('BottomConsoleText')
        self.bottom_console_label.setWordWrap(False)
        layout.addWidget(self.bottom_console_label, 1)
        return bar

    def _build_inspector_card(self, title: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName('InspectorCard')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        header = QLabel(title)
        header.setObjectName('InspectorTitle')
        layout.addWidget(header)
        value = QLabel('-')
        value.setObjectName('InspectorValue')
        value.setWordWrap(True)
        layout.addWidget(value)
        return card, value

    def build_inspector_drawer(self) -> QWidget:
        body = QGroupBox('Диагностика')
        body.setObjectName('InspectorModule')
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(8, 8, 8, 8)
        body_layout.setSpacing(8)

        target_card, self.panel_target_summary = self._build_inspector_card('Цель')
        quality_card, self.panel_quality_summary = self._build_inspector_card('Качество')
        runtime_card, self.panel_monitoring_summary = self._build_inspector_card('Runtime health')
        params_card, self.panel_params_summary = self._build_inspector_card('Параметры')
        eval_card, self.eval_summary_label = self._build_inspector_card('Оценка')
        self.eval_summary_hint = QLabel('-')
        self.eval_summary_hint.setObjectName('InspectorValue')
        eval_card.layout().addWidget(self.eval_summary_hint)

        events_card = QFrame()
        events_card.setObjectName('InspectorCard')
        events_layout = QVBoxLayout(events_card)
        events_layout.setContentsMargins(8, 8, 8, 8)
        events_layout.setSpacing(4)
        events_title = QLabel('События')
        events_title.setObjectName('InspectorTitle')
        events_layout.addWidget(events_title)
        self.panel_events_view = QPlainTextEdit()
        self.panel_events_view.setReadOnly(True)
        self.panel_events_view.setMaximumBlockCount(120)
        self.panel_events_view.setMaximumHeight(180)
        events_layout.addWidget(self.panel_events_view)

        body_layout.addWidget(target_card)
        body_layout.addWidget(quality_card)
        body_layout.addWidget(runtime_card)
        body_layout.addWidget(params_card)
        body_layout.addWidget(eval_card)
        body_layout.addWidget(events_card, 1)
        return body

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

    def _on_expert_dialog_closed(self):
        self.expert_badge.setVisible(False)
        self.expert_btn.setProperty('variant', 'ghost')
        self._refresh_widget_style(self.expert_btn)

    def _hide_expert_dialog(self):
        self.expert_dialog.hide()
        self._on_expert_dialog_closed()

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

    def _fill_scenarios(self):
        available = set(available_presets())
        ordered = [
            'default',
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

        self.next_target_btn.clicked.connect(self._request_next_target)
        self.expert_btn.clicked.connect(self._toggle_expert_mode)
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        self.model_browse_btn.clicked.connect(self._browse_model)

        self.scenario_combo.currentIndexChanged.connect(self._on_scenario_changed)
        self.quick_auto_btn.clicked.connect(lambda: self._apply_canonical_operator_mode('auto'))
        self.quick_day_btn.clicked.connect(lambda: self._apply_canonical_operator_mode('day'))
        self.quick_night_btn.clicked.connect(lambda: self._apply_canonical_operator_mode('night'))
        self.quick_ir_btn.clicked.connect(lambda: self._apply_canonical_operator_mode('ir'))
        self.mode_combo.currentTextChanged.connect(self._apply_runtime_mode_controls)
        self.apply_preset_btn.clicked.connect(self._apply_selected_preset)
        self.profile_load_btn.clicked.connect(self._load_profile_from_disk)
        self.profile_save_btn.clicked.connect(self._save_profile_to_disk)

        self.start_btn.clicked.connect(self._start)
        self.stop_btn.clicked.connect(self._stop)
        self.eval_btn.clicked.connect(self._evaluate)

        self.command_palette_shortcut = QShortcut(QKeySequence('Ctrl+K'), self)
        self.command_palette_shortcut.activated.connect(self._open_command_palette)

    def _apply_defaults(self):
        self.mode_combo.setCurrentText('research')
        self._apply_runtime_mode_controls('research')
        idx = self.scenario_combo.findData('default')
        if idx >= 0:
            self.scenario_combo.setCurrentIndex(idx)
            self._on_scenario_changed()
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
            '2) Выберите режим камеры (Авто/День/Ночь/IR).\n'
            '3) Нажмите Старт.\n\n'
            'Экспертные настройки открываются отдельным окном.',
        )

    def _open_command_palette(self):
        items = ['Старт', 'Стоп', 'Оценка', 'Экспертные настройки']
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

        source_type = str(self.source_type_combo.currentData() or 'camera')
        if source_type == 'camera':
            source_display = f"CAM {self.camera_index_spin.value()}"
        elif source_type == 'stream':
            source_display = 'ПОТОК'
        else:
            source_display = 'ВИДЕО'
        source_hint = str(self.source_path_edit.text().strip() or source_display)
        if source_type == 'video':
            source_short = Path(source_hint).name or source_display
        elif source_type == 'stream':
            source_short = source_hint[:48]
        else:
            source_short = source_display

        self.top_scenario_label.setText(f"Источник: {source_short} | Сцена: {scenario_label}")

        state_map = {
            UIState.IDLE: ('IDLE', 'idle'),
            UIState.CHECKING: ('CHECK', 'stopping'),
            UIState.RUNNING: ('RUNNING', 'running'),
            UIState.LOCK: ('LOCK', 'lock'),
            UIState.LOST: ('LOST', 'lost'),
            UIState.EVALUATION: ('EVALUATE', 'evaluating'),
            UIState.ERROR: ('ERROR', 'error'),
        }
        state_text, state_name = state_map.get(self._state_machine.state, ('IDLE', 'idle'))
        self.top_state_badge.setText(state_text)
        self.top_state_badge.setProperty('state', state_name)
        self._refresh_widget_style(self.top_state_badge)

        readable_state = {
            UIState.IDLE: 'Ожидание',
            UIState.CHECKING: 'Остановка',
            UIState.RUNNING: 'Сканирование',
            UIState.LOCK: 'Захват',
            UIState.LOST: 'Потеря',
            UIState.EVALUATION: 'Оценка',
            UIState.ERROR: 'Ошибка',
        }
        self.console_status_label.setText(
            f"$ {readable_state.get(self._state_machine.state, 'Ожидание').lower()} // {source_display.lower()} // {source_hint}"
        )

        recording = self._job_state in {'tracking', 'stopping'} and self.record_check.isChecked()
        if recording:
            self.record_indicator_label.setText('REC ON')
        elif self.record_check.isChecked():
            self.record_indicator_label.setText('REC READY')
        else:
            self.record_indicator_label.setText('REC OFF')
        self.record_indicator_label.setProperty('recording', recording)
        self._refresh_widget_style(self.record_indicator_label)

        self.panel_params_summary.setText(
            'Сценарий: '
            f"{scenario_label}\n"
            f"Источник: {self.source_type_combo.currentText()} | device: {self.device_combo.currentText()}\n"
            f"imgsz/conf: {self.imgsz_spin.value()} / {self.conf_spin.value():.2f}"
        )

    def _video_idle_text(self, detail: str | None = None) -> str:
        base = 'Операторская сцена пока не активна'
        steps = '1) Выбери источник\n2) Примени сценарий\n3) Нажми Старт'
        if detail:
            return f'{detail}\n\n{steps}'
        return f'{base}\n\n{steps}'

    def _set_video_idle_state(self, detail: str | None = None) -> None:
        self._preview_pixmap = None
        self.video_label.clear()
        self.video_label.setText(self._video_idle_text(detail))

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
        self.expert_badge.setVisible(True)
        self.expert_btn.setProperty('variant', 'primary')
        self._refresh_widget_style(self.expert_btn)

    def _request_next_target(self) -> None:
        if self.worker is not None and self._job_state == 'tracking':
            self.worker.request_switch_target()

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

    def _apply_canonical_operator_mode(self, mode_key: str) -> None:
        """Apply one of the 4 canonical operator modes: auto/day/night/ir.

        Each mode loads the mapped preset and applies operator-safe display
        overrides so that operator buttons never activate research-mode HUD.
        """
        entry = CANONICAL_OPERATOR_MODES.get(mode_key)
        if entry is None:
            self._log(f'Неизвестный канонический режим: {mode_key}')
            return
        preset_key, night_override = entry
        self._apply_scenario_preset(preset_key)
        # Force operator display settings (suppress research-only overlays)
        if not self._updating_controls:
            self._updating_controls = True
            try:
                if self.mode_combo.findText('operator') >= 0:
                    self.mode_combo.setCurrentText('operator')
                self.show_gt_check.setChecked(False)
                self.timing_check.setChecked(False)
                self.show_trails_check.setChecked(False)
                if night_override is not None:
                    self.night_check.setChecked(night_override)
            finally:
                self._updating_controls = False
        self._auto_scene_detect_enabled = (mode_key == 'auto')
        labels = {'auto': 'Авто', 'day': 'День', 'night': 'Ночь', 'ir': 'IR'}
        self._log(f'Режим оператора: {labels.get(mode_key, mode_key)}')
        # Highlight active mode button (TASK-024)
        mode_btns = {
            'auto': self.quick_auto_btn, 'day': self.quick_day_btn,
            'night': self.quick_night_btn, 'ir': self.quick_ir_btn,
        }
        for key, btn in mode_btns.items():
            btn.setProperty('active', key == mode_key)
            self._refresh_widget_style(btn)

    def _apply_scenario_preset(self, preset_key: str):
        cfg, data = load_preset(preset_key, Config())
        profile = {
            'preset': preset_key,
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
                'record_output', 'output_path'
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

        cfg = apply_runtime_mode(Config(), self.mode_combo.currentText())
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
        cfg.AUTO_SCENE_DETECT = bool(getattr(self, '_auto_scene_detect_enabled', False))
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
            self.quick_day_btn,
            self.quick_night_btn,
            self.quick_ir_btn,
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
        self._refresh_record_controls()

        if state == 'idle':
            self._target_present_latched = False
            self._target_missing_streak = 0
            self._had_target_in_session = False

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

        scenario_key = str(self.scenario_combo.currentData() or 'custom')
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
        self.console_status_label.setText('$ запуск // подключение к источнику')
        source_descriptor = f"camera:{source}" if isinstance(source, int) else str(source)
        self._session_history.append(f"{ts} | {scenario_key} | {source_descriptor}")
        if source_descriptor not in self._recent_sources:
            self._recent_sources.append(source_descriptor)
        self._refresh_workspace_overviews()
        self._refresh_sidebar_meta()
        self._log(
            f'Старт: source={source} mode={cfg.RUNTIME_MODE} device={cfg.DEVICE} '
            f'imgsz={cfg.IMG_SIZE} conf={cfg.CONF_THRESH:.2f} '
            f'adaptive={cfg.ADAPTIVE_SCAN_ENABLED} lock_tracker={cfg.LOCK_TRACKER_ENABLED}'
        )
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
            self.console_status_label.setText('$ остановлено // поток завершен')
        elif reason == 'eof':
            self._log('Сессия завершена: поток закончился.')
            self._set_video_idle_state('Источник закончился. Поток не активен.')
            self.console_status_label.setText('$ завершено // источник исчерпан')
        else:
            self._log(f'Сессия завершена: {reason}')
            self._set_video_idle_state(f'Сессия завершена: {reason}')
            self.console_status_label.setText('$ завершено // см. журнал')
        self.worker = None
        self._set_job_state('idle')

    def _on_eval_finished(self, reason: str):
        self.eval_worker = None
        self._set_job_state('idle')
        if reason == 'stopped':
            self._log('Оценка остановлена пользователем.')
            self._set_video_idle_state('Оценка остановлена. Поток не активен.')
            self.console_status_label.setText('$ оценка остановлена')
        else:
            self._log('Оценка завершена.')
            self._set_video_idle_state('Оценка завершена. Поток не активен.')
            self.console_status_label.setText('$ оценка завершена')

    def _on_failed(self, message: str):
        self.worker = None
        self.eval_worker = None
        self._set_job_state('idle')
        self._state_machine.set(UIState.ERROR)
        self._refresh_header_state()
        self._set_video_idle_state('Ошибка потока. Проверь журнал и конфигурацию.')
        self.console_status_label.setText('$ ошибка // открой журнал')
        self._log(f'Ошибка: {message}')
        if not self._is_closing:
            QMessageBox.critical(self, 'Ошибка', message)

    def _on_eval_report(self, report: dict):
        self.eval_summary_label.setText(
            f"lock {report['lock_frames']}/{report['gt_frames']} | IoU {report['avg_gt_iou']:.3f} | fps {report['avg_fps']:.1f}"
        )
        self.eval_summary_hint.setText(
            f"false {report['false_alarm_frames']} | cont {report.get('continuity_score', 0.0) * 100.0:.1f}% | sw/min {report.get('lock_switches_per_min', 0.0):.2f}"
        )
        self.console_status_label.setText('$ оценка // отчет готов')
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
        budget_level = int(stats.get('budget_level', 0))
        budget_load = float(stats.get('budget_load') or 0.0)
        budget_frame_ms = float(stats.get('budget_frame_ms') or 0.0)
        roi_budget_candidates = int(stats.get('roi_budget_candidates', 0))
        night_skip = int(stats.get('night_skip', 0))
        scan_strategy = str(stats.get('scan_strategy', '-'))

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
                self._state_machine.set(UIState.LOCK)
            elif tracker_mode == 'LOST':
                self._state_machine.set(UIState.LOST)
            elif self._target_present_latched and self._target_missing_streak < 3:
                # Brief SCAN while recently latched: hold LOCK badge to avoid flicker.
                self._state_machine.set(UIState.LOCK)
            else:
                self._state_machine.set(UIState.RUNNING)
        elif self._job_state == 'evaluating':
            self._state_machine.set(UIState.EVALUATION)
        elif self._job_state == 'stopping':
            self._state_machine.set(UIState.CHECKING)
        else:
            self._state_machine.set(UIState.IDLE)
        self._last_active_id = active_id

        state_value_map = {
            UIState.IDLE: 'Ожидание',
            UIState.CHECKING: 'Остановка',
            UIState.RUNNING: 'Сканирование',
            UIState.LOCK: 'Захват',
            UIState.LOST: 'Повторный захват',
            UIState.EVALUATION: 'Оценка',
            UIState.ERROR: 'Ошибка',
        }
        state_value = state_value_map.get(self._state_machine.state, 'Ожидание')

        target_count = int(stats.get('target_count', 0))
        visible_count = int(stats.get('visible_target_count', 0))
        bg_visible = max(0, visible_count - (1 if active_id is not None else 0))

        if active_id is not None:
            target_value = f'ID {active_id}'
        elif tracker_mode == 'LOST':
            target_value = 'Потеря'
        else:
            target_value = 'Нет цели'

        operator_mode_map = {
            'TRACK': 'Сопровождение',
            'LOST': 'Повторный захват',
            'SCAN': 'Сканирование',
        }
        operator_mode = operator_mode_map.get(tracker_mode, 'Сканирование')

        confidence_pct = int(round(display_confidence * 100.0))
        continuity_pct = continuity_score * 100.0
        active_presence_pct = active_presence_rate * 100.0
        if gt_visible:
            quality_main = f'IoU {gt_iou:.3f} | conf {confidence_pct}%'
        else:
            quality_main = f'conf {confidence_pct}% | cont {continuity_pct:.1f}%'

        perf_value = budget_frame_ms if budget_frame_ms > 0 else float(timings.get('global', 0.0) or 0.0)
        self.console_status_label.setText(
            f"$ {state_value.lower()} // {target_value.lower()} // {operator_mode.lower()}"
        )

        self.panel_runtime_summary = (
            f"FPS: {fps:.1f}\n"
            f"Состояние: {state_value}\n"
            f"Режим: {operator_mode} | кадр {frame_index + 1}\n"
            f"Budget L{budget_level} load={budget_load:.2f} frame={perf_value:.1f}ms\n"
            f"Continuity {continuity_pct:.1f}% | Presence {active_presence_pct:.1f}%\n"
            f"G {float(timings.get('global', 0.0) or 0.0):.1f} | "
            f"L {float(timings.get('local', 0.0) or 0.0):.1f} | "
            f"ROI {float(timings.get('roi', 0.0) or 0.0):.1f} | "
            f"N {float(timings.get('night', 0.0) or 0.0):.1f}"
        )
        self.panel_monitoring_summary.setText(self.panel_runtime_summary)
        self.panel_target_summary.setText(
            f"Цель: {'ID ' + str(active_id) if active_id is not None else ('временная потеря' if target_present else 'не обнаружена')}\n"
            f"Источник: {active_source}\n"
            f"Lock score: {lock_score:.2f} | strategy: {scan_strategy}"
        )
        self.panel_quality_summary.setText(
            f"{quality_main}\n"
            f"sw/min {lock_switches_per_min:.2f} ({lock_switch_count}) | "
            f"roi cand {roi_budget_candidates} | night skip {night_skip}\n"
            f"видимые цели: {visible_count}, всего: {target_count}, фон: {bg_visible}"
        )

        for event in stats.get('lock_events', []):
            self._log(f"[f{frame_index + 1}] {event}")
            self.panel_events_view.appendPlainText(f"[f{frame_index + 1}] {event}")

        # Update target info card overlay (TASK-023)
        if tracker_mode == 'TRACK' and active_id is not None:
            if self._target_lock_start is None:
                self._target_lock_start = time.perf_counter()
            elapsed = time.perf_counter() - self._target_lock_start
            elapsed_str = f'{int(elapsed // 60):02d}:{int(elapsed % 60):02d}'
            card_state, card_state_key = 'LOCK', 'lock'
        elif tracker_mode == 'LOST':
            elapsed_str = '—'
            card_state, card_state_key = 'ПОТЕРЯ', 'lost'
        else:
            self._target_lock_start = None
            elapsed_str = '—'
            card_state, card_state_key = 'IDLE', 'idle'
        self._tc_id.setText(f'ID {active_id}' if active_id is not None else '—')
        self._tc_conf.setText(f'{confidence_pct}%')
        self._tc_fps.setText(f'{fps:.1f}')
        self._tc_time.setText(elapsed_str)
        self._tc_state.setText(card_state)
        self._tc_state.setProperty('state', card_state_key)
        self._refresh_widget_style(self._tc_state)
        # Enable/disable Next Target button
        self.next_target_btn.setEnabled(self._job_state == 'tracking' and target_count > 1)

        self._refresh_header_state()

    def _log(self, message: str):
        self.log_view.appendPlainText(message)
        ts = time.strftime('%H:%M:%S')
        line = f'{ts}  {message}'
        self.bottom_console_label.setText(line[:220])
        self._log_count += 1
        self._refresh_sidebar_meta()

    def resizeEvent(self, event):
        super().resizeEvent(event)
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
            self.inspector_module.setVisible(False)  # always hidden in operator layer

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
