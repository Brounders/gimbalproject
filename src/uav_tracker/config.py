import warnings
from dataclasses import dataclass, field
from typing import Any, Optional, Union

# RuntimeConfigView is defined at the bottom of this module (after Config).


@dataclass
class Config:
    """Flat configuration dataclass for the UAV tracker.

    Fields are grouped into logical sections by comment headers.
    All field names and defaults are stable — external code uses cfg.FIELD_NAME directly.
    For nested grouping with a breaking API change, see BRIEF-20260314-030.

    Sections:
        Source & Runtime   — video source, mode, device
        Model              — YOLO model path, thresholds, inference size
        Adaptive Scan      — global/local scan scheduling and ROI sizing
        Lock Tracker       — template-matching lock parameters
        ROI Assist         — motion-ROI proposal parameters
        Budget Controller  — CPU load adaptation
        Tracking & Lock    — target state machine, lock policy, ID switches
        Night Detector     — small-target MOG2/diff detector
        Display & Overlay  — HUD, trails, reticle, confidence display
        Auto Scene         — automatic day/night/IR scene switching
        Bbox Smoothing     — display-side bbox EMA to reduce visual jitter
    """

    # ── Source & Runtime ────────────────────────────────────────────────────
    VIDEO_SOURCE: Union[int, str] = 0
    RUNTIME_MODE: str = 'research'
    FALLBACK_FPS: float = 25.0          # used when source FPS is unknown
    SOURCE_FPS_MIN_VALID: float = 1.0   # below this source FPS is treated as unknown
    OUTPUT_FPS_FALLBACK: float = 20.0   # video writer FPS when source FPS is unknown

    # ── Model ───────────────────────────────────────────────────────────────
    MODEL_PATH: str = 'runs/detect/runs/drone_bird_probe_fast/weights/best.pt'
    CONF_THRESH: float = 0.30
    IOU_THRESH: float = 0.45
    IMG_SIZE: int = 640
    DEVICE: str = 'mps'
    CLASSES: Optional[list] = None
    IGNORE_ZONES: list[dict[str, Any]] = field(default_factory=list)
    DETECTION_MAX_AREA_RATIO: float = 0.0
    DETECTION_MAX_WIDTH_RATIO: float = 0.0
    DETECTION_MAX_HEIGHT_RATIO: float = 0.0
    PREFER_CLASS_ID: int = 0
    SMALL_TARGET_IMG_SIZE: int = 960
    SMALL_TARGET_CONF: float = 0.15
    INFERENCE_TIMEOUT_SEC: float = 8.0  # BUG-007: max seconds before inference is considered hung (MPS warmup ~1-5s)

    # ── Adaptive Scan ────────────────────────────────────────────────────────
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

    # ── Lock Tracker (template matching) ────────────────────────────────────
    LOCK_TRACKER_ENABLED: bool = True
    LOCK_TRACKER_SEARCH_SCALE: float = 3.0
    LOCK_TRACKER_MIN_SCORE: float = 0.42
    LOCK_TRACKER_UPDATE_ALPHA: float = 0.18
    LOCK_TRACKER_DRIFT_MAX_LOW: int = 8    # consecutive low-score frames before drift reset (BUG-003)

    # ── ROI Assist ───────────────────────────────────────────────────────────
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

    # ── Budget Controller ────────────────────────────────────────────────────
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

    # ── Tracking & Lock Policy ───────────────────────────────────────────────
    SMOOTH_ALPHA: float = 0.4
    SPEED_WEIGHT: float = 0.7
    VELOCITY_ALPHA: float = 0.60
    LOCK_CONFIRM_FRAMES: int = 5
    LOCK_REACQUIRE_DIST: int = 120
    LOCK_REACQUIRE_DIST_MAX: int = 300  # hard cap regardless of speed/lost_frames (BUG-002)
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
    LOCK_EVENT_LOG_ENABLED: bool = False
    LOCK_EVENT_LOG_PATH: str = ''
    FRAME_TELEMETRY_LOG_ENABLED: bool = False
    FRAME_TELEMETRY_LOG_PATH: str = 'runs/telemetry/frame_results.jsonl'
    FRAME_TELEMETRY_FLUSH_EVERY: int = 30
    YOLO_LOST_MAX: int = 12

    # ── select_active() scoring weights (target_manager.py) ─────────────────
    SELECT_ACTIVE_CONF_WEIGHT: float = 1.2     # conf contribution in select_active()
    SELECT_ACTIVE_STREAK_CAP: float = 4.0      # max hit_streak bonus in select_active()
    SELECT_ACTIVE_STREAK_WEIGHT: float = 0.35  # per-frame hit_streak bonus weight
    SELECT_ACTIVE_LOST_PENALTY: float = 0.8    # per-frame lost_frames penalty + night src penalty
    SELECT_ACTIVE_DRONE_WEIGHT: float = 2.8    # drone_score multiplier for primary-source targets
    SELECT_ACTIVE_MIN_SPEED: float = 1.0       # min speed threshold to accept best candidate

    # ── Reacquire gate geometry (target_manager.py) ──────────────────────────
    REACQUIRE_SPEED_DIST_CAP: int = 90         # max speed-based dist extension (px)
    REACQUIRE_SPEED_MULT: float = 1.8          # speed → dist extension multiplier
    REACQUIRE_LOST_MULT: int = 12              # lost_frames → dist extension multiplier
    REACQUIRE_PRED_GATE_CAP: int = 70          # max speed-based prediction gate extension (px)
    REACQUIRE_PRED_GATE_SPEED_MULT: float = 2.0  # speed → pred gate extension multiplier

    # ── Focus-mode reacquire gate (target_manager.py) ───────────────────────
    FOCUS_MAX_DIST_SPEED_CAP: int = 70         # max speed-based extension for focus reacquire gate (px)
    FOCUS_MAX_DIST_SPEED_MULT: float = 1.6     # speed → focus reacquire gate extension multiplier

    # ── ROI overlap filter (target_manager.py) ───────────────────────────────
    ROI_OVERLAP_IOU_THRESH: float = 0.35       # iou_thresh for _overlaps_any() primary filter

    # ── Lock-score local-validation thresholds (pipeline.py) ─────────────────
    LOCK_SCORE_VALIDATE_MARGIN: float = 0.12   # margin added to LOCK_TRACKER_MIN_SCORE for validate trigger
    LOCK_SCORE_VALIDATE_MIN: float = 0.55      # absolute min lock_score that skips local validation

    # ── Night Detector (MOG2 + frame-diff small-target) ──────────────────────
    NIGHT_ENABLED: bool = True
    NIGHT_MOG2_HISTORY: int = 50       # MOG2 background history length (frames)
    NIGHT_MOG2_VAR_THRESH: int = 25    # MOG2 pixel variance threshold
    NIGHT_BLUR_KERNEL: int = 5         # Gaussian blur kernel size (must be odd)
    NIGHT_MORPH_KERNEL: int = 3        # Morphology open/close kernel size
    NIGHT_GRID_CELL: int = 8           # Candidate position grid quantization (px)
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
    NIGHT_MAX_DETECTIONS: int = 0
    NIGHT_MIN_SPEED: float = 0.0
    NIGHT_MAX_SPEED: float = 0.0
    NIGHT_HOTSPOT_ENABLED: bool = False
    NIGHT_HOTSPOT_KERNEL: int = 17
    NIGHT_HOTSPOT_THRESH: int = 18
    NIGHT_HOTSPOT_TOP_K: int = 0
    NIGHT_CONTOUR_ENABLED: bool = True
    NIGHT_PEAK_ENABLED: bool = False
    NIGHT_PEAK_THRESH: int = 28
    NIGHT_PEAK_BOX: int = 24
    NIGHT_PEAK_NMS_DIST: int = 12
    NIGHT_PEAK_TOP_K: int = 0
    NIGHT_PEAK_REQUIRE_MOTION: bool = False
    NIGHT_PEAK_MIN_MOTION_PIXELS: int = 1
    NIGHT_STICKY_ENABLED: bool = False
    NIGHT_STICKY_RADIUS: int = 80
    NIGHT_STICKY_MISSING_MAX: int = 4
    NIGHT_ACTIVE_HOLD_RADIUS: int = 0
    NIGHT_RUN_WHEN_PRIMARY_SEEN: bool = False
    NIGHT_PRIMARY_COOLDOWN: int = 4

    # ── Display & Overlay ────────────────────────────────────────────────────
    DISPLAY_MIN_HIT_STREAK_PRIMARY: int = 1
    DISPLAY_MIN_HIT_STREAK_NIGHT: int = 3
    DISPLAY_MAX_LOST_FRAMES: int = 2
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

    # ── Auto Scene Detection (day / night / IR) ──────────────────────────────
    # Active when AUTO_SCENE_DETECT=True (e.g. in Auto operator mode).
    AUTO_SCENE_DETECT: bool = False
    AUTO_SCENE_NIGHT_BRIGHTNESS_MAX: int = 50   # mean Y < this → night scene
    AUTO_SCENE_CONFIRM_FRAMES: int = 30         # consecutive frames before scene switch
    AUTO_SCENE_SAMPLE_INTERVAL: int = 10        # analyze every N frames (performance)
    AUTO_SCENE_NIGHT_CONF: float = 0.12         # CONF_THRESH override in night scene
    AUTO_SCENE_NIGHT_MOT_THRESH: int = 12       # NIGHT_MOT_THRESH override in night scene
    AUTO_SCENE_NIGHT_DIFF_THRESH: int = 8       # NIGHT_DIFF_THRESH override in night scene
    AUTO_SCENE_DAY_NIGHT_ENABLED: bool = False  # day scene must not run motion/night detector by default
    AUTO_SCENE_NIGHT_NIGHT_ENABLED: bool = True
    # IR/thermal detection: low-saturation heuristic (HSV S channel).
    AUTO_SCENE_IR_SAT_MAX: int = 25             # mean HSV-S < this → IR candidate
    AUTO_SCENE_IR_NIGHT_ENABLED: bool = True
    AUTO_SCENE_IR_CONF: float = 0.10            # CONF_THRESH override in IR scene
    AUTO_SCENE_IR_MOT_THRESH: int = 8           # NIGHT_MOT_THRESH override in IR scene
    AUTO_SCENE_IR_DIFF_THRESH: int = 6          # NIGHT_DIFF_THRESH override in IR scene
    AUTO_SCENE_IR_PEAK_ENABLED: bool = True
    AUTO_SCENE_IR_CONTOUR_ENABLED: bool = False
    AUTO_SCENE_IR_PEAK_THRESH: int = 24
    AUTO_SCENE_IR_PEAK_BOX: int = 28
    AUTO_SCENE_IR_PEAK_NMS_DIST: int = 14
    AUTO_SCENE_IR_PEAK_TOP_K: int = 80
    AUTO_SCENE_IR_PEAK_REQUIRE_MOTION: bool = True
    AUTO_SCENE_IR_PEAK_MIN_MOTION_PIXELS: int = 1
    # Lock hardening for night/IR: more hits required before confirming lock.
    AUTO_SCENE_NIGHT_LOCK_CONFIRM: int = 8      # LOCK_CONFIRM_FRAMES override in night/IR
    AUTO_SCENE_NIGHT_DRONE_LOCK_SCORE: float = 0.75  # DRONE_LOCK_SCORE_MIN override in night/IR
    # TASK-103c v2: multi-ROI + 5-feature classifier parameters.
    AUTO_SCENE_IR_EDGE_MAX: float = 0.12        # max edge_density for IR (above = EO-overcast guard)
    AUTO_SCENE_IR_HOT_FRAC: float = 0.005       # min hot_pixel_frac to confirm IR (hot spots)
    AUTO_SCENE_STABILITY_WINDOW: int = 30       # sliding-window size for scene stability ratio
    # TASK-103d: Unified Proposal Layer trust-based target selection.
    TRUST_SWITCH_MARGIN: float = 0.25           # best must beat active by 25% to switch

    # ── Bbox Smoothing (display-side EMA to reduce visual jitter) ────────────
    SMOOTH_BBOX_ALPHA: float = 0.35             # EMA alpha for position (higher = more responsive)
    SMOOTH_BBOX_SIZE_ALPHA: float = 0.20        # EMA alpha for width/height (softer)
    SMOOTH_BBOX_HOLD_FRAMES: int = 4            # hold last bbox N frames after target dropout
    DISPLAY_STATE_HOLD_FRAMES: int = 3          # hold display tracking state N frames on downgrade

    # ── ActionPolicy guarded behavior wiring (ALG-001 v1.1) ──────────────────
    # OFF by default: pipeline records ActionPolicy decisions as telemetry only
    # and TemplateLockTracker/TargetManager behavior is unchanged.
    # ON: TrackingAction.DROP_LOCK additionally clears the active target and
    # resets the template lock one tick earlier than the natural age-based drop.
    # All other actions remain observation-only — the flag can never extend a
    # lock, only accelerate dropping a clearly-stale one.
    # Night gate semantics: IR/thermal is the primary night evidence; visible
    # RGB-night is diagnostic-only and must not be treated as a behavior gate.
    ACTION_POLICY_BEHAVIOR_ENABLED: bool = False

    # ── Operator target override (manual correction backend) ────────────────
    # OFF by default: UI/operator input can be queued but will not alter target
    # state until an explicit preset enables it.
    OPERATOR_OVERRIDE_ENABLED: bool = False
    OPERATOR_OVERRIDE_INSTANT_LOCK: bool = True
    OPERATOR_OVERRIDE_BOX_SIZE: int = 64
    OPERATOR_HOLD_GRACE_FRAMES: int = 20
    OPERATOR_REFINE_SEED_BBOX: bool = True
    OPERATOR_REFINE_PADDING: int = 18
    OPERATOR_TEMPLATE_COUNT: int = 3
    OPERATOR_ANNOTATION_LOG_ENABLED: bool = False
    OPERATOR_ANNOTATION_LOG_PATH: str = ''

    def __post_init__(self) -> None:
        """Auto-validate on construction (Session 7 + A1d merge).

        More comprehensive than validate() — checks EMA bounds, budget loads,
        and stride alignment in addition to the basic range checks.
        """
        # Detection thresholds must be strictly in (0, 1)
        for name in ('CONF_THRESH', 'IOU_THRESH'):
            v = getattr(self, name)
            if not (0.0 < v < 1.0):
                raise ValueError(f"Config.{name}={v!r} must be in (0, 1)")
        # EMA alpha fields must be in [0, 1]
        for name in (
            'SMOOTH_ALPHA', 'VELOCITY_ALPHA', 'CLASS_EMA_ALPHA',
            'CONFIDENCE_EMA_ALPHA', 'SMOOTH_BBOX_ALPHA', 'SMOOTH_BBOX_SIZE_ALPHA',
            'LOCK_TRACKER_UPDATE_ALPHA', 'RETICLE_CENTER_ALPHA',
        ):
            v = getattr(self, name)
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"Config.{name}={v!r} must be in [0, 1]")
        if self.IMG_SIZE <= 0:
            raise ValueError(f"Config.IMG_SIZE={self.IMG_SIZE!r} must be > 0")
        if self.ROI_IMG_SIZE <= 0:
            raise ValueError(f"ROI_IMG_SIZE={self.ROI_IMG_SIZE!r} must be > 0")
        if not (0.0 < self.ROI_CONF_THRESH < 1.0):
            raise ValueError(f"ROI_CONF_THRESH={self.ROI_CONF_THRESH!r} must be in (0, 1)")
        if self.NIGHT_CONFIRM < 1:
            raise ValueError(f"NIGHT_CONFIRM={self.NIGHT_CONFIRM!r} must be >= 1")
        if self.LOCK_CONFIRM_FRAMES < 1:
            raise ValueError(f"LOCK_CONFIRM_FRAMES={self.LOCK_CONFIRM_FRAMES!r} must be >= 1")
        if self.BUDGET_TARGET_FPS <= 0:
            raise ValueError(f"BUDGET_TARGET_FPS={self.BUDGET_TARGET_FPS!r} must be > 0")
        if self.BUDGET_HIGH_LOAD <= self.BUDGET_LOW_LOAD:
            raise ValueError(
                f"Config.BUDGET_HIGH_LOAD={self.BUDGET_HIGH_LOAD!r} must be > "
                f"BUDGET_LOW_LOAD={self.BUDGET_LOW_LOAD!r}"
            )
        if self.TRACK_STATE_ACQUIRE_FRAMES < 1:
            raise ValueError(
                f"Config.TRACK_STATE_ACQUIRE_FRAMES={self.TRACK_STATE_ACQUIRE_FRAMES!r} must be >= 1"
            )
        if self.LOCK_LOST_GRACE < 0:
            raise ValueError(f"Config.LOCK_LOST_GRACE={self.LOCK_LOST_GRACE!r} must be >= 0")
        if self.IMG_SIZE % 32 != 0:
            warnings.warn(
                f"Config.IMG_SIZE={self.IMG_SIZE} is not a multiple of 32 (YOLO stride).",
                UserWarning,
                stacklevel=2,
            )

    def validate(self) -> None:
        """Explicit validation shim — backward-compatible with A1d callers.

        Most checks now run automatically in __post_init__. This method exists
        so that pipeline.py and tests can call cfg.validate() explicitly after
        potential post-construction field mutations.
        """
        self.__post_init__()


