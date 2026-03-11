from uav_tracker.config import Config


RUNTIME_MODES = ('research', 'operator', 'embedded')


def apply_runtime_mode(cfg: Config, mode: str) -> Config:
    mode = (mode or 'research').strip().lower()
    if mode not in RUNTIME_MODES:
        raise ValueError(f'Неизвестный runtime mode: {mode}')

    cfg.RUNTIME_MODE = mode

    if mode == 'research':
        cfg.SHOW_GT_OVERLAY = True
        cfg.SHOW_DEBUG_TIMINGS = True
        cfg.SHOW_FOCUS_WINDOW = True
        cfg.SHOW_TRAILS = True
        cfg.OPERATOR_MINIMAL_OVERLAY = False
        cfg.RETICLE_OVERLAY_ENABLED = True
        cfg.ADAPTIVE_SCAN_ENABLED = True
        cfg.ROI_ASSIST_ENABLED = True
        cfg.NIGHT_ENABLED = True
        cfg.LOCK_TRACKER_ENABLED = True
        cfg.SHOW_ONLY_ACTIVE_ON_LOCK = True
    elif mode == 'operator':
        cfg.SHOW_GT_OVERLAY = False
        cfg.SHOW_DEBUG_TIMINGS = False
        cfg.SHOW_FOCUS_WINDOW = False
        cfg.SHOW_TRAILS = False
        cfg.OPERATOR_MINIMAL_OVERLAY = True
        cfg.RETICLE_OVERLAY_ENABLED = False  # operator: bbox+ID overlay, reticle is research-only
        cfg.ADAPTIVE_SCAN_ENABLED = True
        cfg.ROI_ASSIST_ENABLED = True
        cfg.NIGHT_ENABLED = True
        cfg.LOCK_TRACKER_ENABLED = True
        cfg.SHOW_ONLY_ACTIVE_ON_LOCK = True
    elif mode == 'embedded':
        cfg.SHOW_GT_OVERLAY = False
        cfg.SHOW_DEBUG_TIMINGS = False
        cfg.SHOW_FOCUS_WINDOW = False
        cfg.SHOW_TRAILS = False
        cfg.OPERATOR_MINIMAL_OVERLAY = True
        cfg.RETICLE_OVERLAY_ENABLED = False  # embedded: bbox+ID overlay, reticle is research-only
        cfg.ADAPTIVE_SCAN_ENABLED = True
        cfg.ROI_ASSIST_ENABLED = False
        cfg.NIGHT_ENABLED = False
        cfg.LOCK_TRACKER_ENABLED = True
        cfg.GLOBAL_SCAN_INTERVAL = max(cfg.GLOBAL_SCAN_INTERVAL, 8)
        cfg.LOCAL_VALIDATE_INTERVAL = max(cfg.LOCAL_VALIDATE_INTERVAL, 4)
        cfg.SHOW_ONLY_ACTIVE_ON_LOCK = True

    return cfg
