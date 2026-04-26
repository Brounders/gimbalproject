"""app/ui/layout_builders.py — Free-function layout builders extracted from MainWindow (T8e)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


def build_header(window) -> QFrame:
    header = QFrame()
    header.setObjectName('HeaderBar')
    header.setMinimumHeight(60)
    header.setMaximumHeight(66)

    layout = QHBoxLayout(header)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(8)

    window.header_title_label = QLabel('Система сопровождения БПЛА')
    window.header_title_label.setObjectName('WindowTitle')
    layout.addWidget(window.header_title_label)

    layout.addSpacing(6)
    window.top_state_badge = QLabel('IDLE')
    window.top_state_badge.setObjectName('HeaderStatus')
    window.top_state_badge.setProperty('state', 'idle')
    layout.addWidget(window.top_state_badge)

    window.header_source_label = QLabel('Источник: CAM 0')
    window.header_source_label.setObjectName('HeaderMeta')
    layout.addWidget(window.header_source_label, 1)

    window.record_indicator_label = QLabel('REC OFF')
    window.record_indicator_label.setObjectName('RecordIndicator')
    window.record_indicator_label.setProperty('recording', False)
    layout.addWidget(window.record_indicator_label)

    window.next_target_btn = QPushButton('Следующая цель')
    window.next_target_btn.setProperty('variant', 'ghost')
    window.next_target_btn.setToolTip('Переключить на следующую доступную цель')
    window.next_target_btn.setEnabled(False)
    layout.addWidget(window.next_target_btn)

    window.expert_btn = QPushButton('Эксперт')
    window.expert_btn.setProperty('variant', 'ghost')
    layout.addWidget(window.expert_btn)

    window.expert_badge = QLabel('EXP')
    window.expert_badge.setObjectName('HeaderMeta')
    window.expert_badge.setVisible(False)
    layout.addWidget(window.expert_badge)

    window.fullscreen_btn = QPushButton('⛶')
    window.fullscreen_btn.setFixedWidth(34)
    window.fullscreen_btn.setProperty('variant', 'ghost')
    window.fullscreen_btn.setToolTip('Полный экран')
    layout.addWidget(window.fullscreen_btn)

    window.start_btn = QPushButton('Старт')
    window.start_btn.setProperty('variant', 'primary')
    layout.addWidget(window.start_btn)

    window.stop_btn = QPushButton('Стоп')
    window.stop_btn.setProperty('variant', 'destructive')
    window.stop_btn.setEnabled(False)
    layout.addWidget(window.stop_btn)

    return header


def build_left_rail(window) -> QWidget:
    ROOT_DIR = Path(__file__).resolve().parents[2]

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

    window.quick_auto_btn = QPushButton('Авто')
    window.quick_auto_btn.setProperty('variant', 'ghost')
    window.quick_day_btn = QPushButton('День')
    window.quick_day_btn.setProperty('variant', 'ghost')
    window.quick_night_btn = QPushButton('Ночь')
    window.quick_night_btn.setProperty('variant', 'ghost')
    window.quick_ir_btn = QPushButton('IR')
    window.quick_ir_btn.setProperty('variant', 'ghost')
    window.quick_auto_btn.setToolTip('Авто: адаптивный день/ночь (default preset, ночной детектор вкл.)')
    window.quick_day_btn.setToolTip('День: только дневной режим (ночной детектор выкл.)')
    window.quick_night_btn.setToolTip('Ночь: ночной preset в операторском режиме')
    window.quick_ir_btn.setToolTip('IR: thermal / Anti-UAV preset')

    quick_row = QHBoxLayout()
    quick_row.setContentsMargins(0, 0, 0, 0)
    quick_row.setSpacing(4)
    quick_row.addWidget(window.quick_auto_btn)
    quick_row.addWidget(window.quick_day_btn)
    quick_row.addWidget(window.quick_night_btn)
    quick_row.addWidget(window.quick_ir_btn)
    layout.addLayout(quick_row)

    window.source_type_combo = QComboBox()
    window.source_type_combo.addItem('Камера', 'camera')
    window.source_type_combo.addItem('Видео', 'video')
    window.source_type_combo.addItem('Поток', 'stream')
    layout.addWidget(window.source_type_combo)

    window.camera_index_spin = QSpinBox()
    window.camera_index_spin.setRange(0, 16)
    window.camera_index_spin.setValue(0)
    layout.addWidget(window.camera_index_spin)

    window.source_path_label = QLabel('Видео файл')
    window.source_path_label.setObjectName('RailSectionTitle')
    layout.addWidget(window.source_path_label)

    window.source_path_edit = QLineEdit('')
    window.source_path_edit.setPlaceholderText('/путь/к/видео.mp4')
    layout.addWidget(window.source_path_edit)

    window.source_browse_btn = QPushButton('Выбрать...')
    layout.addWidget(window.source_browse_btn)

    window.record_check = QCheckBox('Сохранять видео')
    window.record_check.setChecked(True)
    layout.addWidget(window.record_check)

    window.output_path_label = QLabel('Выход')
    window.output_path_label.setObjectName('RailSectionTitle')
    layout.addWidget(window.output_path_label)

    window.output_edit = QLineEdit(str(ROOT_DIR / 'runs' / 'gui_output.mp4'))
    layout.addWidget(window.output_edit)

    window.output_browse_btn = QPushButton('Куда сохранить...')
    layout.addWidget(window.output_browse_btn)

    window.eval_btn = QPushButton('Оценка')
    layout.addWidget(window.eval_btn)

    window.inspector_module = build_inspector_drawer(window)
    window.inspector_module.setVisible(False)
    layout.addWidget(window.inspector_module, 1)

    layout.addStretch(1)
    return rail


def build_inspector_drawer(window) -> QWidget:
    from app.ui.cards import build_inspector_card

    body = QGroupBox('Диагностика')
    body.setObjectName('InspectorModule')
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(8, 8, 8, 8)
    body_layout.setSpacing(8)

    target_card, window.panel_target_summary = build_inspector_card('Цель')
    quality_card, window.panel_quality_summary = build_inspector_card('Качество')
    runtime_card, window.panel_monitoring_summary = build_inspector_card('Runtime health')
    params_card, window.panel_params_summary = build_inspector_card('Параметры')
    eval_card, window.eval_summary_label = build_inspector_card('Оценка')
    window.eval_summary_hint = QLabel('-')
    window.eval_summary_hint.setObjectName('InspectorValue')
    eval_card.layout().addWidget(window.eval_summary_hint)

    events_card = QFrame()
    events_card.setObjectName('InspectorCard')
    events_layout = QVBoxLayout(events_card)
    events_layout.setContentsMargins(8, 8, 8, 8)
    events_layout.setSpacing(4)
    events_title = QLabel('События')
    events_title.setObjectName('InspectorTitle')
    events_layout.addWidget(events_title)
    window.panel_events_view = QPlainTextEdit()
    window.panel_events_view.setReadOnly(True)
    window.panel_events_view.setMaximumBlockCount(120)
    window.panel_events_view.setMaximumHeight(180)
    events_layout.addWidget(window.panel_events_view)

    body_layout.addWidget(target_card)
    body_layout.addWidget(quality_card)
    body_layout.addWidget(runtime_card)
    body_layout.addWidget(params_card)
    body_layout.addWidget(eval_card)
    body_layout.addWidget(events_card, 1)
    return body