@dataclass(frozen=True)
class RuntimeConfigSnapshot:
    """Immutable snapshot of hot-path config fields captured at frame-start.

    Captures a stable view of Config at the start of process_frame, independent
    of any mid-frame overrides applied by AutoSceneAdapter.

    See also: RuntimeConfigView (runtime_config.py) for the override-proxy approach.
    """
    CONF_THRESH: float
    IMG_SIZE: int
    DEVICE: str
    ADAPTIVE_SCAN_ENABLED: bool
    GLOBAL_SCAN_INTERVAL: int
    LOCK_TRACKER_ENABLED: bool
    LOCK_CONFIRM_FRAMES: int
    NIGHT_ENABLED: bool
    NIGHT_MOT_THRESH: int
    NIGHT_DIFF_THRESH: int
    ROI_ASSIST_ENABLED: bool
    DRONE_LOCK_SCORE_MIN: float
    BUDGET_ENABLED: bool

    @classmethod
    def from_config(cls, cfg: 'Config') -> 'RuntimeConfigSnapshot':
        return cls(
            CONF_THRESH=cfg.CONF_THRESH,
            IMG_SIZE=cfg.IMG_SIZE,
            DEVICE=cfg.DEVICE,
            ADAPTIVE_SCAN_ENABLED=cfg.ADAPTIVE_SCAN_ENABLED,
            GLOBAL_SCAN_INTERVAL=cfg.GLOBAL_SCAN_INTERVAL,
            LOCK_TRACKER_ENABLED=cfg.LOCK_TRACKER_ENABLED,
            LOCK_CONFIRM_FRAMES=cfg.LOCK_CONFIRM_FRAMES,
            NIGHT_ENABLED=cfg.NIGHT_ENABLED,
            NIGHT_MOT_THRESH=cfg.NIGHT_MOT_THRESH,
            NIGHT_DIFF_THRESH=cfg.NIGHT_DIFF_THRESH,
            ROI_ASSIST_ENABLED=cfg.ROI_ASSIST_ENABLED,
            DRONE_LOCK_SCORE_MIN=cfg.DRONE_LOCK_SCORE_MIN,
            BUDGET_ENABLED=cfg.BUDGET_ENABLED,
        )

# Backward-compat alias — Session 7 tests import this name from config
RuntimeConfigView = RuntimeConfigSnapshot
