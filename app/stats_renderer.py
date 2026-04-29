"""app/stats_renderer.py — Stats update logic extracted from MainWindow (T8c)."""
import time

from app.ui import UIState
from app.ui.theme import refresh_widget_style


def update_stats(window, stats: dict) -> None:
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
        window._target_present_latched = True
        window._target_missing_streak = 0
        window._had_target_in_session = True
    elif tracker_mode == 'LOST':
        window._target_present_latched = True
        window._target_missing_streak += 1
    elif window._target_present_latched:
        window._target_missing_streak += 1
        if window._target_missing_streak >= 8:
            window._target_present_latched = False
    target_present = tracker_mode in {'TRACK', 'LOST'}

    if window._job_state == 'tracking':
        if tracker_mode == 'TRACK':
            window._state_machine.set(UIState.LOCK)
        elif tracker_mode == 'LOST':
            window._state_machine.set(UIState.LOST)
        elif window._target_present_latched and window._target_missing_streak < 3:
            # Brief SCAN while recently latched: hold LOCK badge to avoid flicker.
            window._state_machine.set(UIState.LOCK)
        else:
            window._state_machine.set(UIState.RUNNING)
    elif window._job_state == 'evaluating':
        window._state_machine.set(UIState.EVALUATION)
    elif window._job_state == 'stopping':
        window._state_machine.set(UIState.CHECKING)
    else:
        window._state_machine.set(UIState.IDLE)
    window._last_active_id = active_id

    state_value_map = {
        UIState.IDLE: 'Ожидание',
        UIState.CHECKING: 'Остановка',
        UIState.RUNNING: 'Сканирование',
        UIState.LOCK: 'Захват',
        UIState.LOST: 'Повторный захват',
        UIState.EVALUATION: 'Оценка',
        UIState.ERROR: 'Ошибка',
    }
    state_value = state_value_map.get(window._state_machine.state, 'Ожидание')

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
    window.console_status_label.setText(
        f"$ {state_value.lower()} // {target_value.lower()} // {operator_mode.lower()}"
    )

    window.panel_runtime_summary = (
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
    window.panel_monitoring_summary.setText(window.panel_runtime_summary)
    window.panel_target_summary.setText(
        f"Цель: {'ID ' + str(active_id) if active_id is not None else ('временная потеря' if target_present else 'не обнаружена')}\n"
        f"Источник: {active_source}\n"
        f"Lock score: {lock_score:.2f} | strategy: {scan_strategy}"
    )
    window.panel_quality_summary.setText(
        f"{quality_main}\n"
        f"sw/min {lock_switches_per_min:.2f} ({lock_switch_count}) | "
        f"roi cand {roi_budget_candidates} | night skip {night_skip}\n"
        f"видимые цели: {visible_count}, всего: {target_count}, фон: {bg_visible}"
    )

    for event in stats.get('lock_events', []):
        window._log(f"[f{frame_index + 1}] {event}")
        window.panel_events_view.appendPlainText(f"[f{frame_index + 1}] {event}")

    if tracker_mode == 'TRACK' and active_id is not None:
        if window._target_lock_start is None:
            window._target_lock_start = time.perf_counter()
        elapsed = time.perf_counter() - window._target_lock_start
        elapsed_str = f'{int(elapsed // 60):02d}:{int(elapsed % 60):02d}'
        card_state, card_state_key = 'LOCK', 'lock'
    elif tracker_mode == 'LOST':
        elapsed_str = '—'
        card_state, card_state_key = 'ПОТЕРЯ', 'lost'
    else:
        window._target_lock_start = None
        elapsed_str = '—'
        card_state, card_state_key = 'IDLE', 'idle'
    window._tc_id.setText(f'ID {active_id}' if active_id is not None else '—')
    window._tc_conf.setText(f'{confidence_pct}%')
    window._tc_fps.setText(f'{fps:.1f}')
    window._tc_time.setText(elapsed_str)
    window._tc_state.setText(card_state)
    window._tc_state.setProperty('state', card_state_key)
    refresh_widget_style(window._tc_state)
    window.next_target_btn.setEnabled(window._job_state == 'tracking' and target_count > 1)

    window._refresh_header_state()
