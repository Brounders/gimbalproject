from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from uav_tracker.config import Config
from uav_tracker.modes import apply_runtime_mode


PRESET_DIR = Path(__file__).resolve().parents[2] / 'configs'
PROFILE_KEYS = {'preset', 'source', 'record_output', 'output_path'}


def load_yaml(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text())
    return data or {}


def _looks_like_preset(data: dict[str, Any]) -> bool:
    return not any(key in data for key in PROFILE_KEYS)


def available_presets() -> list[str]:
    if not PRESET_DIR.exists():
        return []
    names = []
    for path in PRESET_DIR.glob('*.yaml'):
        data = load_yaml(path)
        if _looks_like_preset(data):
            names.append(path.stem)
    return sorted(names)


def apply_overrides(cfg: Config, overrides: dict[str, Any]) -> Config:
    runtime_mode = overrides.get('runtime_mode')
    if runtime_mode:
        cfg = apply_runtime_mode(cfg, str(runtime_mode))

    mapping = {
        'model_path': 'MODEL_PATH',
        'device': 'DEVICE',
        'imgsz': 'IMG_SIZE',
        'conf_thresh': 'CONF_THRESH',
        'ignore_zones': 'IGNORE_ZONES',
        'detection_max_area_ratio': 'DETECTION_MAX_AREA_RATIO',
        'detection_max_width_ratio': 'DETECTION_MAX_WIDTH_RATIO',
        'detection_max_height_ratio': 'DETECTION_MAX_HEIGHT_RATIO',
        'small_target_mode': None,
        'runtime_mode': 'RUNTIME_MODE',
        'night_enabled': 'NIGHT_ENABLED',
        'roi_assist_enabled': 'ROI_ASSIST_ENABLED',
        'roi_conf_thresh': 'ROI_CONF_THRESH',
        'budget_enabled': 'BUDGET_ENABLED',
        'budget_target_fps': 'BUDGET_TARGET_FPS',
        'budget_high_load': 'BUDGET_HIGH_LOAD',
        'budget_low_load': 'BUDGET_LOW_LOAD',
        'budget_level_max': 'BUDGET_LEVEL_MAX',
        'budget_roi_min_candidates': 'BUDGET_ROI_MIN_CANDIDATES',
        'budget_night_skip_level1': 'BUDGET_NIGHT_SKIP_LEVEL1',
        'budget_night_skip_level2': 'BUDGET_NIGHT_SKIP_LEVEL2',
        'budget_roi_skip_level2': 'BUDGET_ROI_SKIP_LEVEL2',
        'budget_scan_interval_boost_per_level': 'BUDGET_SCAN_INTERVAL_BOOST_PER_LEVEL',
        'budget_local_validate_boost_per_level': 'BUDGET_LOCAL_VALIDATE_BOOST_PER_LEVEL',
        'night_mot_thresh': 'NIGHT_MOT_THRESH',
        'night_diff_thresh': 'NIGHT_DIFF_THRESH',
        'night_mog2_history': 'NIGHT_MOG2_HISTORY',
        'night_mog2_var_thresh': 'NIGHT_MOG2_VAR_THRESH',
        'night_blur_kernel': 'NIGHT_BLUR_KERNEL',
        'night_morph_kernel': 'NIGHT_MORPH_KERNEL',
        'night_min_area': 'NIGHT_MIN_AREA',
        'adaptive_scan_enabled': 'ADAPTIVE_SCAN_ENABLED',
        'global_scan_interval': 'GLOBAL_SCAN_INTERVAL',
        'local_track_img_size': 'LOCAL_TRACK_IMG_SIZE',
        'local_track_conf': 'LOCAL_TRACK_CONF',
        'local_validate_interval': 'LOCAL_VALIDATE_INTERVAL',
        'local_small_box_area': 'LOCAL_SMALL_BOX_AREA',
        'local_small_box_ratio': 'LOCAL_SMALL_BOX_RATIO',
        'local_small_img_size': 'LOCAL_SMALL_IMG_SIZE',
        'local_small_conf': 'LOCAL_SMALL_CONF',
        'local_boost_lock_score_thresh': 'LOCAL_BOOST_LOCK_SCORE_THRESH',
        'lock_tracker_enabled': 'LOCK_TRACKER_ENABLED',
        'lock_tracker_min_score': 'LOCK_TRACKER_MIN_SCORE',
        'lock_tracker_search_scale': 'LOCK_TRACKER_SEARCH_SCALE',
        'velocity_alpha': 'VELOCITY_ALPHA',
        'lock_confirm_frames': 'LOCK_CONFIRM_FRAMES',
        'lock_lost_grace': 'LOCK_LOST_GRACE',
        'lock_reacquire_dist': 'LOCK_REACQUIRE_DIST',
        'lock_reacquire_predict_gain': 'LOCK_REACQUIRE_PREDICT_GAIN',
        'lock_reacquire_predict_horizon_max': 'LOCK_REACQUIRE_PREDICT_HORIZON_MAX',
        'lock_mode_acquire_frames': 'LOCK_MODE_ACQUIRE_FRAMES',
        'lock_mode_release_frames': 'LOCK_MODE_RELEASE_FRAMES',
        'active_id_switch_cooldown_frames': 'ACTIVE_ID_SWITCH_COOLDOWN_FRAMES',
        'active_id_switch_allow_if_lost_frames': 'ACTIVE_ID_SWITCH_ALLOW_IF_LOST_FRAMES',
        'active_strict_lock_switch': 'ACTIVE_STRICT_LOCK_SWITCH',
        'track_state_acquire_frames': 'TRACK_STATE_ACQUIRE_FRAMES',
        'track_state_lost_frames': 'TRACK_STATE_LOST_FRAMES',
        'track_state_reset_frames': 'TRACK_STATE_RESET_FRAMES',
        'class_ema_alpha': 'CLASS_EMA_ALPHA',
        'drone_lock_score_min': 'DRONE_LOCK_SCORE_MIN',
        'drone_reacquire_score_min': 'DRONE_REACQUIRE_SCORE_MIN',
        'show_gt_overlay': 'SHOW_GT_OVERLAY',
        'show_debug_timings': 'SHOW_DEBUG_TIMINGS',
        'show_focus_window': 'SHOW_FOCUS_WINDOW',
        'show_lock_search_window': 'SHOW_LOCK_SEARCH_WINDOW',
        'lock_focus_only': 'LOCK_FOCUS_ONLY',
        'disable_night_on_lock': 'DISABLE_NIGHT_ON_LOCK',
        'reticle_overlay_enabled': 'RETICLE_OVERLAY_ENABLED',
        'reticle_half_size': 'RETICLE_HALF_SIZE',
        'reticle_dot_radius': 'RETICLE_DOT_RADIUS',
        'reticle_center_alpha': 'RETICLE_CENTER_ALPHA',
        'reticle_hold_frames': 'RETICLE_HOLD_FRAMES',
        'confidence_ema_alpha': 'CONFIDENCE_EMA_ALPHA',
        'confidence_display_update_sec': 'CONFIDENCE_DISPLAY_UPDATE_SEC',
        'night_max_area': 'NIGHT_MAX_AREA',
        'night_track_dist': 'NIGHT_TRACK_DIST',
        'night_lost_max': 'NIGHT_LOST_MAX',
        'night_max_detections': 'NIGHT_MAX_DETECTIONS',
        'night_min_speed': 'NIGHT_MIN_SPEED',
        'night_max_speed': 'NIGHT_MAX_SPEED',
        'night_hotspot_enabled': 'NIGHT_HOTSPOT_ENABLED',
        'night_hotspot_kernel': 'NIGHT_HOTSPOT_KERNEL',
        'night_hotspot_thresh': 'NIGHT_HOTSPOT_THRESH',
        'night_hotspot_top_k': 'NIGHT_HOTSPOT_TOP_K',
        'night_contour_enabled': 'NIGHT_CONTOUR_ENABLED',
        'night_peak_enabled': 'NIGHT_PEAK_ENABLED',
        'night_peak_thresh': 'NIGHT_PEAK_THRESH',
        'night_peak_box': 'NIGHT_PEAK_BOX',
        'night_peak_nms_dist': 'NIGHT_PEAK_NMS_DIST',
        'night_peak_top_k': 'NIGHT_PEAK_TOP_K',
        'night_peak_require_motion': 'NIGHT_PEAK_REQUIRE_MOTION',
        'night_peak_min_motion_pixels': 'NIGHT_PEAK_MIN_MOTION_PIXELS',
        'night_sticky_enabled': 'NIGHT_STICKY_ENABLED',
        'night_sticky_radius': 'NIGHT_STICKY_RADIUS',
        'night_sticky_missing_max': 'NIGHT_STICKY_MISSING_MAX',
        'night_active_hold_radius': 'NIGHT_ACTIVE_HOLD_RADIUS',
        'night_confirm': 'NIGHT_CONFIRM',
        'night_hist_len': 'NIGHT_HIST_LEN',
        'night_grid_cell': 'NIGHT_GRID_CELL',
        'night_border': 'NIGHT_BORDER',
        'night_max_ar': 'NIGHT_MAX_AR',
        'night_run_when_primary_seen': 'NIGHT_RUN_WHEN_PRIMARY_SEEN',
        'night_primary_cooldown': 'NIGHT_PRIMARY_COOLDOWN',
        'auto_scene_detect': 'AUTO_SCENE_DETECT',
        'auto_scene_night_brightness_max': 'AUTO_SCENE_NIGHT_BRIGHTNESS_MAX',
        'auto_scene_confirm_frames': 'AUTO_SCENE_CONFIRM_FRAMES',
        'auto_scene_sample_interval': 'AUTO_SCENE_SAMPLE_INTERVAL',
        'auto_scene_day_night_enabled': 'AUTO_SCENE_DAY_NIGHT_ENABLED',
        'auto_scene_night_night_enabled': 'AUTO_SCENE_NIGHT_NIGHT_ENABLED',
        'auto_scene_night_conf': 'AUTO_SCENE_NIGHT_CONF',
        'auto_scene_night_mot_thresh': 'AUTO_SCENE_NIGHT_MOT_THRESH',
        'auto_scene_night_diff_thresh': 'AUTO_SCENE_NIGHT_DIFF_THRESH',
        'auto_scene_ir_sat_max': 'AUTO_SCENE_IR_SAT_MAX',
        'auto_scene_ir_night_enabled': 'AUTO_SCENE_IR_NIGHT_ENABLED',
        'auto_scene_ir_conf': 'AUTO_SCENE_IR_CONF',
        'auto_scene_ir_mot_thresh': 'AUTO_SCENE_IR_MOT_THRESH',
        'auto_scene_ir_diff_thresh': 'AUTO_SCENE_IR_DIFF_THRESH',
        'auto_scene_ir_peak_enabled': 'AUTO_SCENE_IR_PEAK_ENABLED',
        'auto_scene_ir_contour_enabled': 'AUTO_SCENE_IR_CONTOUR_ENABLED',
        'auto_scene_ir_peak_thresh': 'AUTO_SCENE_IR_PEAK_THRESH',
        'auto_scene_ir_peak_box': 'AUTO_SCENE_IR_PEAK_BOX',
        'auto_scene_ir_peak_nms_dist': 'AUTO_SCENE_IR_PEAK_NMS_DIST',
        'auto_scene_ir_peak_top_k': 'AUTO_SCENE_IR_PEAK_TOP_K',
        'auto_scene_ir_peak_require_motion': 'AUTO_SCENE_IR_PEAK_REQUIRE_MOTION',
        'auto_scene_ir_peak_min_motion_pixels': 'AUTO_SCENE_IR_PEAK_MIN_MOTION_PIXELS',
        'display_min_hit_streak_primary': 'DISPLAY_MIN_HIT_STREAK_PRIMARY',
        'display_min_hit_streak_night': 'DISPLAY_MIN_HIT_STREAK_NIGHT',
        'display_max_lost_frames': 'DISPLAY_MAX_LOST_FRAMES',
        'lock_event_log_enabled': 'LOCK_EVENT_LOG_ENABLED',
        'lock_event_log_path': 'LOCK_EVENT_LOG_PATH',
        'show_trails': 'SHOW_TRAILS',
        'operator_minimal_overlay': 'OPERATOR_MINIMAL_OVERLAY',
    }
    for key, value in overrides.items():
        attr = mapping.get(key)
        if attr is None:
            continue
        if hasattr(cfg, attr):
            setattr(cfg, attr, value)
    return cfg


def load_preset(name: str, cfg: Config | None = None) -> tuple[Config, dict[str, Any]]:
    cfg = cfg or Config()
    path = PRESET_DIR / f'{name}.yaml'
    data = load_yaml(path)
    cfg = apply_overrides(cfg, data)
    return cfg, data


def save_profile(path: str | Path, profile: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(profile, sort_keys=False, allow_unicode=False))


def load_profile(path: str | Path) -> dict[str, Any]:
    return load_yaml(path)


def config_to_profile(cfg: Config) -> dict[str, Any]:
    return asdict(cfg)
