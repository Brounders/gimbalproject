"""app/profile_controller.py — Profile / preset / mode control helpers (T8b)."""
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PySide6.QtWidgets import QFileDialog

from uav_tracker.config import Config
from uav_tracker.modes import apply_runtime_mode
from uav_tracker.profile_io import load_preset, load_profile, save_profile
from app.ui.theme import SCENARIO_LABELS, refresh_widget_style

# Canonical operator modes: label → (preset_key, night_enabled_override)
CANONICAL_OPERATOR_MODES: dict[str, tuple[str, bool | None]] = {
    'auto':  ('default', None),
    'day':   ('default', False),
    'night': ('night', None),
    'ir':    ('antiuav_thermal', None),
}


def apply_quick_profile(window, preset_key: str) -> None:
    idx = window.scenario_combo.findData(preset_key)
    if idx >= 0:
        window.scenario_combo.setCurrentIndex(idx)
        return
    window._log(f'Preset недоступен: {preset_key}')


def apply_canonical_operator_mode(window, mode_key: str) -> None:
    """Apply one of the 4 canonical operator modes: auto/day/night/ir.

    Each mode loads the mapped preset and applies operator-safe display
    overrides so that operator buttons never activate research-mode HUD.
    """
    entry = CANONICAL_OPERATOR_MODES.get(mode_key)
    if entry is None:
        window._log(f'Неизвестный канонический режим: {mode_key}')
        return
    preset_key, night_override = entry
    apply_scenario_preset(window, preset_key)
    if not window._updating_controls:
        window._updating_controls = True
        try:
            if window.mode_combo.findText('operator') >= 0:
                window.mode_combo.setCurrentText('operator')
            window.show_gt_check.setChecked(False)
            window.timing_check.setChecked(False)
            window.show_trails_check.setChecked(False)
            if night_override is not None:
                window.night_check.setChecked(night_override)
        finally:
            window._updating_controls = False
    window._auto_scene_detect_enabled = (mode_key == 'auto')
    labels = {'auto': 'Авто', 'day': 'День', 'night': 'Ночь', 'ir': 'IR'}
    window._log(f'Режим оператора: {labels.get(mode_key, mode_key)}')
    mode_btns = {
        'auto': window.quick_auto_btn, 'day': window.quick_day_btn,
        'night': window.quick_night_btn, 'ir': window.quick_ir_btn,
    }
    for key, btn in mode_btns.items():
        btn.setProperty('active', key == mode_key)
        refresh_widget_style(btn)


def apply_scenario_preset(window, preset_key: str) -> None:
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
    set_controls_from_profile(window, profile, preserve_source=True)
    window._log(f'Сценарий применен: {SCENARIO_LABELS.get(preset_key, preset_key)}')


def apply_runtime_mode_controls(window, mode: str) -> None:
    if window._updating_controls:
        return
    cfg = apply_runtime_mode(Config(), mode)
    window.show_gt_check.setChecked(cfg.SHOW_GT_OVERLAY)
    window.timing_check.setChecked(cfg.SHOW_DEBUG_TIMINGS)
    window.show_trails_check.setChecked(cfg.SHOW_TRAILS)
    window.adaptive_scan_check.setChecked(cfg.ADAPTIVE_SCAN_ENABLED)
    window.lock_tracker_check.setChecked(cfg.LOCK_TRACKER_ENABLED)
    window.night_check.setChecked(cfg.NIGHT_ENABLED)
    window.roi_check.setChecked(cfg.ROI_ASSIST_ENABLED)
    window.rescan_spin.setValue(cfg.GLOBAL_SCAN_INTERVAL)


