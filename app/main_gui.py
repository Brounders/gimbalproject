import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import cv2
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from uav_tracker.config import Config
from uav_tracker.modes import apply_runtime_mode
from uav_tracker.pipeline import apply_runtime_preset, parse_video_source
from uav_tracker.profile_io import apply_overrides, available_presets
from app.ui import UIState, UIStateMachine, VideoStage
from app.ui.theme import APP_STYLESHEET, refresh_widget_style
from app.ui.cards import build_target_info_card
from app.app_settings import load_app_settings as _load_app_settings_impl, save_app_settings as _save_app_settings_impl
from app.profile_controller import (
    CANONICAL_OPERATOR_MODES,
    apply_canonical_operator_mode as _apply_canonical_operator_mode_impl,
    apply_quick_profile as _apply_quick_profile_impl,
    apply_runtime_mode_controls as _apply_runtime_mode_controls_impl,
    apply_scenario_preset as _apply_scenario_preset_impl,
    apply_selected_preset as _apply_selected_preset_impl,
    collect_profile as _collect_profile_impl,
    load_profile_from_disk as _load_profile_from_disk_impl,
    save_profile_to_disk as _save_profile_to_disk_impl,
    set_controls_from_profile as _set_controls_from_profile_impl,
)
from app.job_state_machine import refresh_header_state as _refresh_header_state_impl, set_job_state as _set_job_state_impl
from app.source_controller import on_source_type_changed as _on_source_type_changed_impl, source_from_controls as _source_from_controls_impl, split_source as _split_source_impl
from app.stats_renderer import update_stats as _update_stats_impl
from app.ui.expert_dialog import build_expert_dialog as _build_expert_dialog
from app.ui.layout_builders import build_header as _build_header, build_inspector_drawer as _build_inspector_drawer, build_left_rail as _build_left_rail
from app.workers import EvaluationWorker, TrackerWorker


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
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        self._workspace_order = ['operator']
        self.workspace_indexes = {'operator': 0}
        self.sidebar_buttons = {}

        # ── Top pill (centred) ──────────────────────────────────────────────
        topbar_row = QHBoxLayout()
        topbar_row.setContentsMargins(0, 0, 0, 0)
        topbar_row.addStretch(1)
        topbar_row.addWidget(self.build_topbar())
        topbar_row.addStretch(1)
        root.addLayout(topbar_row)

        # ── Body: left | video | right ──────────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(12)
        body.addWidget(self.build_left_rail(), 0)
        body.addWidget(self.build_video_stage(), 1)
        body.addWidget(self.build_right_panel(), 0)
        root.addLayout(body, 1)

        # ── Dock pill (centred) ─────────────────────────────────────────────
        dock_row = QHBoxLayout()
        dock_row.setContentsMargins(0, 0, 0, 0)
        dock_row.addStretch(1)
        dock_row.addWidget(self.build_dock())
        dock_row.addStretch(1)
        root.addLayout(dock_row)

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

    def build_topbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName('TopBar')

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(14)

        # Brand
        brand_name = QLabel('GIMBAL')
        brand_name.setObjectName('BrandName')
        brand_sub = QLabel('система сопровождения')
        brand_sub.setObjectName('BrandSub')
        layout.addWidget(brand_name)
        layout.addWidget(brand_sub)

        sep1 = QLabel()
        sep1.setObjectName('TopBarSep')
        layout.addWidget(sep1)

        # Mode selector (EO / IR / NV) maps to quick mode buttons
        mode_frame = QFrame()
        mode_frame.setObjectName('ModeSelector')
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(3, 3, 3, 3)
        mode_layout.setSpacing(2)

        self.quick_auto_btn = QPushButton('АВТО')
        self.quick_day_btn  = QPushButton('ДЕНЬ')
        self.quick_night_btn = QPushButton('НОЧЬ')
        self.quick_ir_btn   = QPushButton('IR')
        for btn in (self.quick_auto_btn, self.quick_day_btn,
                    self.quick_night_btn, self.quick_ir_btn):
            btn.setObjectName('ModeBtn')
            mode_layout.addWidget(btn)
        self.quick_auto_btn.setProperty('active', 'true')
        refresh_widget_style(self.quick_auto_btn)

        layout.addWidget(mode_frame)

        sep2 = QLabel()
        sep2.setObjectName('TopBarSep')
        layout.addWidget(sep2)

        # Status badge
        self.top_state_badge = QLabel('IDLE')
        self.top_state_badge.setObjectName('HeaderStatus')
        self.top_state_badge.setProperty('state', 'idle')
        layout.addWidget(self.top_state_badge)

        # Source / scenario label
        self.header_source_label = QLabel('CAM 0')
        self.header_source_label.setObjectName('BrandSub')
        layout.addWidget(self.header_source_label)

        sep3 = QLabel()
        sep3.setObjectName('TopBarSep')
        layout.addWidget(sep3)

        # Record indicator
        self.record_indicator_label = QLabel('● REC')
        self.record_indicator_label.setObjectName('RecordIndicator')
        self.record_indicator_label.setProperty('recording', False)
        layout.addWidget(self.record_indicator_label)

        sep4 = QLabel()
        sep4.setObjectName('TopBarSep')
        layout.addWidget(sep4)

        # Expert button
        self.expert_btn = QPushButton('Эксперт')
        self.expert_btn.setObjectName('ModeBtn')
        layout.addWidget(self.expert_btn)

        self.expert_badge = QLabel('EXP')
        self.expert_badge.setObjectName('ChipAccent')
        self.expert_badge.setVisible(False)
        layout.addWidget(self.expert_badge)

        # Fullscreen
        self.fullscreen_btn = QPushButton('⛶')
        self.fullscreen_btn.setObjectName('ModeBtn')
        self.fullscreen_btn.setFixedWidth(34)
        self.fullscreen_btn.setToolTip('Полный экран')
        layout.addWidget(self.fullscreen_btn)

        # Next target (hidden until tracking)
        self.next_target_btn = QPushButton('↕ Цель')
        self.next_target_btn.setObjectName('ModeBtn')
        self.next_target_btn.setToolTip('Следующая цель')
        self.next_target_btn.setEnabled(False)
        layout.addWidget(self.next_target_btn)

        sep5 = QLabel()
        sep5.setObjectName('TopBarSep')
        layout.addWidget(sep5)

        # Clock
        from PySide6.QtCore import QTimer, QTime
        self._clock_label = QLabel(QTime.currentTime().toString('HH:mm'))
        self._clock_label.setObjectName('TopBarClock')
        layout.addWidget(self._clock_label)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(
            lambda: self._clock_label.setText(QTime.currentTime().toString('HH:mm'))
        )
        self._clock_timer.start(30_000)

        return bar

    def build_left_rail(self) -> QWidget:
        rail = QFrame()
        rail.setObjectName('LeftControlRail')
        rail.setFixedWidth(260)

        layout = QVBoxLayout(rail)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # ── Source panel ────────────────────────────────────────────────────
        src_panel = QFrame()
        src_panel.setObjectName('GlassPanel')
        src_layout = QVBoxLayout(src_panel)
        src_layout.setContentsMargins(14, 14, 14, 14)
        src_layout.setSpacing(8)

        src_title = QLabel('ИСТОЧНИК')
        src_title.setObjectName('RailSectionTitle')
        src_layout.addWidget(src_title)

        self.source_type_combo = QComboBox()
        self.source_type_combo.addItem('Камера', 'camera')
        self.source_type_combo.addItem('Видео', 'video')
        self.source_type_combo.addItem('Поток', 'stream')
        src_layout.addWidget(self.source_type_combo)

        self.camera_index_spin = QSpinBox()
        self.camera_index_spin.setRange(0, 16)
        self.camera_index_spin.setValue(0)
        src_layout.addWidget(self.camera_index_spin)

        self.source_path_label = QLabel('Видео файл')
        self.source_path_label.setObjectName('RailSectionTitle')
        src_layout.addWidget(self.source_path_label)

        self.source_path_edit = QLineEdit('')
        self.source_path_edit.setPlaceholderText('/путь/к/видео.mp4')
        src_layout.addWidget(self.source_path_edit)

        self.source_browse_btn = QPushButton('Выбрать...')
        src_layout.addWidget(self.source_browse_btn)

        layout.addWidget(src_panel)

        # ── Record panel ────────────────────────────────────────────────────
        rec_panel = QFrame()
        rec_panel.setObjectName('GlassPanel')
        rec_layout = QVBoxLayout(rec_panel)
        rec_layout.setContentsMargins(14, 14, 14, 14)
        rec_layout.setSpacing(8)

        rec_title = QLabel('ЗАПИСЬ')
        rec_title.setObjectName('RailSectionTitle')
        rec_layout.addWidget(rec_title)

        self.record_check = QCheckBox('Сохранять видео')
        self.record_check.setChecked(True)
        rec_layout.addWidget(self.record_check)

        self.output_path_label = QLabel('Путь')
        self.output_path_label.setObjectName('RailSectionTitle')
        rec_layout.addWidget(self.output_path_label)

        self.output_edit = QLineEdit(str(ROOT / 'runs' / 'gui_output.mp4'))
        rec_layout.addWidget(self.output_edit)

        self.output_browse_btn = QPushButton('Куда сохранить...')
        rec_layout.addWidget(self.output_browse_btn)

        self.eval_btn = QPushButton('Оценка')
        self.eval_btn.setProperty('variant', 'ghost')
        rec_layout.addWidget(self.eval_btn)

        layout.addWidget(rec_panel)

        layout.addStretch(1)
        return rail

    def build_video_stage(self) -> QWidget:
        self.video_stage = VideoStage()
        self.video_label = self.video_stage.surface
        (self.target_info_card, self._tc_id, self._tc_conf,
         self._tc_fps, self._tc_time, self._tc_state) = build_target_info_card()
        self.video_stage.add_overlay_top_right(self.target_info_card)
        return self.video_stage

    def build_right_panel(self) -> QWidget:
        col = QFrame()
        col.setObjectName('LeftControlRail')
        col.setFixedWidth(340)

        layout = QVBoxLayout(col)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # ── Active target card ──────────────────────────────────────────────
        card = QFrame()
        card.setObjectName('ActiveTargetCard')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        # Header row: live badge + id
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        self._rp_live_badge = QLabel('● LOCK')
        self._rp_live_badge.setObjectName('LiveBadge')
        self._rp_id_label = QLabel('—')
        self._rp_id_label.setObjectName('ActiveTargetId')
        hdr.addWidget(self._rp_live_badge)
        hdr.addWidget(self._rp_id_label)
        hdr.addStretch(1)
        self._rp_state_chip = QLabel('IDLE')
        self._rp_state_chip.setObjectName('ChipWarn')
        hdr.addWidget(self._rp_state_chip)
        card_layout.addLayout(hdr)

        # Name + sub
        self._rp_name_label = QLabel('Нет цели')
        self._rp_name_label.setObjectName('ActiveTargetName')
        self._rp_sub_label = QLabel('ожидание...')
        self._rp_sub_label.setObjectName('ActiveTargetSub')
        card_layout.addWidget(self._rp_name_label)
        card_layout.addWidget(self._rp_sub_label)

        # 3-metric grid: conf / fps / source
        metrics = QHBoxLayout()
        metrics.setContentsMargins(0, 0, 0, 0)
        metrics.setSpacing(0)
        self._rp_conf_key  = QLabel('УВЕРЕН')
        self._rp_conf_val  = QLabel('—')
        self._rp_fps_key   = QLabel('FPS')
        self._rp_fps_val   = QLabel('—')
        self._rp_src_key   = QLabel('РЕЖИМ')
        self._rp_src_val   = QLabel('—')
        for key, val in ((self._rp_conf_key, self._rp_conf_val),
                         (self._rp_fps_key,  self._rp_fps_val),
                         (self._rp_src_key,  self._rp_src_val)):
            key.setObjectName('MetricKey')
            val.setObjectName('MetricVal')
            cell = QVBoxLayout()
            cell.setContentsMargins(0, 0, 0, 0)
            cell.setSpacing(4)
            cell.addWidget(key)
            cell.addWidget(val)
            metrics.addLayout(cell)
            metrics.addStretch(1)
        card_layout.addLayout(metrics)

        # Confidence bar
        bar_row = QHBoxLayout()
        bar_row.setContentsMargins(0, 0, 0, 0)
        bar_row.setSpacing(10)
        conf_lbl = QLabel('CONF')
        conf_lbl.setObjectName('MetricKey')
        bar_track = QFrame()
        bar_track.setObjectName('ConfBarTrack')
        bar_track.setMinimumWidth(60)
        bar_inner = QHBoxLayout(bar_track)
        bar_inner.setContentsMargins(0, 0, 0, 0)
        bar_inner.setSpacing(0)
        self._rp_conf_bar = QFrame()
        self._rp_conf_bar.setObjectName('ConfBarFill')
        self._rp_conf_bar.setFixedWidth(0)
        bar_inner.addWidget(self._rp_conf_bar)
        bar_inner.addStretch(1)
        self._rp_conf_pct = QLabel('—')
        self._rp_conf_pct.setObjectName('MetricVal')
        self._rp_conf_pct.setFixedWidth(42)
        bar_row.addWidget(conf_lbl)
        bar_row.addWidget(bar_track, 1)
        bar_row.addWidget(self._rp_conf_pct)
        card_layout.addLayout(bar_row)

        layout.addWidget(card)

        # ── Runtime stats card ──────────────────────────────────────────────
        rt = QFrame()
        rt.setObjectName('RuntimeCard')
        rt_layout = QGridLayout(rt)
        rt_layout.setContentsMargins(16, 14, 16, 14)
        rt_layout.setHorizontalSpacing(20)
        rt_layout.setVerticalSpacing(6)

        rt_title = QLabel('ТЕЛЕМЕТРИЯ ТРЕКЕРА')
        rt_title.setObjectName('RuntimeTitle')
        rt_layout.addWidget(rt_title, 0, 0, 1, 3)

        self._rp_rt_fps_k  = QLabel('FPS')
        self._rp_rt_fps_v  = QLabel('—')
        self._rp_rt_bdg_k  = QLabel('БЮДЖЕТ')
        self._rp_rt_bdg_v  = QLabel('—')
        self._rp_rt_tgt_k  = QLabel('ЦЕЛЕЙ')
        self._rp_rt_tgt_v  = QLabel('—')

        for i, (k, v) in enumerate(((self._rp_rt_fps_k, self._rp_rt_fps_v),
                                     (self._rp_rt_bdg_k, self._rp_rt_bdg_v),
                                     (self._rp_rt_tgt_k, self._rp_rt_tgt_v))):
            k.setObjectName('RuntimeTitle')
            v.setObjectName('RuntimeVal')
            rt_layout.addWidget(k, 1, i)
            rt_layout.addWidget(v, 2, i)

        layout.addWidget(rt)

        # ── Inspector (diagnostics) — collapsible ───────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.inspector_module = self.build_inspector_drawer()
        self.inspector_module.setVisible(True)
        scroll.setWidget(self.inspector_module)
        layout.addWidget(scroll, 1)

        return col

    def build_dock(self) -> QFrame:
        dock = QFrame()
        dock.setObjectName('Dock')

        layout = QHBoxLayout(dock)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(4)

        # Status / log line
        self.bottom_console_label = QLabel('готово к запуску')
        self.bottom_console_label.setObjectName('BottomConsoleText')
        self.bottom_console_label.setWordWrap(False)
        layout.addWidget(self.bottom_console_label, 1)

        sep1 = QFrame()
        sep1.setObjectName('DockSep')
        layout.addWidget(sep1)

        # Start
        self.start_btn = QPushButton('▶  Старт')
        self.start_btn.setObjectName('DockPrimary')
        layout.addWidget(self.start_btn)

        # Stop
        self.stop_btn = QPushButton('■  Стоп')
        self.stop_btn.setObjectName('DockDestructive')
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        sep2 = QFrame()
        sep2.setObjectName('DockSep')
        layout.addWidget(sep2)

        # Next target
        btn_next = self.next_target_btn if hasattr(self, 'next_target_btn') else QPushButton('↕')
        # next_target_btn already created in build_topbar; add a duplicate dock shortcut
        dock_next = QPushButton('↕')
        dock_next.setObjectName('DockIconBtn')
        dock_next.setToolTip('Следующая цель')
        dock_next.setEnabled(False)
        dock_next.clicked.connect(self._request_next_target)
        self._dock_next_btn = dock_next
        layout.addWidget(dock_next)

        return dock

    # keep alias so any code calling build_bottom_console still works
    def build_bottom_console(self) -> QFrame:
        return self.build_dock()

    def build_inspector_drawer(self) -> QWidget:
        return _build_inspector_drawer(self)

    def build_expert_dialog(self) -> None:
        _build_expert_dialog(self)

    def _on_expert_dialog_closed(self):
        self.expert_badge.setVisible(False)
        self.expert_btn.setProperty('variant', 'ghost')
        refresh_widget_style(self.expert_btn)

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

    def _refresh_header_state(self):
        _refresh_header_state_impl(self)

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
        return _split_source_impl(source)

    def _source_from_controls(self):
        return _source_from_controls_impl(self)

    def _on_source_type_changed(self):
        _on_source_type_changed_impl(self)

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
        refresh_widget_style(self.expert_btn)

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
        _apply_quick_profile_impl(self, preset_key)

    def _apply_canonical_operator_mode(self, mode_key: str) -> None:
        _apply_canonical_operator_mode_impl(self, mode_key)

    def _apply_scenario_preset(self, preset_key: str):
        _apply_scenario_preset_impl(self, preset_key)

    def _apply_runtime_mode_controls(self, mode: str):
        _apply_runtime_mode_controls_impl(self, mode)

    def _set_controls_from_profile(self, profile: dict[str, Any], preserve_source: bool = False):
        _set_controls_from_profile_impl(self, profile, preserve_source)

    def _apply_selected_preset(self):
        _apply_selected_preset_impl(self)

    def _collect_profile(self) -> dict[str, Any]:
        return _collect_profile_impl(self)

    def _load_profile_from_disk(self):
        _load_profile_from_disk_impl(self)

    def _save_profile_to_disk(self):
        _save_profile_to_disk_impl(self)

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
        _set_job_state_impl(self, state)

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
        refresh_widget_style(self._tc_state)

        # ── Right panel updates ─────────────────────────────────────────────
        self._rp_id_label.setText(f'ID {active_id}' if active_id is not None else '—')
        self._rp_name_label.setText(
            f'ID {active_id}' if active_id is not None else ('Потеря сигнала' if tracker_mode == 'LOST' else 'Нет цели')
        )
        self._rp_sub_label.setText(f'{active_source} · {operator_mode}')

        if tracker_mode == 'TRACK':
            self._rp_live_badge.setObjectName('LiveBadge')
            self._rp_state_chip.setText('ЗАХВАТ')
            self._rp_state_chip.setObjectName('ChipOk')
        elif tracker_mode == 'LOST':
            self._rp_live_badge.setObjectName('ChipWarn')
            self._rp_state_chip.setText('ПОТЕРЯ')
            self._rp_state_chip.setObjectName('ChipWarn')
        else:
            self._rp_live_badge.setObjectName('ChipAccent')
            self._rp_state_chip.setText('СКАН')
            self._rp_state_chip.setObjectName('ChipAccent')
        refresh_widget_style(self._rp_live_badge)
        refresh_widget_style(self._rp_state_chip)

        self._rp_conf_val.setText(f'{confidence_pct}%')
        self._rp_fps_val.setText(f'{fps:.0f}')
        self._rp_src_val.setText(tracker_mode)
        self._rp_conf_pct.setText(f'{confidence_pct}%')

        # Confidence bar fill (max width is track width of ConfBarTrack)
        bar_w = max(0, int(self._rp_conf_bar.parent().width() * display_confidence))
        self._rp_conf_bar.setFixedWidth(bar_w)

        # Runtime card
        self._rp_rt_fps_v.setText(f'{fps:.0f}')
        self._rp_rt_bdg_v.setText(f'L{budget_level}')
        self._rp_rt_tgt_v.setText(str(target_count))

        # Enable/disable Next Target button
        can_switch = self._job_state == 'tracking' and target_count > 1
        self.next_target_btn.setEnabled(can_switch)
        if hasattr(self, '_dock_next_btn'):
            self._dock_next_btn.setEnabled(can_switch)

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
        _save_app_settings_impl(self)

    def _load_app_settings(self):
        _load_app_settings_impl(self)

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
