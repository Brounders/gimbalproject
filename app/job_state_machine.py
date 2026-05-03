"""app/job_state_machine.py — Job state transitions and header refresh (T8g)."""
from pathlib import Path

from app.ui import UIState
from app.ui.theme import refresh_widget_style


def refresh_header_state(window) -> None:
    from uav_tracker.config import Config  # avoid circular at module level
    scenario_key = str(window.scenario_combo.currentData() or 'custom')
    from app.ui.theme import SCENARIO_LABELS
    scenario_label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    source_type = str(window.source_type_combo.currentData() or 'camera')
    if source_type == 'camera':
        source_display = f"CAM {window.camera_index_spin.value()}"
    elif source_type == 'stream':
        source_display = 'ПОТОК'
    else:
        source_display = 'ВИДЕО'
    source_hint = str(window.source_path_edit.text().strip() or source_display)
    if source_type == 'video':
        source_short = Path(source_hint).name or source_display
    elif source_type == 'stream':
        source_short = source_hint[:48]
    else:
        source_short = source_display

    window.top_scenario_label.setText(f"Источник: {source_short} | Сцена: {scenario_label}")

    state_map = {
        UIState.IDLE: ('IDLE', 'idle'),
        UIState.CHECKING: ('CHECK', 'stopping'),
        UIState.RUNNING: ('RUNNING', 'running'),
        UIState.LOCK: ('LOCK', 'lock'),
        UIState.LOST: ('LOST', 'lost'),
        UIState.EVALUATION: ('EVALUATE', 'evaluating'),
        UIState.ERROR: ('ERROR', 'error'),
    }
    state_text, state_name = state_map.get(window._state_machine.state, ('IDLE', 'idle'))
    window.top_state_badge.setText(state_text)
    window.top_state_badge.setProperty('state', state_name)
    refresh_widget_style(window.top_state_badge)

    readable_state = {
        UIState.IDLE: 'Ожидание',
        UIState.CHECKING: 'Остановка',
        UIState.RUNNING: 'Сканирование',
        UIState.LOCK: 'Захват',
        UIState.LOST: 'Потеря',
        UIState.EVALUATION: 'Оценка',
        UIState.ERROR: 'Ошибка',
    }
    window.console_status_label.setText(
        f"$ {readable_state.get(window._state_machine.state, 'Ожидание').lower()} // {source_display.lower()} // {source_hint}"
    )

    recording = window._job_state in {'tracking', 'stopping'} and window.record_check.isChecked()
    if recording:
        window.record_indicator_label.setText('REC ON')
    elif window.record_check.isChecked():
        window.record_indicator_label.setText('REC READY')
    else:
        window.record_indicator_label.setText('REC OFF')
    window.record_indicator_label.setProperty('recording', recording)
    refresh_widget_style(window.record_indicator_label)

    window.panel_params_summary.setText(
        'Сценарий: '
        f"{scenario_label}\n"
        f"Источник: {window.source_type_combo.currentText()} | device: {window.device_combo.currentText()}\n"
        f"imgsz/conf: {window.imgsz_spin.value()} / {window.conf_spin.value():.2f}"
    )


def set_job_state(window, state: str) -> None:
    window._job_state = state
    if state == 'idle':
        window._state_machine.set(UIState.IDLE)
    elif state == 'tracking':
        window._state_machine.set(UIState.RUNNING)
    elif state == 'stopping':
        window._state_machine.set(UIState.CHECKING)
    elif state == 'evaluating':
        window._state_machine.set(UIState.EVALUATION)

    tracking_active = state in {'tracking', 'stopping'}
    evaluating_active = state == 'evaluating'
    busy = tracking_active or evaluating_active

    window.start_btn.setEnabled(window._state_machine.can_start() and not busy)
    window.eval_btn.setEnabled(window._state_machine.can_evaluate() and not busy)
    window.stop_btn.setEnabled(window._state_machine.can_stop())
    for name in (
        'operator_confirm_btn',
        'operator_release_btn',
        '_dock_operator_confirm_btn',
        '_dock_operator_release_btn',
    ):
        widget = getattr(window, name, None)
        if widget is not None:
            widget.setEnabled(state == 'tracking')

    for widget in [
        window.scenario_combo,
        window.quick_day_btn,
        window.quick_night_btn,
        window.quick_ir_btn,
        window.source_type_combo,
        window.camera_index_spin,
        window.source_path_edit,
        window.source_browse_btn,
        window.record_check,
        window.output_edit,
        window.output_browse_btn,
        window.expert_btn,
    ]:
        widget.setEnabled(not busy)
    window._refresh_record_controls()

    if state == 'idle':
        window._target_present_latched = False
        window._target_missing_streak = 0
        window._had_target_in_session = False

    window._on_source_type_changed()
    window._refresh_header_state()
