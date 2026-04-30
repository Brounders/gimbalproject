import json
import logging
import time
from collections import deque
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

from uav_tracker.pipeline_control.budget_controller import BudgetController
from uav_tracker.config import Config
from uav_tracker.exceptions import ModelNotFoundError, SourceOpenError
from uav_tracker.tracking.continuity_tracker import ContinuityTracker
from uav_tracker.display.display_state_tracker import DisplayStateTracker
from uav_tracker.tracking.lock_event_tracker import LockEventTracker
from uav_tracker.tracking.tracking_state_machine import TrackingStateMachine
from uav_tracker.detectors.night_detector import NightSmallTargetDetector
from uav_tracker.detectors.roi_assist import MotionROIProposer
from uav_tracker.runtime import create_detector_backend
from uav_tracker.detection_source import DetectionSource
from uav_tracker.runtime.base import Detection
from uav_tracker.runtime_config import RuntimeConfigView
from uav_tracker.tracking.lock_tracker import TemplateLockTracker
from uav_tracker.tracking.target_manager import TargetManager
from uav_tracker.tracking.tracked_target import TrackedTarget
from utils.geometry import iou


logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}


from uav_tracker.display.frame_result import FrameOutput
from uav_tracker.display.overlay import _draw_active_reticle, _draw_target, _target_class_label, draw_frame


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


