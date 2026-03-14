import json
import logging
import time
from collections import deque
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

from uav_tracker.config import Config
from uav_tracker.detectors.night_detector import NightSmallTargetDetector
from uav_tracker.detectors.roi_assist import MotionROIProposer
from uav_tracker.runtime import create_detector_backend
from uav_tracker.runtime.base import Detection
from uav_tracker.tracking.lock_tracker import TemplateLockTracker
from uav_tracker.tracking.target_manager import TargetManager, TrackedTarget


logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}


from uav_tracker.frame_result import FrameOutput


class SequenceGroundTruth:
    def __init__(self, folder: Union[str, Path]):
        self.folder = Path(folder)
        self.label_path = self._resolve_label_path(self.folder)
        self.exist: list[int] = []
        self.gt_rect: list[list[int]] = []
        if self.label_path is not None:
            try:
                data = json.loads(self.label_path.read_text())
                self.exist = list(data.get('exist', []))
                self.gt_rect = list(data.get('gt_rect', []))
            except Exception:
                self.exist = []
                self.gt_rect = []

    @staticmethod
    def _resolve_label_path(folder: Path) -> Optional[Path]:
        for name in ('IR_label.json', 'label.json', 'gt.json'):
            path = folder / name
            if path.exists():
                return path
        return None

    def bbox_for(self, index: int) -> Optional[tuple[int, int, int, int]]:
        if index >= len(self.exist) or index >= len(self.gt_rect):
            return None
        if int(self.exist[index]) != 1:
            return None
        rect = self.gt_rect[index]
        if not rect or len(rect) < 4:
            return None
        x, y, w, h = [int(v) for v in rect[:4]]
        if w <= 0 or h <= 0:
            return None
        return x, y, x + w, y + h


class ImageSequenceCapture:
    def __init__(self, folder: Union[str, Path]):
        self.folder = Path(folder)
        self.files = sorted([p for p in self.folder.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS])
        self.index = 0
        self._opened = bool(self.files)
        self._shape: Optional[tuple[int, int]] = None
        if self._opened:
            first = cv2.imread(str(self.files[0]))
            if first is not None:
                self._shape = first.shape[:2]
            else:
                self._opened = False

    def isOpened(self) -> bool:
        return self._opened

    def read(self):
        if not self._opened or self.index >= len(self.files):
            return False, None
        frame = cv2.imread(str(self.files[self.index]))
        self.index += 1
        if frame is None:
            return False, None
        return True, frame

    def get(self, prop_id: int):
        if self._shape is None:
            return 0
        height, width = self._shape
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            return width
        if prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return height
        if prop_id == cv2.CAP_PROP_FPS:
            return 25.0
        if prop_id == cv2.CAP_PROP_FRAME_COUNT:
            return len(self.files)
        return 0

    def release(self):
        self._opened = False


def parse_video_source(video_source: Union[str, int]) -> Union[str, int]:
    if isinstance(video_source, int):
        return video_source
    if isinstance(video_source, str) and video_source.isdigit():
        return int(video_source)
    return video_source