def set_controls_from_profile(window, profile: dict[str, Any], preserve_source: bool = False) -> None:
    window._updating_controls = True
    try:
        preset = profile.get('preset', 'custom')
        pidx = window.preset_combo.findText(str(preset))
        if pidx >= 0:
            window.preset_combo.setCurrentIndex(pidx)
        else:
            custom_pidx = window.preset_combo.findText('custom')
            if custom_pidx >= 0:
                window.preset_combo.setCurrentIndex(custom_pidx)
        scenario_idx = window.scenario_combo.findData(preset if preset is not None else 'custom')
        if scenario_idx >= 0:
            window.scenario_combo.setCurrentIndex(scenario_idx)
        else:
            custom_idx = window.scenario_combo.findData('custom')
            if custom_idx >= 0:
                window.scenario_combo.setCurrentIndex(custom_idx)

        if not preserve_source:
            source_type, cam_idx, source_path = window._split_source(profile.get('source', 0))
            st_idx = window.source_type_combo.findData(source_type)
            if st_idx >= 0:
                window.source_type_combo.setCurrentIndex(st_idx)
            window.camera_index_spin.setValue(cam_idx)
            window.source_path_edit.setText(source_path)

        mode = str(profile.get('runtime_mode', window.mode_combo.currentText()))
        if window.mode_combo.findText(mode) >= 0:
            window.mode_combo.setCurrentText(mode)

        device = str(profile.get('device', window.device_combo.currentText()))
        if window.device_combo.findText(device) >= 0:
            window.device_combo.setCurrentText(device)

        window.model_edit.setText(str(profile.get('model_path', window.model_edit.text())))
        window.imgsz_spin.setValue(int(profile.get('imgsz', window.imgsz_spin.value())))
        window.conf_spin.setValue(float(profile.get('conf_thresh', window.conf_spin.value())))
        window.rescan_spin.setValue(int(profile.get('global_scan_interval', window.rescan_spin.value())))

        window.small_target_check.setChecked(bool(profile.get('small_target_mode', window.small_target_check.isChecked())))
        window.adaptive_scan_check.setChecked(bool(profile.get('adaptive_scan_enabled', window.adaptive_scan_check.isChecked())))
        window.lock_tracker_check.setChecked(bool(profile.get('lock_tracker_enabled', window.lock_tracker_check.isChecked())))
        window.night_check.setChecked(bool(profile.get('night_enabled', window.night_check.isChecked())))
        window.roi_check.setChecked(bool(profile.get('roi_assist_enabled', window.roi_check.isChecked())))
        window.show_gt_check.setChecked(bool(profile.get('show_gt_overlay', window.show_gt_check.isChecked())))
        window.timing_check.setChecked(bool(profile.get('show_debug_timings', window.timing_check.isChecked())))
        window.show_trails_check.setChecked(bool(profile.get('show_trails', window.show_trails_check.isChecked())))

        window.record_check.setChecked(bool(profile.get('record_output', window.record_check.isChecked())))
        window.output_edit.setText(str(profile.get('output_path', window.output_edit.text())))

        ignored = {
            'preset', 'runtime_mode', 'source', 'model_path', 'device', 'imgsz', 'conf_thresh',
            'small_target_mode', 'adaptive_scan_enabled', 'global_scan_interval', 'lock_tracker_enabled',
            'night_enabled', 'roi_assist_enabled', 'show_gt_overlay', 'show_debug_timings', 'show_trails',
            'record_output', 'output_path'
        }
        window._profile_extras = {k: v for k, v in profile.items() if k not in ignored}
    finally:
        window._updating_controls = False
        window._refresh_record_controls()
        window._on_source_type_changed()
        window._refresh_workspace_overviews()
        window._refresh_sidebar_meta()
        window._refresh_header_state()


def apply_selected_preset(window) -> None:
    if window._updating_controls:
        return
    preset_name = window.preset_combo.currentText()
    if preset_name == 'custom':
        window._profile_extras = {}
        window._log('Preset: custom')
        return
    apply_scenario_preset(window, preset_name)


def collect_profile(window) -> dict[str, Any]:
    source = window._source_from_controls()
    preset_key = window.scenario_combo.currentData() or 'custom'
    profile = {
        'preset': preset_key,
        'runtime_mode': window.mode_combo.currentText(),
        'source': str(source),
        'model_path': window.model_edit.text().strip(),
        'device': window.device_combo.currentText(),
        'imgsz': int(window.imgsz_spin.value()),
        'conf_thresh': float(window.conf_spin.value()),
        'small_target_mode': window.small_target_check.isChecked(),
        'adaptive_scan_enabled': window.adaptive_scan_check.isChecked(),
        'global_scan_interval': int(window.rescan_spin.value()),
        'lock_tracker_enabled': window.lock_tracker_check.isChecked(),
        'night_enabled': window.night_check.isChecked(),
        'roi_assist_enabled': window.roi_check.isChecked(),
        'show_gt_overlay': window.show_gt_check.isChecked(),
        'show_debug_timings': window.timing_check.isChecked(),
        'show_trails': window.show_trails_check.isChecked(),
        'record_output': window.record_check.isChecked(),
        'output_path': window.output_edit.text().strip(),
    }
    profile.update(window._profile_extras)
    return profile


def load_profile_from_disk(window) -> None:
    path, _ = QFileDialog.getOpenFileName(window, 'Загрузить профиль', str(ROOT / 'configs'), 'YAML (*.yaml *.yml)')
    if not path:
        return
    profile = load_profile(path)
    set_controls_from_profile(window, profile)
    window._log(f'Профиль загружен: {path}')


def save_profile_to_disk(window) -> None:
    path, _ = QFileDialog.getSaveFileName(window, 'Сохранить профиль', str(ROOT / 'configs' / 'custom_profile.yaml'), 'YAML (*.yaml *.yml)')
    if not path:
        return
    save_profile(path, collect_profile(window))
    window._log(f'Профиль сохранен: {path}')
