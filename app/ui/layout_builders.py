"""app/ui/layout_builders.py — Free-function layout builders extracted from MainWindow (T8e)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PySide6.QtCore import QTime, QTimer
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
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.ui.theme import refresh_widget_style


def build_topbar(window) -> QFrame:
    bar = QFrame()
    bar.setObjectName('TopBar')

    layout = QHBoxLayout(bar)
    layout.setContentsMargins(14, 0, 14, 0)
    layout.setSpacing(14)

    brand_name = QLabel('GIMBAL')
    brand_name.setObjectName('BrandName')
    brand_sub = QLabel('система сопровождения')
    brand_sub.setObjectName('BrandSub')
    layout.addWidget(brand_name)
    layout.addWidget(brand_sub)

    sep1 = QLabel()
    sep1.setObjectName('TopBarSep')
    layout.addWidget(sep1)

    mode_frame = QFrame()
    mode_frame.setObjectName('ModeSelector')
    mode_layout = QHBoxLayout(mode_frame)
    mode_layout.setContentsMargins(3, 3, 3, 3)
    mode_layout.setSpacing(2)

    window.quick_auto_btn = QPushButton('АВТО')
    window.quick_day_btn = QPushButton('ДЕНЬ')
    window.quick_night_btn = QPushButton('НОЧЬ')
    window.quick_ir_btn = QPushButton('IR')
    for btn in (window.quick_auto_btn, window.quick_day_btn,
                window.quick_night_btn, window.quick_ir_btn):
        btn.setObjectName('ModeBtn')
        mode_layout.addWidget(btn)
    window.quick_auto_btn.setProperty('active', 'true')
    refresh_widget_style(window.quick_auto_btn)

    layout.addWidget(mode_frame)

    sep2 = QLabel()
    sep2.setObjectName('TopBarSep')
    layout.addWidget(sep2)

    window.top_state_badge = QLabel('IDLE')
    window.top_state_badge.setObjectName('HeaderStatus')
    window.top_state_badge.setProperty('state', 'idle')
    layout.addWidget(window.top_state_badge)

    window.header_source_label = QLabel('CAM 0')
    window.header_source_label.setObjectName('BrandSub')
    layout.addWidget(window.header_source_label)

    sep3 = QLabel()
    sep3.setObjectName('TopBarSep')
    layout.addWidget(sep3)

    window.record_indicator_label = QLabel('● REC')
    window.record_indicator_label.setObjectName('RecordIndicator')
    window.record_indicator_label.setProperty('recording', False)
    layout.addWidget(window.record_indicator_label)

    sep4 = QLabel()
    sep4.setObjectName('TopBarSep')
    layout.addWidget(sep4)

    window.expert_btn = QPushButton('Эксперт')
    window.expert_btn.setObjectName('ModeBtn')
    layout.addWidget(window.expert_btn)

    window.dts_btn = QPushButton('DTS')
    window.dts_btn.setObjectName('ModeBtn')
    window.dts_btn.setToolTip('Training Desk: контроль ручной разметки')
    layout.addWidget(window.dts_btn)

    window.expert_badge = QLabel('EXP')
    window.expert_badge.setObjectName('ChipAccent')
    window.expert_badge.setVisible(False)
    layout.addWidget(window.expert_badge)

    window.fullscreen_btn = QPushButton('⛶')
    window.fullscreen_btn.setObjectName('ModeBtn')
    window.fullscreen_btn.setFixedWidth(34)
    window.fullscreen_btn.setToolTip('Полный экран')
    layout.addWidget(window.fullscreen_btn)

    window.next_target_btn = QPushButton('↕ Цель')
    window.next_target_btn.setObjectName('ModeBtn')
    window.next_target_btn.setToolTip('Следующая цель')
    window.next_target_btn.setEnabled(False)
    layout.addWidget(window.next_target_btn)

    window.operator_confirm_btn = QPushButton('✓')
    window.operator_confirm_btn.setObjectName('ModeBtn')
    window.operator_confirm_btn.setToolTip('Подтвердить текущую цель оператором')
    window.operator_confirm_btn.setEnabled(False)
    layout.addWidget(window.operator_confirm_btn)

    window.operator_release_btn = QPushButton('✕')
    window.operator_release_btn.setObjectName('ModeBtn')
    window.operator_release_btn.setToolTip('Сбросить операторскую цель')
    window.operator_release_btn.setEnabled(False)
    layout.addWidget(window.operator_release_btn)

    sep5 = QLabel()
    sep5.setObjectName('TopBarSep')
    layout.addWidget(sep5)

    window._clock_label = QLabel(QTime.currentTime().toString('HH:mm'))
    window._clock_label.setObjectName('TopBarClock')
    layout.addWidget(window._clock_label)
    window._clock_timer = QTimer(window)
    window._clock_timer.timeout.connect(
        lambda: window._clock_label.setText(QTime.currentTime().toString('HH:mm'))
    )
    window._clock_timer.start(30_000)

    return bar


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

    window.operator_confirm_btn = QPushButton('Подтвердить')
    window.operator_confirm_btn.setProperty('variant', 'ghost')
    window.operator_confirm_btn.setToolTip('Подтвердить текущую цель оператором')
    window.operator_confirm_btn.setEnabled(False)
    layout.addWidget(window.operator_confirm_btn)

    window.operator_release_btn = QPushButton('Сбросить')
    window.operator_release_btn.setProperty('variant', 'ghost')
    window.operator_release_btn.setToolTip('Сбросить операторскую цель')
    window.operator_release_btn.setEnabled(False)
    layout.addWidget(window.operator_release_btn)

    window.expert_btn = QPushButton('Эксперт')
    window.expert_btn.setProperty('variant', 'ghost')
    layout.addWidget(window.expert_btn)

    window.dts_btn = QPushButton('DTS')
    window.dts_btn.setProperty('variant', 'ghost')
    window.dts_btn.setToolTip('Training Desk: контроль ручной разметки')
    layout.addWidget(window.dts_btn)

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
    rail = QFrame()
    rail.setObjectName('LeftControlRail')
    rail.setFixedWidth(260)

    layout = QVBoxLayout(rail)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    src_panel = QFrame()
    src_panel.setObjectName('GlassPanel')
    src_layout = QVBoxLayout(src_panel)
    src_layout.setContentsMargins(14, 14, 14, 14)
    src_layout.setSpacing(8)

    src_title = QLabel('ИСТОЧНИК')
    src_title.setObjectName('RailSectionTitle')
    src_layout.addWidget(src_title)

    window.source_type_combo = QComboBox()
    window.source_type_combo.addItem('Камера', 'camera')
    window.source_type_combo.addItem('Видео', 'video')
    window.source_type_combo.addItem('Поток', 'stream')
    src_layout.addWidget(window.source_type_combo)

    window.camera_index_spin = QSpinBox()
    window.camera_index_spin.setRange(0, 16)
    window.camera_index_spin.setValue(0)
    src_layout.addWidget(window.camera_index_spin)

    window.source_path_label = QLabel('Видео файл')
    window.source_path_label.setObjectName('RailSectionTitle')
    src_layout.addWidget(window.source_path_label)

    window.source_path_edit = QLineEdit('')
    window.source_path_edit.setPlaceholderText('/путь/к/видео.mp4')
    src_layout.addWidget(window.source_path_edit)

    window.source_browse_btn = QPushButton('Выбрать...')
    src_layout.addWidget(window.source_browse_btn)

    layout.addWidget(src_panel)

    rec_panel = QFrame()
    rec_panel.setObjectName('GlassPanel')
    rec_layout = QVBoxLayout(rec_panel)
    rec_layout.setContentsMargins(14, 14, 14, 14)
    rec_layout.setSpacing(8)

    rec_title = QLabel('ЗАПИСЬ')
    rec_title.setObjectName('RailSectionTitle')
    rec_layout.addWidget(rec_title)

    window.record_check = QCheckBox('Сохранять видео')
    window.record_check.setChecked(True)
    rec_layout.addWidget(window.record_check)

    window.output_path_label = QLabel('Путь')
    window.output_path_label.setObjectName('RailSectionTitle')
    rec_layout.addWidget(window.output_path_label)

    window.output_edit = QLineEdit(str(ROOT / 'runs' / 'gui_output.mp4'))
    rec_layout.addWidget(window.output_edit)

    window.output_browse_btn = QPushButton('Куда сохранить...')
    rec_layout.addWidget(window.output_browse_btn)

    window.eval_btn = QPushButton('Оценка')
    window.eval_btn.setProperty('variant', 'ghost')
    rec_layout.addWidget(window.eval_btn)

    layout.addWidget(rec_panel)

    layout.addStretch(1)
    return rail


def build_right_panel(window) -> QWidget:
    from PySide6.QtWidgets import QGridLayout, QScrollArea
    from PySide6.QtCore import Qt

    col = QFrame()
    col.setObjectName('LeftControlRail')
    col.setFixedWidth(340)

    layout = QVBoxLayout(col)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    card = QFrame()
    card.setObjectName('ActiveTargetCard')
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(18, 18, 18, 18)
    card_layout.setSpacing(12)

    hdr = QHBoxLayout()
    hdr.setContentsMargins(0, 0, 0, 0)
    window._rp_live_badge = QLabel('● LOCK')
    window._rp_live_badge.setObjectName('LiveBadge')
    window._rp_id_label = QLabel('—')
    window._rp_id_label.setObjectName('ActiveTargetId')
    hdr.addWidget(window._rp_live_badge)
    hdr.addWidget(window._rp_id_label)
    hdr.addStretch(1)
    window._rp_state_chip = QLabel('IDLE')
    window._rp_state_chip.setObjectName('ChipWarn')
    hdr.addWidget(window._rp_state_chip)
    card_layout.addLayout(hdr)

    window._rp_name_label = QLabel('Нет цели')
    window._rp_name_label.setObjectName('ActiveTargetName')
    window._rp_sub_label = QLabel('ожидание...')
    window._rp_sub_label.setObjectName('ActiveTargetSub')
    card_layout.addWidget(window._rp_name_label)
    card_layout.addWidget(window._rp_sub_label)

    metrics = QHBoxLayout()
    metrics.setContentsMargins(0, 0, 0, 0)
    metrics.setSpacing(0)
    window._rp_conf_key = QLabel('УВЕРЕН')
    window._rp_conf_val = QLabel('—')
    window._rp_fps_key = QLabel('FPS')
    window._rp_fps_val = QLabel('—')
    window._rp_src_key = QLabel('РЕЖИМ')
    window._rp_src_val = QLabel('—')
    for key, val in ((window._rp_conf_key, window._rp_conf_val),
                     (window._rp_fps_key, window._rp_fps_val),
                     (window._rp_src_key, window._rp_src_val)):
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
    window._rp_conf_bar = QFrame()
    window._rp_conf_bar.setObjectName('ConfBarFill')
    window._rp_conf_bar.setFixedWidth(0)
    bar_inner.addWidget(window._rp_conf_bar)
    bar_inner.addStretch(1)
    window._rp_conf_pct = QLabel('—')
    window._rp_conf_pct.setObjectName('MetricVal')
    window._rp_conf_pct.setFixedWidth(42)
    bar_row.addWidget(conf_lbl)
    bar_row.addWidget(bar_track, 1)
    bar_row.addWidget(window._rp_conf_pct)
    card_layout.addLayout(bar_row)

    layout.addWidget(card)

    rt = QFrame()
    rt.setObjectName('RuntimeCard')
    rt_layout = QGridLayout(rt)
    rt_layout.setContentsMargins(16, 14, 16, 14)
    rt_layout.setHorizontalSpacing(20)
    rt_layout.setVerticalSpacing(6)

    rt_title = QLabel('ТЕЛЕМЕТРИЯ ТРЕКЕРА')
    rt_title.setObjectName('RuntimeTitle')
    rt_layout.addWidget(rt_title, 0, 0, 1, 3)

    window._rp_rt_fps_k = QLabel('FPS')
    window._rp_rt_fps_v = QLabel('—')
    window._rp_rt_bdg_k = QLabel('БЮДЖЕТ')
    window._rp_rt_bdg_v = QLabel('—')
    window._rp_rt_tgt_k = QLabel('ЦЕЛЕЙ')
    window._rp_rt_tgt_v = QLabel('—')

    for i, (k, v) in enumerate(((window._rp_rt_fps_k, window._rp_rt_fps_v),
                                 (window._rp_rt_bdg_k, window._rp_rt_bdg_v),
                                 (window._rp_rt_tgt_k, window._rp_rt_tgt_v))):
        k.setObjectName('RuntimeTitle')
        v.setObjectName('RuntimeVal')
        rt_layout.addWidget(k, 1, i)
        rt_layout.addWidget(v, 2, i)

    layout.addWidget(rt)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    window.inspector_module = build_inspector_drawer(window)
    window.inspector_module.setVisible(True)
    scroll.setWidget(window.inspector_module)
    layout.addWidget(scroll, 1)

    return col


def build_dock(window) -> QFrame:
    dock = QFrame()
    dock.setObjectName('Dock')

    layout = QHBoxLayout(dock)
    layout.setContentsMargins(12, 0, 12, 0)
    layout.setSpacing(4)

    window.bottom_console_label = QLabel('готово к запуску')
    window.bottom_console_label.setObjectName('BottomConsoleText')
    window.bottom_console_label.setWordWrap(False)
    layout.addWidget(window.bottom_console_label, 1)

    sep1 = QFrame()
    sep1.setObjectName('DockSep')
    layout.addWidget(sep1)

    window.start_btn = QPushButton('▶  Старт')
    window.start_btn.setObjectName('DockPrimary')
    layout.addWidget(window.start_btn)

    window.stop_btn = QPushButton('■  Стоп')
    window.stop_btn.setObjectName('DockDestructive')
    window.stop_btn.setEnabled(False)
    layout.addWidget(window.stop_btn)

    sep2 = QFrame()
    sep2.setObjectName('DockSep')
    layout.addWidget(sep2)

    dock_next = QPushButton('↕')
    dock_next.setObjectName('DockIconBtn')
    dock_next.setToolTip('Следующая цель')
    dock_next.setEnabled(False)
    dock_next.clicked.connect(window._request_next_target)
    window._dock_next_btn = dock_next
    layout.addWidget(dock_next)

    dock_confirm = QPushButton('✓')
    dock_confirm.setObjectName('DockIconBtn')
    dock_confirm.setToolTip('Подтвердить текущую цель')
    dock_confirm.setEnabled(False)
    dock_confirm.clicked.connect(window._request_operator_confirm)
    window._dock_operator_confirm_btn = dock_confirm
    layout.addWidget(dock_confirm)

    dock_release = QPushButton('✕')
    dock_release.setObjectName('DockIconBtn')
    dock_release.setToolTip('Сбросить операторскую цель')
    dock_release.setEnabled(False)
    dock_release.clicked.connect(window._request_operator_release)
    window._dock_operator_release_btn = dock_release
    layout.addWidget(dock_release)

    return dock


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
