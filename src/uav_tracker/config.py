from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class Config:
    VIDEO_SOURCE: Union[int, str] = 0
    RUNTIME_MODE: str = 'research'

    MODEL_PATH: str = 'runs/detect/runs/drone_bird_probe_fast/weights/best.pt'
    CONF_THRESH: float = 0.30
    IOU_THRESH: float = 0.45
    IMG_SIZE: int = 640
    DEVICE: str = 'mps'
    CLASSES: Optional[list] = None
    PREFER_CLASS_ID: int = 0
    SMALL_TARGET_IMG_SIZE: int = 960
    SMALL_TARGET_CONF: float = 0.15

    ADAPTIVE_SCAN_ENABLED: bool = True
    GLOBAL_SCAN_INTERVAL: int = 6
    LOCAL_TRACK_IMG_SIZE: int = 640
    LOCAL_TRACK_CONF: float = 0.10
    LOCAL_TRACK_PADDING: int = 132
    LOCAL_TRACK_MIN_SIZE: int = 192
    LOCAL_TRACK_MAX_SIZE: int = 512
    LOCAL_VALIDATE_INTERVAL: int = 3
    LOCAL_SMALL_BOX_AREA: int = 1200
    LOCAL_SMALL_BOX_RATIO: float = 0.003
    LOCAL_SMALL_IMG_SIZE: int = 960
    LOCAL_SMALL_CONF: float = 0.08
    LOCAL_BOOST_LOCK_SCORE_THRESH: float = 0.55

    LOCK_TRACKER_ENABLED: bool = True
    LOCK_TRACKER_SEARCH_SCALE: float = 3.0
    LOCK_TRACKER_MIN_SCORE: float = 0.42
    LOCK_TRACKER_UPDATE_ALPHA: float = 0.18

    ROI_ASSIST_ENABLED: bool = True
    ROI_ASSIST_ON_SMALL_TARGET_ONLY: bool = True
    ROI_DIFF_THRESH: int = 14
    ROI_MIN_AREA: int = 4
    ROI_MAX_AREA: int = 600
    ROI_PADDING: int = 72
    ROI_MIN_SIZE: int = 160
    ROI_MAX_CANDIDATES: int = 3
    ROI_CONF_THRESH: float = 0.12
    ROI_IMG_SIZE: int = 960

    BUDGET_ENABLED: bool = True
    BUDGET_TARGET_FPS: float = 24.0
    BUDGET_HIGH_LOAD: float = 1.18
    BUDGET_LOW_LOAD: float = 0.82
    BUDGET_LEVEL_MAX: int = 2
    BUDGET_ROI_MIN_CANDIDATES: int = 1
    BUDGET_NIGHT_SKIP_LEVEL1: int = 2
    BUDGET_NIGHT_SKIP_LEVEL2: int = 3
    BUDGET_ROI_SKIP_LEVEL2: int = 2
    BUDGET_SCAN_INTERVAL_BOOST_PER_LEVEL: int = 1
    BUDGET_LOCAL_VALIDATE_BOOST_PER_LEVEL: int = 1

    SMOOTH_ALPHA: float = 0.4
    SPEED_WEIGHT: float = 0.7
    VELOCITY_ALPHA: float = 0.60
    LOCK_CONFIRM_FRAMES: int = 5
    LOCK_REACQUIRE_DIST: int = 120
    LOCK_REACQUIRE_PREDICT_GAIN: float = 1.0
    LOCK_REACQUIRE_PREDICT_HORIZON_MAX: int = 4
    LOCK_LOST_GRACE: int = 2
    LOCK_MODE_ACQUIRE_FRAMES: int = 2
    LOCK_MODE_RELEASE_FRAMES: int = 6
    ACTIVE_ID_SWITCH_COOLDOWN_FRAMES: int = 30
    ACTIVE_ID_SWITCH_ALLOW_IF_LOST_FRAMES: int = 6
    ACTIVE_STRICT_LOCK_SWITCH: bool = True
    TRACK_STATE_ACQUIRE_FRAMES: int = 3
    TRACK_STATE_LOST_FRAMES: int = 8
    TRACK_STATE_RESET_FRAMES: int = 40
    CLASS_EMA_ALPHA: float = 0.18
    DRONE_LOCK_SCORE_MIN: float = 0.62
    DRONE_REACQUIRE_SCORE_MIN: float = 0.48
    LOCK_FOCUS_ONLY: bool = True
    DISABLE_NIGHT_ON_LOCK: bool = True
    SHOW_ONLY_ACTIVE_ON_LOCK: bool = True

    NIGHT_ENABLED: bool = True
    NIGHT_MIN_AREA: int = 3
    NIGHT_MAX_AREA: int = 200
    NIGHT_MOT_THRESH: int = 18
    NIGHT_DIFF_THRESH: int = 12
    NIGHT_HIST_LEN: int = 5
    NIGHT_CONFIRM: int = 3
    NIGHT_BORDER: int = 4
    NIGHT_MAX_AR: float = 3.0
    NIGHT_TRACK_DIST: int = 42
    NIGHT_LOST_MAX: int = 8
    NIGHT_RUN_WHEN_PRIMARY_SEEN: bool = False
    NIGHT_PRIMARY_COOLDOWN: int = 4
    YOLO_LOST_MAX: int = 12

    DISPLAY_MIN_HIT_STREAK_PRIMARY: int = 1
    DISPLAY_MIN_HIT_STREAK_NIGHT: int = 3
    DISPLAY_MAX_LOST_FRAMES: int = 2
    LOCK_EVENT_LOG_ENABLED: bool = False
    LOCK_EVENT_LOG_PATH: str = ''

    SHOW_GT_OVERLAY: bool = True
    SHOW_DEBUG_TIMINGS: bool = True
    SHOW_FOCUS_WINDOW: bool = True
    SHOW_LOCK_SEARCH_WINDOW: bool = False
    SHOW_NIGHT_DOTS: bool = True
    SHOW_TRAILS: bool = True
    OPERATOR_MINIMAL_OVERLAY: bool = True
    RETICLE_OVERLAY_ENABLED: bool = True
    RETICLE_HALF_SIZE: int = 84
    RETICLE_DOT_RADIUS: int = 5
    RETICLE_CENTER_ALPHA: float = 0.30
    RETICLE_HOLD_FRAMES: int = 8
    CONFIDENCE_EMA_ALPHA: float = 0.12
    CONFIDENCE_DISPLAY_UPDATE_SEC: float = 5.0
    TRAIL_LEN: int = 30
