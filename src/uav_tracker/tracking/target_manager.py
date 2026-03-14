from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from uav_tracker.config import Config
from uav_tracker.runtime.base import Detection
from utils.geometry import iou


@dataclass
class TrackedTarget:
    track_id: int
    bbox: tuple
    raw_bbox: tuple
    cx: float = 0.0
    cy: float = 0.0
    speed: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    conf: float = 0.0
    cls_id: int = -1
    drone_score: float = 0.5
    lost_frames: int = 0
    hit_streak: int = 0
    source: str = 'yolo'
    trail: deque = field(default_factory=lambda: deque(maxlen=30))


class TargetManager:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.targets: dict[int, TrackedTarget] = {}
        self.active_id: Optional[int] = None
        self._next_aux_id = 9000
        self._frames_since_primary = 9999
        self._focus_mode = False
        self._focus_enter_streak = 0
        self._focus_exit_streak = 0
        self._active_switch_cooldown = 0

    def _smooth_bbox(self, old_bbox, new_bbox, alpha):
        if old_bbox is None:
            return new_bbox
        return tuple(int(alpha * n + (1 - alpha) * o) for o, n in zip(old_bbox, new_bbox))

    def _dist(self, ax, ay, bx, by) -> float:
        return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

    def _is_primary_source(self, source: str) -> bool:
        return source in {'yolo', 'roi', 'local', 'lock'}

    def get_active_target(self) -> Optional[TrackedTarget]:
        if self.active_id is None:
            return None
        return self.targets.get(self.active_id)

    def note_primary_seen(self, seen: bool) -> None:
        if seen:
            self._frames_since_primary = 0
        else:
            self._frames_since_primary += 1

    def frame_tick(self) -> None:
        if self._active_switch_cooldown > 0:
            self._active_switch_cooldown -= 1

    def _can_switch_active(self, new_tid: int, *, force: bool = False) -> bool:
        if force:
            return True
        if self.active_id is None or self.active_id == new_tid:
            return True
        active = self.get_active_target()
        if active is None:
            return True

        allow_if_lost = max(0, int(self.cfg.ACTIVE_ID_SWITCH_ALLOW_IF_LOST_FRAMES))
        if (
            bool(self.cfg.ACTIVE_STRICT_LOCK_SWITCH)
            and self.is_focus_mode()
            and active.track_id != new_tid
            and active.lost_frames <= allow_if_lost
        ):
            return False

        if self._active_switch_cooldown <= 0:
            return True
        if active.lost_frames > allow_if_lost:
            return True
        if not self._is_drone_like_target(active, self.cfg.DRONE_REACQUIRE_SCORE_MIN):
            return True
        return False

    def _set_active_id(self, new_tid: Optional[int], *, force: bool = False) -> bool:
        if new_tid is None:
            self.active_id = None
            self._active_switch_cooldown = 0
            return True
        tid = int(new_tid)
        if self.active_id == tid:
            return True
        if not self._can_switch_active(tid, force=force):
            return False
        self.active_id = tid
        self._active_switch_cooldown = max(0, int(self.cfg.ACTIVE_ID_SWITCH_COOLDOWN_FRAMES))
        return True

    def _is_drone_like_target(self, target: TrackedTarget, min_score: float) -> bool:
        if not self._is_primary_source(target.source):
            return False
        if target.drone_score >= min_score:
            return True
        return target.cls_id == self.cfg.PREFER_CLASS_ID

    def _is_drone_like_detection(self, cls_id: int, conf: float) -> bool:
        _ = conf
        return cls_id == self.cfg.PREFER_CLASS_ID

    def has_confirmed_drone_lock(self) -> bool:
        active = self.get_active_target()
        if active is None:
            return False
        if not self._is_primary_source(active.source):
            return False
        if active.hit_streak < self.cfg.LOCK_CONFIRM_FRAMES:
            return False
        if active.lost_frames > self.cfg.LOCK_LOST_GRACE:
            return False
        return self._is_drone_like_target(active, self.cfg.DRONE_LOCK_SCORE_MIN)

    def is_focus_mode(self) -> bool:
        return bool(self.cfg.LOCK_FOCUS_ONLY and self._focus_mode)

    def update_focus_mode(self) -> bool:
        if not self.cfg.LOCK_FOCUS_ONLY:
            self._focus_mode = False
            self._focus_enter_streak = 0
            self._focus_exit_streak = 0
            return False

        confirmed = self.has_confirmed_drone_lock()
        enter_frames = max(1, int(self.cfg.LOCK_MODE_ACQUIRE_FRAMES))
        release_frames = max(1, int(self.cfg.LOCK_MODE_RELEASE_FRAMES))

        if confirmed:
            self._focus_enter_streak += 1
            self._focus_exit_streak = 0
            if not self._focus_mode and self._focus_enter_streak >= enter_frames:
                self._focus_mode = True
            return self._focus_mode

        self._focus_enter_streak = 0
        if self._focus_mode:
            self._focus_exit_streak += 1
            if self._focus_exit_streak >= release_frames:
                self._focus_mode = False
        else:
            self._focus_exit_streak = 0
        return self._focus_mode

    def should_run_night_detector(self) -> bool:
        if not self.cfg.NIGHT_ENABLED:
            return False
        if self.cfg.DISABLE_NIGHT_ON_LOCK and self.is_focus_mode():
            return False
        if not self.cfg.NIGHT_RUN_WHEN_PRIMARY_SEEN:
            cooldown = max(0, int(self.cfg.NIGHT_PRIMARY_COOLDOWN))
            if self._frames_since_primary < cooldown:
                return False
        return True

    def display_targets(self) -> list[TrackedTarget]:
        if self.cfg.SHOW_ONLY_ACTIVE_ON_LOCK and self.is_focus_mode():
            active = self.get_active_target()
            return [active] if active is not None else []
        visible = []
        for target in self.targets.values():
            if target.lost_frames > self.cfg.DISPLAY_MAX_LOST_FRAMES:
                continue
            min_hits = (
                self.cfg.DISPLAY_MIN_HIT_STREAK_PRIMARY
                if self._is_primary_source(target.source)
                else self.cfg.DISPLAY_MIN_HIT_STREAK_NIGHT
            )
            if target.track_id != self.active_id and target.hit_streak < min_hits:
                continue
            visible.append(target)
        return visible

    def _append_trail(self, target: TrackedTarget, point: tuple[int, int]):
        target.trail.append(point)

    def _predict_center(self, target: TrackedTarget) -> tuple[float, float]:
        horizon = max(1, min(int(self.cfg.LOCK_REACQUIRE_PREDICT_HORIZON_MAX), target.lost_frames + 1))
        gain = float(self.cfg.LOCK_REACQUIRE_PREDICT_GAIN)
        return (
            float(target.cx + target.vx * horizon * gain),
            float(target.cy + target.vy * horizon * gain),
        )

    def _merge_active_lock(self, new_tid: int):
        active = self.get_active_target()
        candidate = self.targets.get(new_tid)
        if active is None or candidate is None or active.track_id == new_tid:
            return
        if not self._can_switch_active(new_tid):
            return
        merged_trail = list(active.trail) + list(candidate.trail)
        candidate.trail = deque(merged_trail[-self.cfg.TRAIL_LEN :], maxlen=self.cfg.TRAIL_LEN)
        candidate.hit_streak = max(candidate.hit_streak, active.hit_streak)
        candidate.vx = 0.5 * candidate.vx + 0.5 * active.vx
        candidate.vy = 0.5 * candidate.vy + 0.5 * active.vy
        self._set_active_id(new_tid)

    def _try_reacquire_active_from_primary(self, seen_ids: set[int]):
        active = self.get_active_target()
        if active is None:
            return
        if not self._is_primary_source(active.source):
            return
        if not self._is_drone_like_target(active, self.cfg.DRONE_REACQUIRE_SCORE_MIN):
            return
        if active.track_id in seen_ids:
            return

        max_reacquire_dist = self.cfg.LOCK_REACQUIRE_DIST + min(90, int(active.speed * 1.8) + active.lost_frames * 12)
        px, py = self._predict_center(active)
        pred_gate_dist = max_reacquire_dist + min(70, int(active.speed * 2.0))
        best_tid = None
        best_score = None
        for tid in seen_ids:
            candidate = self.targets.get(tid)
            if candidate is None or not self._is_primary_source(candidate.source):
                continue
            if not self._is_drone_like_target(candidate, self.cfg.DRONE_REACQUIRE_SCORE_MIN):
                continue
            dist = self._dist(active.cx, active.cy, candidate.cx, candidate.cy)
            if dist > max_reacquire_dist:
                continue
            pred_dist = self._dist(px, py, candidate.cx, candidate.cy)
            if pred_dist > pred_gate_dist:
                continue
            score = (pred_dist, dist, -candidate.drone_score, -candidate.conf)
            if best_score is None or score < best_score:
                best_score = score
                best_tid = tid
        if best_tid is not None:
            self._merge_active_lock(best_tid)

    def _update_drone_score(self, target: TrackedTarget, cls_id: int, conf: float, source: str) -> None:
        if not self._is_primary_source(source) or cls_id < 0:
            return
        alpha = float(self.cfg.CLASS_EMA_ALPHA)
        alpha = max(0.05, min(0.50, alpha * (0.6 + 0.8 * float(conf))))
        cls_value = 1.0 if cls_id == self.cfg.PREFER_CLASS_ID else 0.0
        target.drone_score = (1.0 - alpha) * target.drone_score + alpha * cls_value

    def _update_or_create_target(self, tid: int, raw: tuple, cx: float, cy: float, conf: float, cls_id: int, source: str):
        if tid in self.targets:
            target = self.targets[tid]
            dx, dy = cx - target.cx, cy - target.cy
            speed = (dx ** 2 + dy ** 2) ** 0.5
            speed_alpha = max(0.1, min(0.95, float(self.cfg.SPEED_WEIGHT)))
            target.speed = speed_alpha * speed + (1.0 - speed_alpha) * target.speed
            vel_alpha = max(0.1, min(0.95, float(self.cfg.VELOCITY_ALPHA)))
            target.vx = vel_alpha * dx + (1.0 - vel_alpha) * target.vx
            target.vy = vel_alpha * dy + (1.0 - vel_alpha) * target.vy
            target.bbox = self._smooth_bbox(target.bbox, raw, self.cfg.SMOOTH_ALPHA)
            target.raw_bbox = raw
            target.cx, target.cy = cx, cy
            target.conf = conf
            target.cls_id = cls_id if cls_id >= 0 else target.cls_id
            target.lost_frames = 0
            target.hit_streak += 1
            target.source = source
            self._update_drone_score(target, cls_id, conf, source)
        else:
            if self._is_primary_source(source) and cls_id >= 0:
                initial_drone_score = 0.70 if cls_id == self.cfg.PREFER_CLASS_ID else 0.30
            else:
                initial_drone_score = 0.5
            self.targets[tid] = TrackedTarget(
                track_id=tid,
                bbox=raw,
                raw_bbox=raw,
                cx=cx,
                cy=cy,
                vx=0.0,
                vy=0.0,
                conf=conf,
                cls_id=cls_id,
                drone_score=initial_drone_score,
                hit_streak=1,
                source=source,
            )
        self._append_trail(self.targets[tid], (int(cx), int(cy)))

    def update_from_yolo(self, detections: list[Detection]) -> set[int]:
        seen_ids = set()
        focus_target = self.get_active_target() if self.is_focus_mode() else None
        for det in detections:
            if det.track_id is None:
                continue
            tid = int(det.track_id)
            raw = det.bbox
            cx, cy = det.cx, det.cy

            if focus_target is not None:
                is_active_box = tid == focus_target.track_id
                fpx, fpy = self._predict_center(focus_target)
                focus_max_dist = self.cfg.LOCK_REACQUIRE_DIST + min(70, int(focus_target.speed * 1.6))
                is_reacquire_candidate = (
                    self._is_drone_like_detection(det.cls_id, det.conf)
                    and self._dist(cx, cy, fpx, fpy) <= focus_max_dist
                )
                if not is_active_box and not is_reacquire_candidate:
                    continue

            self._update_or_create_target(tid, raw, cx, cy, det.conf, det.cls_id, det.source)
            seen_ids.add(tid)

        self._try_reacquire_active_from_primary(seen_ids)
        return seen_ids

    def update_from_focus_detection(self, det: Optional[Detection], source_name: str) -> set[int]:
        active = self.get_active_target()
        if active is None or det is None or self.active_id is None:
            return set()
        self._update_or_create_target(
            self.active_id,
            det.bbox,
            det.cx,
            det.cy,
            det.conf,
            det.cls_id if det.cls_id >= 0 else active.cls_id,
            source_name,
        )
        return {self.active_id}

    def update_from_roi_yolo(self, roi_dets: list[Detection], primary_ids: set[int]) -> set[int]:
        if not roi_dets:
            return set()

        primary_bboxes = [self.targets[tid].raw_bbox for tid in primary_ids if tid in self.targets]
        seen_roi_ids = set()
        focus_target = self.get_active_target() if self.is_focus_mode() else None

        for det in roi_dets:
            if self._overlaps_any(det.bbox, primary_bboxes, iou_thresh=0.35):
                continue

            if focus_target is not None:
                fpx, fpy = self._predict_center(focus_target)
                focus_max_dist = self.cfg.LOCK_REACQUIRE_DIST + min(70, int(focus_target.speed * 1.6))
                is_reacquire_candidate = (
                    self._is_drone_like_detection(det.cls_id, det.conf)
                    and self._dist(det.cx, det.cy, fpx, fpy) <= focus_max_dist
                )
                if not is_reacquire_candidate:
                    continue

            tid = self._find_nearby_track(det.cx, det.cy, max_dist=self.cfg.NIGHT_TRACK_DIST * 2, sources={'roi'})
            if tid is None:
                tid = self._next_aux_id
                self._next_aux_id += 1
            self._update_or_create_target(tid, det.bbox, det.cx, det.cy, det.conf, det.cls_id, 'roi')
            seen_roi_ids.add(tid)

        self._try_reacquire_active_from_primary(seen_roi_ids)
        return seen_roi_ids

    def update_from_night(self, night_dets: list[dict], primary_ids: set[int]) -> set[int]:
        if self.is_focus_mode():
            return set()

        primary_bboxes = [self.targets[tid].raw_bbox for tid in primary_ids if tid in self.targets]
        seen_night_ids = set()
        for det in night_dets:
            if self._overlaps_any(det['bbox'], primary_bboxes, iou_thresh=0.3):
                continue
            tid = self._find_nearby_track(det['cx'], det['cy'], max_dist=self.cfg.NIGHT_TRACK_DIST, sources={'night'})
            if tid is None:
                tid = self._next_aux_id
                self._next_aux_id += 1
            self._update_or_create_target(tid, det['bbox'], det['cx'], det['cy'], det.get('conf', 0.0), det.get('cls_id', -1), 'night')
            seen_night_ids.add(tid)
        return seen_night_ids

    def _overlaps_any(self, bbox, others, iou_thresh=0.3):
        for other in others:
            if iou(bbox, other) > iou_thresh:
                return True
        return False

    def _find_nearby_track(self, cx, cy, max_dist=40, sources: Optional[set[str]] = None):
        best_id, best_dist = None, max_dist
        for tid, target in self.targets.items():
            if sources is not None and target.source not in sources:
                continue
            dist = ((cx - target.cx) ** 2 + (cy - target.cy) ** 2) ** 0.5
            if dist < best_dist:
                best_dist, best_id = dist, tid
        return best_id

    def age_targets(self, seen_ids: set[int]):
        dead = []
        for tid, target in self.targets.items():
            if tid not in seen_ids:
                target.lost_frames += 1
                target.hit_streak = max(0, target.hit_streak - 1)
                ttl = self.cfg.YOLO_LOST_MAX if self._is_primary_source(target.source) else self.cfg.NIGHT_LOST_MAX
                if target.lost_frames > ttl:
                    dead.append(tid)
        for tid in dead:
            del self.targets[tid]
            if self.active_id == tid:
                self._set_active_id(None)

    def select_active(self):
        if self.active_id and self.active_id in self.targets:
            return
        if not self.targets:
            return
        if self.cfg.ACTIVE_STRICT_LOCK_SWITCH and self.is_focus_mode():
            return

        def score(target: TrackedTarget) -> float:
            score_value = float(target.speed)
            score_value += target.conf * 1.2
            score_value += min(4.0, target.hit_streak * 0.35)
            score_value -= target.lost_frames * 0.8
            if self._is_primary_source(target.source):
                score_value += 2.8 * target.drone_score
            else:
                score_value -= 0.8
            return score_value

        best = max(self.targets.values(), key=score)
        if best.speed > 1.0 or self._is_drone_like_target(best, self.cfg.DRONE_REACQUIRE_SCORE_MIN):
            self._set_active_id(best.track_id)

    def switch_target(self):
        ids = list(self.targets.keys())
        if not ids:
            return
        if self.active_id not in ids:
            self._set_active_id(ids[0], force=True)
            return
        idx = ids.index(self.active_id)
        self._set_active_id(ids[(idx + 1) % len(ids)], force=True)