def resolve_model_path(model_path: str) -> str:
    candidates = [
        model_path,
        'runs/detect/runs/drone_bird_probe_fast/weights/best.pt',
        'runs/detect/runs/drone_bird_v2/weights/best.pt',
        'runs/detect/runs/drone_bird_v1/weights/best.pt',
        'models/yolo11n.pt',
        'yolo11n.pt',
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return model_path


def apply_runtime_preset(cfg: Config, small_target_mode: bool = False, imgsz: Optional[int] = None, conf: Optional[float] = None) -> Config:
    cfg.IMG_SIZE = imgsz if imgsz is not None else cfg.IMG_SIZE
    cfg.CONF_THRESH = conf if conf is not None else cfg.CONF_THRESH
    if small_target_mode:
        cfg.IMG_SIZE = max(cfg.IMG_SIZE, cfg.SMALL_TARGET_IMG_SIZE)
        cfg.CONF_THRESH = min(cfg.CONF_THRESH, cfg.SMALL_TARGET_CONF)
    cfg.MODEL_PATH = resolve_model_path(cfg.MODEL_PATH)
    return cfg


def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    xi1, yi1 = max(a[0], b[0]), max(a[1], b[1])
    xi2, yi2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    if inter <= 0:
        return 0.0
    union_area = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union_area if union_area > 0 else 0.0


class TrackerPipeline:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.backend = create_detector_backend(cfg.MODEL_PATH, cfg.DEVICE)
        self.night = NightSmallTargetDetector(cfg)
        self.roi = MotionROIProposer(cfg)
        self.manager = TargetManager(cfg)
        self.lock_tracker = TemplateLockTracker(cfg)
        self.fps_buf = deque(maxlen=30)
        self.t_prev = time.perf_counter()
        self.frame_counter = 0
        self.lock_switch_count = 0
        self.lock_event_counts = {'acquired': 0, 'lost': 0, 'reacquired': 0, 'switch': 0}
        self._had_lock_before = False
        self._prev_focus_mode = False
        self._prev_active_id: Optional[int] = None
        self._video_elapsed_sec = 0.0
        self._fallback_fps = 25.0
        self._budget_level = 0
        self._budget_load_ema = 1.0
        self._last_frame_budget_ms = 0.0
        self._last_roi_budget_candidates = max(1, int(cfg.ROI_MAX_CANDIDATES))
        self._last_night_skip = 1
        self._confidence_ema = 0.0
        self._display_confidence = 0.0
        self._confidence_last_update_sec = 0.0
        self._reticle_center: Optional[tuple[float, float]] = None
        self._reticle_missing_streak = 0
        self._continuity_prev_active_id: Optional[int] = None
        self._continuity_transitions = 0
        self._continuity_same_id_transitions = 0
        self._continuity_id_changes = 0
        self._continuity_active_frames = 0
        self._continuity_lost_run = 0
        self._continuity_reacquire_gaps: list[int] = []
        self._tracking_state = 'SCAN'
        self._tracking_present_streak = 0
        self._tracking_missing_streak = 0
        self._tracking_had_target = False
        # Display-only state: lags behind real state to avoid visual flicker.
        self._display_tracking_state = 'SCAN'
        self._display_state_hold = 0

        # Auto scene detection state (TASK-020).
        self._auto_scene_state = 'day'       # 'day' or 'night'
        self._auto_scene_streak = 0          # consecutive frames in candidate state
        self._auto_scene_orig_conf = float(cfg.CONF_THRESH)
        self._auto_scene_orig_mot = int(cfg.NIGHT_MOT_THRESH)
        self._auto_scene_orig_diff = int(cfg.NIGHT_DIFF_THRESH)
        self._auto_scene_orig_lock_confirm = int(cfg.LOCK_CONFIRM_FRAMES)
        self._auto_scene_orig_drone_lock_score = float(cfg.DRONE_LOCK_SCORE_MIN)
        self._auto_scene_frame_tick = 0

        # Display bbox smoothing state (TASK-021).
        self._smooth_bbox: Optional[list[float]] = None   # [x1, y1, x2, y2] floats
        self._smooth_bbox_missing = 0

    def _update_video_time(self, source_fps: Optional[float]) -> None:
        if source_fps is not None and source_fps > 1.0:
            self._video_elapsed_sec += 1.0 / float(source_fps)
            return
        fallback = self.fps_buf[-1] if self.fps_buf else self._fallback_fps
        fallback = max(1.0, float(fallback))
        self._video_elapsed_sec += 1.0 / fallback

    def _lock_switches_per_min(self) -> float:
        if self._video_elapsed_sec < 5.0:
            return 0.0
        return self.lock_switch_count * 60.0 / self._video_elapsed_sec

    def _instant_tracking_confidence(self, active: Optional[TrackedTarget], lock_score: float) -> float:
        if active is None:
            return 0.0
        streak_norm = min(1.0, float(active.hit_streak) / max(1.0, float(self.cfg.LOCK_CONFIRM_FRAMES)))
        lock_norm = float(lock_score) if lock_score > 0.0 else float(active.conf)
        value = 0.45 * float(active.conf) + 0.35 * lock_norm + 0.20 * streak_norm
        if active.lost_frames > 0:
            value *= max(0.2, 1.0 - 0.2 * float(active.lost_frames))
        return max(0.0, min(1.0, value))

    def _update_display_confidence(self, active: Optional[TrackedTarget], lock_score: float) -> float:
        instant = self._instant_tracking_confidence(active, lock_score)
        alpha = max(0.01, min(0.95, float(self.cfg.CONFIDENCE_EMA_ALPHA)))
        self._confidence_ema = (1.0 - alpha) * self._confidence_ema + alpha * instant

        period = max(0.5, float(self.cfg.CONFIDENCE_DISPLAY_UPDATE_SEC))
        if self._video_elapsed_sec - self._confidence_last_update_sec >= period:
            self._display_confidence = self._confidence_ema
            self._confidence_last_update_sec = self._video_elapsed_sec

        if self.frame_counter <= 3:
            self._display_confidence = self._confidence_ema
        return max(0.0, min(1.0, self._display_confidence))

    def _update_reticle_center(self, active: Optional[TrackedTarget]) -> Optional[tuple[int, int]]:
        if active is not None:
            x1, y1, x2, y2 = active.bbox
            cx = float((x1 + x2) * 0.5)
            cy = float((y1 + y2) * 0.5)
            if active.lost_frames > 0:
                horizon = max(1, min(int(self.cfg.LOCK_REACQUIRE_PREDICT_HORIZON_MAX), active.lost_frames))
                gain = float(self.cfg.LOCK_REACQUIRE_PREDICT_GAIN)
                cx += float(active.vx) * horizon * gain
                cy += float(active.vy) * horizon * gain
            alpha = max(0.01, min(0.95, float(self.cfg.RETICLE_CENTER_ALPHA)))
            if self._reticle_center is None:
                self._reticle_center = (cx, cy)
            else:
                px, py = self._reticle_center
                self._reticle_center = (
                    (1.0 - alpha) * px + alpha * cx,
                    (1.0 - alpha) * py + alpha * cy,
                )
            self._reticle_missing_streak = 0
        elif self._reticle_center is not None:
            self._reticle_missing_streak += 1
            if self._reticle_missing_streak > max(1, int(self.cfg.RETICLE_HOLD_FRAMES)):
                self._reticle_center = None
                self._reticle_missing_streak = 0

        if self._reticle_center is None:
            return None
        return int(self._reticle_center[0]), int(self._reticle_center[1])

    def _update_continuity_metrics(self, active_id: Optional[int]) -> None:
        if active_id is not None:
            self._continuity_active_frames += 1

        prev = self._continuity_prev_active_id
        if prev is not None and active_id is not None:
            self._continuity_transitions += 1
            if prev == active_id:
                self._continuity_same_id_transitions += 1
            else:
                self._continuity_id_changes += 1

        if active_id is None:
            self._continuity_lost_run += 1
        else:
            if self._continuity_lost_run > 0:
                self._continuity_reacquire_gaps.append(self._continuity_lost_run)
                self._continuity_lost_run = 0

        self._continuity_prev_active_id = active_id

    def _continuity_score(self) -> float:
        if self._continuity_transitions <= 0:
            return 1.0 if self._continuity_active_frames > 0 else 0.0
        return float(self._continuity_same_id_transitions) / float(self._continuity_transitions)

    def _active_presence_rate(self) -> float:
        if self.frame_counter <= 0:
            return 0.0
        return float(self._continuity_active_frames) / float(self.frame_counter)

    def _median_reacquire_frames(self) -> float:
        if not self._continuity_reacquire_gaps:
            return 0.0
        return float(np.median(self._continuity_reacquire_gaps))

    def _update_tracking_state(self, active: Optional[TrackedTarget]) -> str:
        present = active is not None and int(active.lost_frames) <= int(self.cfg.LOCK_LOST_GRACE)
        acquire_frames = max(1, int(self.cfg.TRACK_STATE_ACQUIRE_FRAMES))
        lost_frames = max(1, int(self.cfg.TRACK_STATE_LOST_FRAMES))
        reset_frames = max(lost_frames + 1, int(self.cfg.TRACK_STATE_RESET_FRAMES))

        if present:
            self._tracking_present_streak += 1
            self._tracking_missing_streak = 0
            self._tracking_had_target = True
            if self._tracking_state != 'TRACK' and self._tracking_present_streak >= acquire_frames:
                self._tracking_state = 'TRACK'
        else:
            self._tracking_present_streak = 0
            self._tracking_missing_streak += 1
            if self._tracking_state == 'TRACK' and self._tracking_missing_streak >= lost_frames:
                self._tracking_state = 'LOST'
            elif self._tracking_state == 'LOST' and self._tracking_missing_streak >= reset_frames:
                self._tracking_state = 'SCAN'
                self._tracking_had_target = False
            elif not self._tracking_had_target:
                self._tracking_state = 'SCAN'

        if self._tracking_state == 'LOST' and present and self._tracking_present_streak >= acquire_frames:
            self._tracking_state = 'TRACK'
        return self._tracking_state

    def _get_display_tracking_state(self, real_state: str) -> str:
        """Return a display-smoothed tracking state.

        Upgrades (e.g. SCAN→TRACK) are applied immediately.
        Downgrades (e.g. TRACK→SCAN) are held for DISPLAY_STATE_HOLD_FRAMES
        frames to suppress momentary visual flicker without affecting metrics.
        """
        _ORDER = {'SCAN': 0, 'LOST': 1, 'TRACK': 2}
        hold = max(1, int(getattr(self.cfg, 'DISPLAY_STATE_HOLD_FRAMES', 3)))
        real_level = _ORDER.get(real_state, 0)
        disp_level = _ORDER.get(self._display_tracking_state, 0)
        if real_level >= disp_level:
            self._display_tracking_state = real_state
            self._display_state_hold = 0
        else:
            self._display_state_hold += 1
            if self._display_state_hold >= hold:
                self._display_tracking_state = real_state
                self._display_state_hold = 0
        return self._display_tracking_state

    def _adapt_auto_scene(self, frame: np.ndarray) -> None:
        """Auto scene detection: Day / Night / IR (TASK-020 + TASK-026).

        Runs every AUTO_SCENE_SAMPLE_INTERVAL frames.  Requires
        AUTO_SCENE_CONFIRM_FRAMES / SAMPLE_INTERVAL consecutive samples before switch.

        Scene classification (priority order):
          1. mean Y < NIGHT_BRIGHTNESS_MAX  → 'night'   (dark scene)
          2. mean HSV-S < IR_SAT_MAX        → 'ir'      (desaturated/thermal, any brightness)
          3. else                           → 'day'

        On switch: applies config overrides; on revert to 'day': restores originals.
        """
        if not getattr(self.cfg, 'AUTO_SCENE_DETECT', False):
            return
        self._auto_scene_frame_tick += 1
        interval = max(1, int(getattr(self.cfg, 'AUTO_SCENE_SAMPLE_INTERVAL', 10)))
        if self._auto_scene_frame_tick % interval != 0:
            return

        # Sample frame center crop (avoid border vignetting effects)
        h, w = frame.shape[:2]
        y0, y1 = h // 4, 3 * h // 4
        x0, x1 = w // 4, 3 * w // 4
        crop = frame[y0:y1, x0:x1]

        if crop.ndim == 3:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            mean_sat = float(np.mean(hsv[:, :, 1]))
        else:
            gray = crop
            mean_sat = 0.0  # grayscale input — treat as potentially IR

        mean_brightness = float(np.mean(gray))

        night_thresh = int(getattr(self.cfg, 'AUTO_SCENE_NIGHT_BRIGHTNESS_MAX', 50))
        ir_sat_max = int(getattr(self.cfg, 'AUTO_SCENE_IR_SAT_MAX', 25))
        confirm = max(1, int(getattr(self.cfg, 'AUTO_SCENE_CONFIRM_FRAMES', 30)))

        # Priority: dark → night; desaturated (any brightness) → ir; else → day
        if mean_brightness < night_thresh:
            candidate = 'night'
        elif mean_sat < ir_sat_max:
            candidate = 'ir'
        else:
            candidate = 'day'

        if candidate == self._auto_scene_state:
            self._auto_scene_streak = 0
            return

        self._auto_scene_streak += 1
        if self._auto_scene_streak < max(1, confirm // interval):
            return

        # Scene confirmed — apply overrides
        self._auto_scene_state = candidate
        self._auto_scene_streak = 0
        if candidate == 'night':
            self.cfg.CONF_THRESH = float(getattr(self.cfg, 'AUTO_SCENE_NIGHT_CONF', 0.12))
            self.cfg.NIGHT_MOT_THRESH = int(getattr(self.cfg, 'AUTO_SCENE_NIGHT_MOT_THRESH', 12))
            self.cfg.NIGHT_DIFF_THRESH = int(getattr(self.cfg, 'AUTO_SCENE_NIGHT_DIFF_THRESH', 8))
            self.cfg.LOCK_CONFIRM_FRAMES = int(getattr(self.cfg, 'AUTO_SCENE_NIGHT_LOCK_CONFIRM', 8))
            self.cfg.DRONE_LOCK_SCORE_MIN = float(getattr(self.cfg, 'AUTO_SCENE_NIGHT_DRONE_LOCK_SCORE', 0.75))
        elif candidate == 'ir':
            self.cfg.CONF_THRESH = float(getattr(self.cfg, 'AUTO_SCENE_IR_CONF', 0.10))
            self.cfg.NIGHT_MOT_THRESH = int(getattr(self.cfg, 'AUTO_SCENE_IR_MOT_THRESH', 8))
            self.cfg.NIGHT_DIFF_THRESH = int(getattr(self.cfg, 'AUTO_SCENE_IR_DIFF_THRESH', 6))
            self.cfg.LOCK_CONFIRM_FRAMES = int(getattr(self.cfg, 'AUTO_SCENE_NIGHT_LOCK_CONFIRM', 8))
            self.cfg.DRONE_LOCK_SCORE_MIN = float(getattr(self.cfg, 'AUTO_SCENE_NIGHT_DRONE_LOCK_SCORE', 0.75))
        else:  # day — restore originals
            self.cfg.CONF_THRESH = self._auto_scene_orig_conf
            self.cfg.NIGHT_MOT_THRESH = self._auto_scene_orig_mot
            self.cfg.NIGHT_DIFF_THRESH = self._auto_scene_orig_diff
            self.cfg.LOCK_CONFIRM_FRAMES = self._auto_scene_orig_lock_confirm
            self.cfg.DRONE_LOCK_SCORE_MIN = self._auto_scene_orig_drone_lock_score

    def _get_smooth_display_bbox(
        self, active: Optional[TrackedTarget]
    ) -> Optional[tuple[int, int, int, int]]:
        """Return EMA-smoothed bbox for display (TASK-021).

        Center position uses SMOOTH_BBOX_ALPHA.
        Width/height use softer SMOOTH_BBOX_SIZE_ALPHA to damp size jitter.
        Holds last bbox for SMOOTH_BBOX_HOLD_FRAMES when target is absent.
        """
        alpha_pos = max(0.05, min(0.95, float(getattr(self.cfg, 'SMOOTH_BBOX_ALPHA', 0.35))))
        alpha_sz = max(0.05, min(0.95, float(getattr(self.cfg, 'SMOOTH_BBOX_SIZE_ALPHA', 0.20))))
        hold = max(0, int(getattr(self.cfg, 'SMOOTH_BBOX_HOLD_FRAMES', 4)))

        if active is not None:
            x1, y1, x2, y2 = active.bbox
            cx, cy = float((x1 + x2) * 0.5), float((y1 + y2) * 0.5)
            w, h = float(x2 - x1), float(y2 - y1)
            if self._smooth_bbox is None:
                self._smooth_bbox = [cx, cy, w, h]
            else:
                scx, scy, sw, sh = self._smooth_bbox
                self._smooth_bbox = [
                    (1.0 - alpha_pos) * scx + alpha_pos * cx,
                    (1.0 - alpha_pos) * scy + alpha_pos * cy,
                    (1.0 - alpha_sz) * sw + alpha_sz * w,
                    (1.0 - alpha_sz) * sh + alpha_sz * h,
                ]
            self._smooth_bbox_missing = 0
        else:
            self._smooth_bbox_missing += 1
            if self._smooth_bbox_missing > hold:
                self._smooth_bbox = None
                return None

        if self._smooth_bbox is None:
            return None
        scx, scy, sw, sh = self._smooth_bbox
        sx1 = int(scx - sw * 0.5)
        sy1 = int(scy - sh * 0.5)
        sx2 = int(scx + sw * 0.5)
        sy2 = int(scy + sh * 0.5)
        return sx1, sy1, sx2, sy2

    def _effective_global_scan_interval(self) -> int:
        base = max(1, int(self.cfg.GLOBAL_SCAN_INTERVAL))
        if not self.cfg.BUDGET_ENABLED:
            return base
        boost = max(0, int(self.cfg.BUDGET_SCAN_INTERVAL_BOOST_PER_LEVEL))
        return max(1, base + boost * self._budget_level)

    def _effective_local_validate_interval(self) -> int:
        base = max(1, int(self.cfg.LOCAL_VALIDATE_INTERVAL))
        if not self.cfg.BUDGET_ENABLED:
            return base
        boost = max(0, int(self.cfg.BUDGET_LOCAL_VALIDATE_BOOST_PER_LEVEL))
        return max(1, base + boost * self._budget_level)

    def _effective_roi_max_candidates(self) -> int:
        base = max(1, int(self.cfg.ROI_MAX_CANDIDATES))
        if not self.cfg.BUDGET_ENABLED:
            return base
        min_candidates = max(1, int(self.cfg.BUDGET_ROI_MIN_CANDIDATES))
        return max(min_candidates, base - self._budget_level)

    def _effective_night_skip(self) -> int:
        if not self.cfg.BUDGET_ENABLED:
            return 1
        if self._budget_level <= 0:
            return 1
        if self._budget_level == 1:
            return max(1, int(self.cfg.BUDGET_NIGHT_SKIP_LEVEL1))
        return max(1, int(self.cfg.BUDGET_NIGHT_SKIP_LEVEL2))

    def _should_run_night_with_budget(self) -> bool:
        night_skip = self._effective_night_skip()
        self._last_night_skip = night_skip
        if night_skip <= 1:
            return True
        return (self.frame_counter % night_skip) == 0

    def _should_run_roi_with_budget(self) -> bool:
        if not self.cfg.BUDGET_ENABLED:
            return True
        skip = max(1, int(self.cfg.BUDGET_ROI_SKIP_LEVEL2))
        if self._budget_level < 2 or skip <= 1:
            return True
        return (self.frame_counter % skip) == 0

    def _update_budget_state(self, timings_ms: dict[str, float]) -> None:
        self._last_frame_budget_ms = (
            float(timings_ms.get('global', 0.0))
            + float(timings_ms.get('lock', 0.0))
            + float(timings_ms.get('local', 0.0))
            + float(timings_ms.get('roi', 0.0))
            + float(timings_ms.get('night', 0.0))
            + float(timings_ms.get('draw', 0.0))
        )
        if not self.cfg.BUDGET_ENABLED:
            self._budget_level = 0
            self._budget_load_ema = 1.0
            return

        target_fps = max(5.0, float(self.cfg.BUDGET_TARGET_FPS))
        target_ms = 1000.0 / target_fps
        load = self._last_frame_budget_ms / max(target_ms, 1.0)
        self._budget_load_ema = 0.86 * self._budget_load_ema + 0.14 * load

        max_level = max(0, int(self.cfg.BUDGET_LEVEL_MAX))
        high = float(self.cfg.BUDGET_HIGH_LOAD)
        low = float(self.cfg.BUDGET_LOW_LOAD)
        if self._budget_load_ema > high and self._budget_level < max_level:
            self._budget_level += 1
        elif self._budget_load_ema < low and self._budget_level > 0:
            self._budget_level -= 1

    def _update_lock_events(self) -> list[str]:
        events: list[str] = []
        focus_mode = self.manager.is_focus_mode()
        active_id = self.manager.active_id

        if not self._prev_focus_mode and focus_mode:
            if self._had_lock_before:
                self.lock_event_counts['reacquired'] += 1
                events.append(f'LOCK_REACQUIRED id={active_id}')
            else:
                self._had_lock_before = True
                self.lock_event_counts['acquired'] += 1
                events.append(f'LOCK_ACQUIRED id={active_id}')

        if self._prev_focus_mode and not focus_mode:
            self.lock_event_counts['lost'] += 1
            events.append(f'LOCK_LOST id={self._prev_active_id}')

        if (
            self._prev_focus_mode
            and focus_mode
            and self._prev_active_id is not None
            and active_id is not None
            and self._prev_active_id != active_id
        ):
            self.lock_switch_count += 1
            self.lock_event_counts['switch'] += 1
            events.append(f'LOCK_SWITCH {self._prev_active_id}->{active_id}')

        self._prev_focus_mode = focus_mode
        self._prev_active_id = active_id
        return events

    def _should_run_global_scan(self) -> tuple[bool, str]:
        active = self.manager.get_active_target()
        if not self.cfg.ADAPTIVE_SCAN_ENABLED:
            return True, 'GLOBAL-SCAN'
        if not self.manager.is_focus_mode() or active is None:
            return True, 'GLOBAL-SCAN'
        if active.lost_frames > self.cfg.LOCK_LOST_GRACE:
            return True, 'GLOBAL-RECOVERY'
        interval = self._effective_global_scan_interval()
        if self.frame_counter % interval == 0:
            return True, 'GLOBAL-RESCAN'
        return False, 'LOCK-TRACK'

    def _build_focus_roi(self, frame_shape: tuple[int, int, int]) -> Optional[tuple[int, int, int, int]]:
        active = self.manager.get_active_target()
        if active is None:
            return None
        h, w = frame_shape[:2]
        x1, y1, x2, y2 = active.raw_bbox
        box_size = max(x2 - x1, y2 - y1)
        size = max(self.cfg.LOCAL_TRACK_MIN_SIZE, box_size + self.cfg.LOCAL_TRACK_PADDING * 2)
        size = min(size, self.cfg.LOCAL_TRACK_MAX_SIZE, max(w, h))
        cx, cy = int(active.cx), int(active.cy)
        rx1 = max(0, cx - size // 2)
        ry1 = max(0, cy - size // 2)
        rx2 = min(w, rx1 + size)
        ry2 = min(h, ry1 + size)
        rx1 = max(0, rx2 - size)
        ry1 = max(0, ry2 - size)
        if rx2 <= rx1 or ry2 <= ry1:
            return None
        return int(rx1), int(ry1), int(rx2), int(ry2)

    def _offset_detection(self, det: Detection, offset: tuple[int, int], source: str) -> Detection:
        ox, oy = offset
        x1, y1, x2, y2 = det.bbox
        return Detection(
            bbox=(x1 + ox, y1 + oy, x2 + ox, y2 + oy),
            conf=det.conf,
            cls_id=det.cls_id,
            cx=det.cx + ox,
            cy=det.cy + oy,
            source=source,
            track_id=det.track_id,
        )

    def _select_best_local_detection(self, detections: list[Detection]) -> Optional[Detection]:
        active = self.manager.get_active_target()
        if active is None or not detections:
            return None
        best_det = None
        best_score = None
        for det in detections:
            dist = self.manager._dist(det.cx, det.cy, active.cx, active.cy)
            class_penalty = 0 if det.cls_id == self.cfg.PREFER_CLASS_ID else 1
            score = (class_penalty, dist, -det.conf)
            if best_score is None or score < best_score:
                best_score = score
                best_det = det
        return best_det

    def _local_validation_params(self, frame: np.ndarray, lock_score: float) -> tuple[int, float]:
        imgsz = int(self.cfg.LOCAL_TRACK_IMG_SIZE)
        conf = float(self.cfg.LOCAL_TRACK_CONF)
        active = self.manager.get_active_target()
        if active is None:
            return imgsz, conf

        x1, y1, x2, y2 = active.raw_bbox
        bw = max(1, int(x2 - x1))
        bh = max(1, int(y2 - y1))
        box_area = bw * bh
        frame_area = max(1, int(frame.shape[0] * frame.shape[1]))
        small_area_gate = max(int(self.cfg.LOCAL_SMALL_BOX_AREA), int(frame_area * float(self.cfg.LOCAL_SMALL_BOX_RATIO)))
        is_small_target = box_area <= small_area_gate
        weak_lock = lock_score < float(self.cfg.LOCAL_BOOST_LOCK_SCORE_THRESH)

        if is_small_target or weak_lock:
            imgsz = max(imgsz, int(self.cfg.LOCAL_SMALL_IMG_SIZE))
            conf = min(conf, float(self.cfg.LOCAL_SMALL_CONF))

        # Under heavy budget load keep full boost only for truly tiny targets.
        if self.cfg.BUDGET_ENABLED and self._budget_level >= 2 and not is_small_target:
            imgsz = int(self.cfg.LOCAL_TRACK_IMG_SIZE)
            conf = float(self.cfg.LOCAL_TRACK_CONF)
        return imgsz, conf

    def _run_local_validation(
        self,
        frame: np.ndarray,
        focus_roi: tuple[int, int, int, int],
        *,
        local_imgsz: int,
        local_conf: float,
    ) -> Optional[Detection]:
        x1, y1, x2, y2 = focus_roi
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        detections = self.backend.predict_frame(
            crop,
            self.cfg,
            conf=local_conf,
            imgsz=local_imgsz,
            source='local',
        )
        shifted = [self._offset_detection(det, (x1, y1), 'local') for det in detections]
        return self._select_best_local_detection(shifted)

    def _sync_lock_tracker(self, frame: np.ndarray) -> None:
        active = self.manager.get_active_target()
        if active is None:
            self.lock_tracker.reset()
            return
        if active.source in {'yolo', 'roi', 'local'}:
            self.lock_tracker.sync_from_bbox(frame, active.raw_bbox)

    def _compute_gt_iou(self, gt_bbox: Optional[tuple[int, int, int, int]]) -> float:
        if gt_bbox is None:
            return 0.0
        active = self.manager.get_active_target()
        if active is None:
            return 0.0
        return _iou(active.raw_bbox, gt_bbox)

    def process_frame(
        self,
        frame: np.ndarray,
        frame_index: int = 0,
        gt_bbox: Optional[tuple[int, int, int, int]] = None,
        small_target_mode: bool = False,
        render: bool = True,
        source_fps: Optional[float] = None,
    ) -> FrameOutput:
        self.frame_counter += 1
        self.manager.frame_tick()
        self._update_video_time(source_fps)
        timings_ms = {'global': 0.0, 'lock': 0.0, 'local': 0.0, 'roi': 0.0, 'night': 0.0, 'draw': 0.0}
        focus_roi = None
        lock_search_roi = None
        lock_score = 0.0

        run_global_scan, scan_strategy = self._should_run_global_scan()
        global_ids: set[int] = set()
        lock_ids: set[int] = set()
        local_ids: set[int] = set()
        roi_ids: set[int] = set()
        night_ids: set[int] = set()

        if run_global_scan:
            t0 = time.perf_counter()
            global_dets = self.backend.track_frame(frame, self.cfg)
            timings_ms['global'] = (time.perf_counter() - t0) * 1000.0
            global_ids = self.manager.update_from_yolo(global_dets)
        else:
            focus_roi = self._build_focus_roi(frame.shape)
            if self.cfg.LOCK_TRACKER_ENABLED:
                t0 = time.perf_counter()
                lock_det_data, lock_score, lock_search_roi = self.lock_tracker.predict(frame)
                timings_ms['lock'] = (time.perf_counter() - t0) * 1000.0
                if lock_det_data is not None:
                    active = self.manager.get_active_target()
                    cls_id = active.cls_id if active is not None else -1
                    lock_det = Detection(
                        bbox=lock_det_data['bbox'],
                        conf=float(lock_det_data['conf']),
                        cls_id=cls_id,
                        cx=float(lock_det_data['cx']),
                        cy=float(lock_det_data['cy']),
                        source='lock',
                        track_id=self.manager.active_id,
                    )
                    lock_ids = self.manager.update_from_focus_detection(lock_det, 'lock')
                    scan_strategy = 'LOCK-TRACK'

            need_local_validate = (
                focus_roi is not None
                and (
                    not lock_ids
                    or lock_score < max(self.cfg.LOCK_TRACKER_MIN_SCORE + 0.12, 0.55)
                    or self.frame_counter % self._effective_local_validate_interval() == 0
                )
            )
            if need_local_validate:
                t0 = time.perf_counter()
                local_imgsz, local_conf = self._local_validation_params(frame, lock_score)
                local_det = self._run_local_validation(
                    frame,
                    focus_roi,
                    local_imgsz=local_imgsz,
                    local_conf=local_conf,
                )
                timings_ms['local'] = (time.perf_counter() - t0) * 1000.0
                local_ids = self.manager.update_from_focus_detection(local_det, 'local')
                scan_strategy = 'LOCK-TRACK+LOCAL' if lock_ids else 'LOCAL-VALIDATE'

        run_roi_assist = (
            self.cfg.ROI_ASSIST_ENABLED
            and (not self.cfg.ROI_ASSIST_ON_SMALL_TARGET_ONLY or small_target_mode)
            and not self.manager.is_focus_mode()
            and self._should_run_roi_with_budget()
        )
        if run_roi_assist:
            t0 = time.perf_counter()
            roi_max_candidates = self._effective_roi_max_candidates()
            self._last_roi_budget_candidates = roi_max_candidates
            roi_regions = self.roi.propose(frame, max_candidates=roi_max_candidates)
            roi_dets = self.backend.predict_crops(
                frame,
                roi_regions,
                self.cfg,
                conf=self.cfg.ROI_CONF_THRESH,
                imgsz=self.cfg.ROI_IMG_SIZE,
                source='roi',
            )
            timings_ms['roi'] = (time.perf_counter() - t0) * 1000.0
            roi_ids = self.manager.update_from_roi_yolo(roi_dets, global_ids | lock_ids | local_ids)
        else:
            self._last_roi_budget_candidates = self._effective_roi_max_candidates()

        primary_seen_ids = global_ids | lock_ids | local_ids | roi_ids
        self.manager.note_primary_seen(bool(primary_seen_ids))

        night_budget_gate = self._should_run_night_with_budget()
        if self.manager.should_run_night_detector() and night_budget_gate:
            t0 = time.perf_counter()
            night_dets = self.night.detect(frame)
            timings_ms['night'] = (time.perf_counter() - t0) * 1000.0
            night_ids = self.manager.update_from_night(night_dets, primary_seen_ids)

        all_seen = primary_seen_ids | night_ids
        self.manager.age_targets(all_seen)
        self.manager.select_active()
        self.manager.update_focus_mode()
        lock_events = self._update_lock_events()
        self._sync_lock_tracker(frame)

        t_now = time.perf_counter()
        self.fps_buf.append(1.0 / max(t_now - self.t_prev, 1e-6))
        self.t_prev = t_now
        fps = sum(self.fps_buf) / len(self.fps_buf)

        gt_iou = self._compute_gt_iou(gt_bbox)
        active = self.manager.get_active_target()
        self._update_continuity_metrics(self.manager.active_id)
        active_bbox = active.raw_bbox if active is not None else None
        display_confidence = self._update_display_confidence(active, lock_score)
        reticle_center = self._update_reticle_center(active)
        continuity_score = self._continuity_score()
        active_presence_rate = self._active_presence_rate()
        active_id_changes = int(self._continuity_id_changes)
        median_reacquire_frames = self._median_reacquire_frames()
        tracking_mode = self._update_tracking_state(active)
        display_tracking_mode = self._get_display_tracking_state(tracking_mode)
        self._adapt_auto_scene(frame)
        smooth_active_bbox = self._get_smooth_display_bbox(active)

        rendered = None
        if render:
            t0 = time.perf_counter()
            rendered = draw_frame(
                frame.copy(),
                self.manager,
                fps,
                self.cfg,
                frame_index=frame_index,
                scan_strategy=scan_strategy,
                tracking_mode=display_tracking_mode,
                gt_bbox=gt_bbox,
                gt_iou=gt_iou,
                timings_ms=timings_ms,
                focus_roi=focus_roi,
                lock_search_roi=lock_search_roi,
                lock_score=lock_score,
                display_confidence=display_confidence,
                lock_switches_per_min=self._lock_switches_per_min(),
                lock_switch_count=self.lock_switch_count,
                budget_level=self._budget_level,
                budget_load=self._budget_load_ema,
                roi_budget_candidates=self._last_roi_budget_candidates,
                night_skip=self._last_night_skip,
                reticle_center=reticle_center,
                smooth_active_bbox=smooth_active_bbox,
            )
            timings_ms['draw'] = (time.perf_counter() - t0) * 1000.0

        self._update_budget_state(timings_ms)

        visible = len(self.manager.display_targets())
        active_source = active.source if active is not None else '-'
        return FrameOutput(
            frame=rendered,
            fps=fps,
            active_id=self.manager.active_id,
            active_source=active_source,
            active_bbox=active_bbox,
            target_count=len(self.manager.targets),
            visible_target_count=visible,
            mode=tracking_mode,
            frame_index=frame_index,
            scan_strategy=scan_strategy,
            gt_visible=gt_bbox is not None,
            gt_iou=gt_iou,
            lock_score=lock_score,
            display_confidence=display_confidence,
            continuity_score=continuity_score,
            active_presence_rate=active_presence_rate,
            active_id_changes=active_id_changes,
            median_reacquire_frames=median_reacquire_frames,
            lock_events=lock_events,
            lock_switch_count=self.lock_switch_count,
            lock_switches_per_min=self._lock_switches_per_min(),
            lock_event_counts=dict(self.lock_event_counts),
            budget_level=self._budget_level,
            budget_load=self._budget_load_ema,
            budget_frame_ms=self._last_frame_budget_ms,
            roi_budget_candidates=self._last_roi_budget_candidates,
            night_skip=self._last_night_skip,
            timings_ms=timings_ms,
        )


class VideoSession:
    def __init__(self, cfg: Config, source: Union[str, int], output_path: str = '', manage_cv_windows: bool = True):
        self.cfg = cfg
        self.source = parse_video_source(source)
        self.output_path = output_path
        self.manage_cv_windows = manage_cv_windows
        self.cap: Optional[object] = None
        self.writer: Optional[cv2.VideoWriter] = None
        self.frame_index = 0
        self.source_name = str(self.source)
        self.source_fps = 0.0
        self.gt: Optional[SequenceGroundTruth] = None

    def open(self) -> None:
        source_path = Path(str(self.source)) if isinstance(self.source, str) else None
        if source_path is not None and source_path.is_dir():
            self.cap = ImageSequenceCapture(source_path)
            self.gt = SequenceGroundTruth(source_path)
            self.source_name = source_path.name
            self.source_fps = 25.0
        else:
            self.cap = cv2.VideoCapture(self.source)
            if source_path is not None:
                self.source_name = source_path.name
            if self.cap is not None:
                src_fps = float(self.cap.get(cv2.CAP_PROP_FPS))
                self.source_fps = src_fps if src_fps > 1.0 else 0.0
        if self.cap is None or not self.cap.isOpened():
            raise RuntimeError(f'Не удалось открыть источник: {self.source}')
        if self.output_path:
            output = Path(self.output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
            src_fps = self.cap.get(cv2.CAP_PROP_FPS)
            out_fps = src_fps if src_fps and src_fps > 1 else 20.0
            self.writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*'mp4v'), out_fps, (width, height))
            if not self.writer.isOpened():
                raise RuntimeError(f'Не удалось открыть файл для записи: {output}')

    def read(self):
        if self.cap is None:
            raise RuntimeError('Сессия не открыта')
        ret, frame = self.cap.read()
        if not ret:
            return False, None, {}
        meta = {
            'frame_index': self.frame_index,
            'source_name': self.source_name,
            'source_fps': self.source_fps,
            'gt_bbox': self.gt.bbox_for(self.frame_index) if self.gt is not None else None,
        }
        self.frame_index += 1
        return True, frame, meta

    def write(self, frame: np.ndarray) -> None:
        if self.writer is not None:
            self.writer.write(frame)

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
        if self.writer is not None:
            self.writer.release()
        if self.manage_cv_windows:
            cv2.destroyAllWindows()


from uav_tracker.overlay import _draw_active_reticle, _draw_target, _target_class_label, draw_frame


def run_tracker(
    cfg: Config,
    source: Union[str, int],
    output_path: str = '',
    lock_log_path: str = '',
    no_display: bool = False,
    max_frames: int = 0,
    small_target_mode: bool = False,
) -> None:
    session = VideoSession(cfg, source, output_path=output_path)
    session.open()
    pipeline = TrackerPipeline(cfg)
    frame_idx = 0
    event_log_handle = None

    resolved_lock_log = lock_log_path.strip()
    if not resolved_lock_log and cfg.LOCK_EVENT_LOG_ENABLED and cfg.LOCK_EVENT_LOG_PATH:
        resolved_lock_log = str(cfg.LOCK_EVENT_LOG_PATH)
    if resolved_lock_log:
        lock_log_file = Path(resolved_lock_log)
        lock_log_file.parent.mkdir(parents=True, exist_ok=True)
        event_log_handle = lock_log_file.open('a', encoding='utf-8')

    try:
        while True:
            ret, frame, meta = session.read()
            if not ret:
                logger.warning('Кадр не получен. Конец потока или ошибка камеры.')
                break
            frame_idx += 1

            result = pipeline.process_frame(
                frame,
                frame_index=int(meta.get('frame_index', frame_idx - 1)),
                gt_bbox=meta.get('gt_bbox'),
                small_target_mode=small_target_mode,
                render=True,
                source_fps=meta.get('source_fps'),
            )
            if result.frame is not None:
                session.write(result.frame)

            if event_log_handle is not None and result.lock_events:
                for event in result.lock_events:
                    payload = {
                        'frame_index': int(result.frame_index),
                        'event': event,
                        'active_id': result.active_id,
                        'mode': result.mode,
                        'lock_score': round(float(result.lock_score), 4),
                        'lock_switches_per_min': round(float(result.lock_switches_per_min), 4),
                        'budget_level': int(result.budget_level),
                        'budget_load': round(float(result.budget_load), 4),
                    }
                    event_log_handle.write(json.dumps(payload, ensure_ascii=False) + '\n')

            if not no_display and result.frame is not None:
                cv2.imshow('Drone Tracker', result.frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                if key == ord('n'):
                    pipeline.manager.switch_target()
                if key == ord('r'):
                    pipeline.manager.active_id = None
                    pipeline.manager.targets.clear()
                    pipeline.lock_tracker.reset()

            if max_frames > 0 and frame_idx >= max_frames:
                logger.info('Достигнут лимит кадров: %d', frame_idx)
                break
    finally:
        session.close()
        if event_log_handle is not None:
            event_log_handle.close()
        if output_path:
            logger.info('Сохранён результат: %s', output_path)
        logger.info(
            'Lock telemetry: events=%s switches=%s sw/min=%.2f',
            pipeline.lock_event_counts,
            pipeline.lock_switch_count,
            pipeline._lock_switches_per_min(),
        )
        logger.info(
            'Budget telemetry: level=%s load=%.2f frame_ms=%.1f roi=%s nskip=%s',
            pipeline._budget_level,
            pipeline._budget_load_ema,
            pipeline._last_frame_budget_ms,
            pipeline._last_roi_budget_candidates,
            pipeline._last_night_skip,
        )
        logger.info('Трекер остановлен.')