class TrackerPipeline:
    """Main tracking pipeline for UAV detection and lock.

    Orchestrates the full per-frame tracking cycle:
      1. Global YOLO scan (every N frames) or local lock/ROI scan.
      2. Night small-target detector (when enabled and budget allows).
      3. Motion-ROI proposer for sub-frame candidate refinement.
      4. TargetManager: multi-target state, active target selection, lock policy.
      5. TemplateLockTracker: template-matching-based lock continuity.
      6. Budget controller: adapts scan frequency under CPU load.
      7. Auto scene detection: switches night/IR presets on-the-fly.

    Typical usage::

        pipeline = TrackerPipeline(cfg)
        while True:
            ret, frame = cap.read()
            result = pipeline.process_frame(frame)
            if result.active_id is not None:
                x1, y1, x2, y2 = result.active_bbox
    """

    def __init__(self, cfg: Config):
        cfg.validate()
        self.cfg = cfg
        # BUG-008: raise ModelNotFoundError so TrackerWorker can show specific message
        from pathlib import Path as _Path
        if not _Path(cfg.MODEL_PATH).exists():
            raise ModelNotFoundError(cfg.MODEL_PATH)
        self.backend = create_detector_backend(cfg.MODEL_PATH, cfg.DEVICE)
        self.night = NightSmallTargetDetector(cfg)
        self.roi = MotionROIProposer(cfg)
        self.manager = TargetManager(cfg)
        self.lock_tracker = TemplateLockTracker(cfg)
        self.fps_buf = deque(maxlen=30)
        self.t_prev = time.perf_counter()
        self.frame_counter = 0
        self.lock_telemetry = LockEventTracker()
        self._video_elapsed_sec = 0.0
        self._fallback_fps = cfg.FALLBACK_FPS
        self.budget = BudgetController(cfg, initial_roi_candidates=max(1, int(cfg.ROI_MAX_CANDIDATES)))
        self.continuity = ContinuityTracker()
        self.tracking_sm = TrackingStateMachine(cfg)
        self.display_state = DisplayStateTracker(cfg)

        # RuntimeConfigView: base cfg + per-scene overrides (BUG-001 fix).
        # _adapt_auto_scene writes to _scene_overrides only; base cfg is never mutated.
        self._runtime_cfg = RuntimeConfigView(cfg)

        # Auto scene detection state (TASK-020).
        self._auto_scene_state = 'day'       # 'day' or 'night'
        self._auto_scene_streak = 0          # consecutive frames in candidate state
        self._auto_scene_frame_tick = 0

    def _update_video_time(self, source_fps: Optional[float]) -> None:
        min_valid = self.cfg.SOURCE_FPS_MIN_VALID
        if source_fps is not None and source_fps > min_valid:
            self._video_elapsed_sec += 1.0 / float(source_fps)
            return
        fallback = self.fps_buf[-1] if self.fps_buf else self._fallback_fps
        fallback = max(min_valid, float(fallback))
        self._video_elapsed_sec += 1.0 / fallback

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

        # Scene confirmed — update RuntimeConfigView overrides; base cfg is never mutated.
        self._auto_scene_state = candidate
        self._auto_scene_streak = 0
        if candidate == 'night':
            self._runtime_cfg = self._runtime_cfg.with_overrides(
                CONF_THRESH=float(getattr(self.cfg, 'AUTO_SCENE_NIGHT_CONF', 0.12)),
                NIGHT_MOT_THRESH=int(getattr(self.cfg, 'AUTO_SCENE_NIGHT_MOT_THRESH', 12)),
                NIGHT_DIFF_THRESH=int(getattr(self.cfg, 'AUTO_SCENE_NIGHT_DIFF_THRESH', 8)),
                LOCK_CONFIRM_FRAMES=int(getattr(self.cfg, 'AUTO_SCENE_NIGHT_LOCK_CONFIRM', 8)),
                DRONE_LOCK_SCORE_MIN=float(getattr(self.cfg, 'AUTO_SCENE_NIGHT_DRONE_LOCK_SCORE', 0.75)),
            )
        elif candidate == 'ir':
            self._runtime_cfg = self._runtime_cfg.with_overrides(
                CONF_THRESH=float(getattr(self.cfg, 'AUTO_SCENE_IR_CONF', 0.10)),
                NIGHT_MOT_THRESH=int(getattr(self.cfg, 'AUTO_SCENE_IR_MOT_THRESH', 8)),
                NIGHT_DIFF_THRESH=int(getattr(self.cfg, 'AUTO_SCENE_IR_DIFF_THRESH', 6)),
                LOCK_CONFIRM_FRAMES=int(getattr(self.cfg, 'AUTO_SCENE_NIGHT_LOCK_CONFIRM', 8)),
                DRONE_LOCK_SCORE_MIN=float(getattr(self.cfg, 'AUTO_SCENE_NIGHT_DRONE_LOCK_SCORE', 0.75)),
            )
        else:  # day — clear overrides (restore base cfg values)
            self._runtime_cfg = RuntimeConfigView(self.cfg)

    def _should_run_global_scan(self) -> tuple[bool, str]:
        active = self.manager.get_active_target()
        if not self.cfg.ADAPTIVE_SCAN_ENABLED:
            return True, 'GLOBAL-SCAN'
        if not self.manager.is_focus_mode() or active is None:
            return True, 'GLOBAL-SCAN'
        if active.lost_frames > self.cfg.LOCK_LOST_GRACE:
            return True, 'GLOBAL-RECOVERY'
        interval = self.budget.effective_global_scan_interval(self.frame_counter)
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
        if self.cfg.BUDGET_ENABLED and self.budget.level >= 2 and not is_small_target:
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
            source=DetectionSource.LOCAL,
        )
        shifted = [self._offset_detection(det, (x1, y1), DetectionSource.LOCAL) for det in detections]
        return self._select_best_local_detection(shifted)

    def _sync_lock_tracker(self, frame: np.ndarray) -> None:
        active = self.manager.get_active_target()
        if active is None:
            self.lock_tracker.reset()
            return
        if active.source in {DetectionSource.YOLO, DetectionSource.ROI, DetectionSource.LOCAL}:
            self.lock_tracker.sync_from_bbox(frame, active.raw_bbox)

    def _compute_gt_iou(self, gt_bbox: Optional[tuple[int, int, int, int]]) -> float:
        if gt_bbox is None:
            return 0.0
        active = self.manager.get_active_target()
        if active is None:
            return 0.0
        return iou(active.raw_bbox, gt_bbox)

    def process_frame(
        self,
        frame: np.ndarray,
        frame_index: int = 0,
        gt_bbox: Optional[tuple[int, int, int, int]] = None,
        small_target_mode: bool = False,
        render: bool = True,
        source_fps: Optional[float] = None,
    ) -> FrameOutput:
        """Process one video frame through the full tracking pipeline.

        Args:
            frame: BGR image as numpy array (H, W, 3).
            frame_index: Sequential frame number used for scan scheduling.
            gt_bbox: Ground-truth bounding box (x1, y1, x2, y2) for evaluation;
                None when no GT is available.
            small_target_mode: If True, uses higher resolution inference for small targets.
            render: If True, draws HUD overlays onto `frame` in-place.
            source_fps: Native FPS of the source video used for timing metrics;
                falls back to measured FPS when None.

        Returns:
            FrameOutput dataclass with tracking state, metrics, and the
            (optionally annotated) frame.
        """
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
            global_dets = self.backend.track_frame(frame, self._runtime_cfg)
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
                        source=DetectionSource.LOCK,
                        track_id=self.manager.active_id,
                    )
                    lock_ids = self.manager.update_from_focus_detection(lock_det, DetectionSource.LOCK)
                    scan_strategy = 'LOCK-TRACK'

            need_local_validate = (
                focus_roi is not None
                and (
                    not lock_ids
                    or lock_score < max(self.cfg.LOCK_TRACKER_MIN_SCORE + 0.12, 0.55)
                    or self.frame_counter % self.budget.effective_local_validate_interval(self.frame_counter) == 0
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
            and self.budget.should_run_roi(self.frame_counter)
        )
        if run_roi_assist:
            t0 = time.perf_counter()
            roi_max_candidates = self.budget.effective_roi_max_candidates()
            roi_regions = self.roi.propose(frame, max_candidates=roi_max_candidates)
            roi_dets = self.backend.predict_crops(
                frame,
                roi_regions,
                self.cfg,
                conf=self.cfg.ROI_CONF_THRESH,
                imgsz=self.cfg.ROI_IMG_SIZE,
                source=DetectionSource.ROI,
            )
            timings_ms['roi'] = (time.perf_counter() - t0) * 1000.0
            roi_ids = self.manager.update_from_roi_yolo(roi_dets, global_ids | lock_ids | local_ids)
        else:
            self.budget.effective_roi_max_candidates()

        primary_seen_ids = global_ids | lock_ids | local_ids | roi_ids
        self.manager.note_primary_seen(bool(primary_seen_ids))

        night_budget_gate = self.budget.should_run_night(self.frame_counter)
        if self.manager.should_run_night_detector() and night_budget_gate:
            t0 = time.perf_counter()
            night_dets = self.night.detect(frame)
            timings_ms['night'] = (time.perf_counter() - t0) * 1000.0
            night_ids = self.manager.update_from_night(night_dets, primary_seen_ids)

        all_seen = primary_seen_ids | night_ids
        self.manager.age_targets(all_seen)
        self.manager.select_active()
        self.manager.update_focus_mode()
        lock_events = self.lock_telemetry.update(self.manager.is_focus_mode(), self.manager.active_id)
        self._sync_lock_tracker(frame)

        t_now = time.perf_counter()
        self.fps_buf.append(1.0 / max(t_now - self.t_prev, 1e-6))
        self.t_prev = t_now
        fps = sum(self.fps_buf) / len(self.fps_buf)

        gt_iou = self._compute_gt_iou(gt_bbox)
        active = self.manager.get_active_target()
        self.continuity.update(self.manager.active_id)
        active_bbox = active.raw_bbox if active is not None else None
        display_confidence = self.display_state.update_confidence(
            active, lock_score, self._video_elapsed_sec, self.frame_counter)
        reticle_center = self.display_state.update_reticle(active)
        continuity_score = self.continuity.score()
        active_presence_rate = self.continuity.presence_rate(self.frame_counter)
        active_id_changes = int(self.continuity.id_changes)
        median_reacquire_frames = self.continuity.median_reacquire_frames()
        lost_frames_val = active.lost_frames if active is not None else None
        tracking_mode = self.tracking_sm.update(lost_frames_val)
        display_tracking_mode = self.tracking_sm.update_display()
        self._adapt_auto_scene(frame)
        smooth_active_bbox = self.display_state.update_smooth_bbox(active)

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
                lock_switches_per_min=self.lock_telemetry.switches_per_min(self._video_elapsed_sec),
                lock_switch_count=self.lock_telemetry.switch_count,
                budget_level=self.budget.level,
                budget_load=self.budget.load_ema,
                roi_budget_candidates=self.budget.last_roi_candidates,
                night_skip=self.budget.last_night_skip,
                reticle_center=reticle_center,
                smooth_active_bbox=smooth_active_bbox,
            )
            timings_ms['draw'] = (time.perf_counter() - t0) * 1000.0

        self.budget.update(timings_ms)

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
            lock_switch_count=self.lock_telemetry.switch_count,
            lock_switches_per_min=self.lock_telemetry.switches_per_min(self._video_elapsed_sec),
            lock_event_counts=dict(self.lock_telemetry.event_counts),
            budget_level=self.budget.level,
            budget_load=self.budget.load_ema,
            budget_frame_ms=self.budget.last_frame_ms,
            roi_budget_candidates=self.budget.last_roi_candidates,
            night_skip=self.budget.last_night_skip,
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
            self.source_fps = self.cfg.FALLBACK_FPS
        else:
            self.cap = cv2.VideoCapture(self.source)
            if source_path is not None:
                self.source_name = source_path.name
            if self.cap is not None:
                src_fps = float(self.cap.get(cv2.CAP_PROP_FPS))
                self.source_fps = src_fps if src_fps > self.cfg.SOURCE_FPS_MIN_VALID else 0.0
        if self.cap is None or not self.cap.isOpened():
            raise SourceOpenError(self.source)
        if self.output_path:
            output = Path(self.output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
            src_fps = self.cap.get(cv2.CAP_PROP_FPS)
            out_fps = src_fps if src_fps and src_fps > self.cfg.SOURCE_FPS_MIN_VALID else self.cfg.OUTPUT_FPS_FALLBACK
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
            pipeline.lock_telemetry.event_counts,
            pipeline.lock_telemetry.switch_count,
            pipeline.lock_telemetry.switches_per_min(pipeline._video_elapsed_sec),
        )
        logger.info(
            'Budget telemetry: level=%s load=%.2f frame_ms=%.1f roi=%s nskip=%s',
            pipeline.budget.level,
            pipeline.budget.load_ema,
            pipeline.budget.last_frame_ms,
            pipeline.budget.last_roi_candidates,
            pipeline.budget.last_night_skip,
        )
        logger.info('Трекер остановлен.')
