import sys
import threading
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
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
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
from app.ui.layout_builders import (
    build_dock as _build_dock,
    build_header as _build_header,
    build_inspector_drawer as _build_inspector_drawer,
    build_left_rail as _build_left_rail,
    build_right_panel as _build_right_panel,
    build_topbar as _build_topbar,
)
from app.workers import EvaluationWorker, TrackerWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: TrackerWorker | None = None
        self.eval_worker: EvaluationWorker | None = None
        self._worker_lock = threading.RLock()
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
        return _build_topbar(self)

    def build_left_rail(self) -> QWidget:
        return _build_left_rail(self)

    def build_video_stage(self) -> QWidget:
        self.video_stage = VideoStage()
        self.video_label = self.video_stage.surface
        (self.target_info_card, self._tc_id, self._tc_conf,
         self._tc_fps, self._tc_time, self._tc_state) = build_target_info_card()
        self.video_stage.add_overlay_top_right(self.target_info_card)
        return self.video_stage

    def build_right_panel(self) -> QWidget:
        return _build_right_panel(self)

    def build_dock(self) -> QFrame:
        return _build_dock(self)

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
        with self._worker_lock:
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

        with self._worker_lock:
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
        with self._worker_lock:
            worker = self.worker
            eval_worker = self.eval_worker
        if worker is not None and worker.isRunning():
            self._set_job_state('stopping')
            worker.stop()
            self._log('Остановка сессии запрошена...')
            return
        if eval_worker is not None and eval_worker.isRunning():
            self._set_job_state('stopping')
            eval_worker.stop()
            self._log('Остановка оценки запрошена...')

    def _evaluate(self):
        with self._worker_lock:
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

        with self._worker_lock:
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
        with self._worker_lock:
            self.worker = None
        self._set_job_state('idle')

    def _on_eval_finished(self, reason: str):
        with self._worker_lock:
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
        with self._worker_lock:
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
        _update_stats_impl(self, stats)

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
        with self._worker_lock:
            if getattr(self, '_workers_shutdown_done', False):
                return
            self._workers_shutdown_done = True
            worker = self.worker
            eval_worker = self.eval_worker

        if worker is not None:
            worker.stop()
            deadline = time.monotonic() + 15.0
            while not worker.isFinished() and time.monotonic() < deadline:
                worker.wait(120)
            if not worker.isFinished():
                worker.terminate()
                worker.wait(1000)

        if eval_worker is not None:
            eval_worker.stop()
            deadline = time.monotonic() + 20.0
            while not eval_worker.isFinished() and time.monotonic() < deadline:
                eval_worker.wait(120)
            if not eval_worker.isFinished():
                eval_worker.terminate()
                eval_worker.wait(1000)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
