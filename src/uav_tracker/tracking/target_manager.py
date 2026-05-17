from collections import deque
from typing import Optional

from uav_tracker.config import Config
from uav_tracker.detection_source import DetectionSource
from uav_tracker.runtime.base import Detection
from uav_tracker.tracking.focus_mode_controller import FocusModeController
from uav_tracker.tracking.operator_override import OperatorOverrideResult, OperatorTargetOverride
from uav_tracker.tracking.proposal_trust import build_proposals, source_trust
from uav_tracker.tracking.tracked_target import TrackedTarget
from uav_tracker.tracking.evidence import normalize_source
from utils.geometry import iou


class TargetManager:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.targets: dict[int, TrackedTarget] = {}
        self.active_id: Optional[int] = None
        self._next_aux_id = 9000
        self._frames_since_primary = 9999
        self._focus_ctrl = FocusModeController(cfg)
        self._active_switch_cooldown = 0
        self._night_key_to_tid: dict[tuple, int] = {}
        self._low_trust_streak: int = 0       # TASK-103e: frames active source trust < threshold
        self._health_released_tid: int | None = None  # TASK-103f: tid suppressed after health release
        self._health_suppress_frames: int = 0         # TASK-103f: frames remaining in suppression window

    def _smooth_bbox(self, old_bbox, new_bbox, alpha):
        if old_bbox is None:
            return new_bbox
        return tuple(int(alpha * n + (1 - alpha) * o) for o, n in zip(old_bbox, new_bbox))

    def _dist(self, ax, ay, bx, by) -> float:
        return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

    def _is_primary_source(self, source: str) -> bool:
        if source == DetectionSource.NIGHT and bool(getattr(self.cfg, "NIGHT_PRIMARY_SOURCE_ENABLED", False)):
            return True
        return source in DetectionSource.primary_sources()

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
            self._low_trust_streak = 0  # TASK-103e
            return True
        tid = int(new_tid)
        if self.active_id == tid:
            return True
        if not self._can_switch_active(tid, force=force):
            return False
        self.active_id = tid
        self._active_switch_cooldown = max(0, int(self.cfg.ACTIVE_ID_SWITCH_COOLDOWN_FRAMES))
        self._low_trust_streak = 0        # TASK-103e: reset on every active switch
        self._health_released_tid = None  # TASK-103f: clear suppression on successful switch
        self._health_suppress_frames = 0  # TASK-103f
        return True

    def release_active(self) -> bool:
        """Public API to release the currently active target.

        Idempotent: clears `active_id` and resets the active-switch cooldown
        without touching `self.targets` (lock_tracker reset is the caller's
        responsibility).  Returns True if there was an active id to clear,
        False if already empty.

        Used by guarded ActionPolicy behavior wiring (ALG-001 v1.1) so it
        does not have to call the private `_set_active_id` shim.
        """
        self._health_released_tid = None   # TASK-103f: operator release clears suppression
        self._health_suppress_frames = 0   # TASK-103f
        if self.active_id is None:
            return False
        self._set_active_id(None)
        return True

    def _find_operator_override_target(self, bbox: tuple[int, int, int, int]) -> Optional[int]:
        x1, y1, x2, y2 = bbox
        ocx = (x1 + x2) / 2.0
        ocy = (y1 + y2) / 2.0
        best_id = None
        best_score = None
        for tid, target in self.targets.items():
            inside = x1 <= target.cx <= x2 and y1 <= target.cy <= y2
            overlap = iou(bbox, target.raw_bbox)
            if not inside and overlap <= 0.0:
                continue
            dist = self._dist(ocx, ocy, target.cx, target.cy)
            score = (0 if inside else 1, -overlap, dist)
            if best_score is None or score < best_score:
                best_score = score
                best_id = tid
        return best_id

    def apply_operator_override(
        self,
        override: OperatorTargetOverride,
        *,
        frame_shape: tuple[int, ...],
    ) -> OperatorOverrideResult:
        """Force active target to the operator-selected frame region.

        The method prefers an existing target whose center/box overlaps the
        operator region; otherwise it creates a dedicated auxiliary target.
        It marks the target as operator-confirmed and force-selects it.  The
        caller remains responsible for resetting/syncing TemplateLockTracker.
        """
        bbox = override.to_bbox(frame_shape)
        if bbox is None:
            return OperatorOverrideResult(False, 'invalid')

        tid = self._find_operator_override_target(bbox)
        if tid is None:
            tid = self._next_aux_id
            self._next_aux_id += 1

        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        self._update_or_create_target(
            int(tid),
            bbox,
            cx,
            cy,
            1.0,
            int(self.cfg.PREFER_CLASS_ID),
            DetectionSource.OPERATOR,
        )
        target = self.targets[int(tid)]
        target.bbox = bbox
        target.raw_bbox = bbox
        target.cx = cx
        target.cy = cy
        target.vx = 0.0
        target.vy = 0.0
        target.speed = 0.0
        target.conf = 1.0
        target.cls_id = int(self.cfg.PREFER_CLASS_ID)
        target.drone_score = 1.0
        target.lost_frames = 0
        instant_lock = bool(getattr(self.cfg, 'OPERATOR_OVERRIDE_INSTANT_LOCK', True))
        if instant_lock:
            target.hit_streak = max(int(target.hit_streak), int(self.cfg.LOCK_CONFIRM_FRAMES))
        else:
            target.hit_streak = max(1, min(int(target.hit_streak), int(self.cfg.LOCK_CONFIRM_FRAMES) - 1))
        target.source = DetectionSource.OPERATOR
        self._set_active_id(int(tid), force=True)
        if instant_lock:
            self._focus_ctrl.force_active()
            status = 'applied'
        else:
            status = 'verifying'
        return OperatorOverrideResult(True, status, active_id=int(tid), bbox=bbox)

    def confirm_active_as_operator(self) -> bool:
        active = self.get_active_target()
        if active is None:
            return False
        active.source = DetectionSource.OPERATOR
        active.conf = 1.0
        active.drone_score = 1.0
        active.lost_frames = 0
        active.hit_streak = max(int(active.hit_streak), int(self.cfg.LOCK_CONFIRM_FRAMES))
        self._focus_ctrl.force_active()
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
        return self._focus_ctrl.is_active()

    def update_focus_mode(self) -> bool:
        return self._focus_ctrl.update(self.has_confirmed_drone_lock())

    def should_run_night_detector(self) -> bool:
        return self._focus_ctrl.should_run_night_detector(self._frames_since_primary)

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

        max_reacquire_dist = min(
            self.cfg.LOCK_REACQUIRE_DIST_MAX,
            self.cfg.LOCK_REACQUIRE_DIST + min(self.cfg.REACQUIRE_SPEED_DIST_CAP, int(active.speed * self.cfg.REACQUIRE_SPEED_MULT) + active.lost_frames * self.cfg.REACQUIRE_LOST_MULT),
        )  # BUG-002: hard cap prevents radius exceeding frame on high speed/lost combos
        px, py = self._predict_center(active)
        pred_gate_dist = max_reacquire_dist + min(self.cfg.REACQUIRE_PRED_GATE_CAP, int(active.speed * self.cfg.REACQUIRE_PRED_GATE_SPEED_MULT))
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
            if source == DetectionSource.NIGHT and bool(getattr(self.cfg, "NIGHT_PRIMARY_SOURCE_ENABLED", False)):
                initial_drone_score = float(getattr(self.cfg, "NIGHT_PRIMARY_DRONE_SCORE", 0.70))
            elif self._is_primary_source(source) and cls_id >= 0:
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
                focus_max_dist = self.cfg.LOCK_REACQUIRE_DIST + min(self.cfg.FOCUS_MAX_DIST_SPEED_CAP, int(focus_target.speed * self.cfg.FOCUS_MAX_DIST_SPEED_MULT))
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
            if self._overlaps_any(det.bbox, primary_bboxes, iou_thresh=self.cfg.ROI_OVERLAP_IOU_THRESH):
                continue

            if focus_target is not None:
                fpx, fpy = self._predict_center(focus_target)
                focus_max_dist = self.cfg.LOCK_REACQUIRE_DIST + min(self.cfg.FOCUS_MAX_DIST_SPEED_CAP, int(focus_target.speed * self.cfg.FOCUS_MAX_DIST_SPEED_MULT))
                is_reacquire_candidate = (
                    self._is_drone_like_detection(det.cls_id, det.conf)
                    and self._dist(det.cx, det.cy, fpx, fpy) <= focus_max_dist
                )
                if not is_reacquire_candidate:
                    continue

            tid = self._find_nearby_track(det.cx, det.cy, max_dist=self.cfg.NIGHT_TRACK_DIST * 2, sources={DetectionSource.ROI})
            if tid is None:
                tid = self._next_aux_id
                self._next_aux_id += 1
            self._update_or_create_target(tid, det.bbox, det.cx, det.cy, det.conf, det.cls_id, DetectionSource.ROI)
            seen_roi_ids.add(tid)

        self._try_reacquire_active_from_primary(seen_roi_ids)
        return seen_roi_ids

    def update_from_night(self, night_dets: list[dict], primary_ids: set[int]) -> set[int]:
        if self.is_focus_mode():
            return set()

        primary_bboxes = [self.targets[tid].raw_bbox for tid in primary_ids if tid in self.targets]
        usable_dets = [
            det for det in night_dets
            if not self._overlaps_any(det['bbox'], primary_bboxes, iou_thresh=0.3)
        ]
        seen_night_ids = set()
        active = self.get_active_target()
        used_det_index = None
        if active is not None and active.source == DetectionSource.NIGHT and usable_dets:
            px, py = self._predict_center(active)
            hold_radius = float(getattr(self.cfg, 'NIGHT_ACTIVE_HOLD_RADIUS', 0) or 0)
            max_dist = hold_radius if hold_radius > 0 else max(
                float(self.cfg.NIGHT_TRACK_DIST),
                float(getattr(self.cfg, 'NIGHT_STICKY_RADIUS', self.cfg.NIGHT_TRACK_DIST)),
            )
            best_index = None
            best_dist = max_dist
            for index, det in enumerate(usable_dets):
                dist = self._dist(float(det['cx']), float(det['cy']), px, py)
                if dist < best_dist:
                    best_index = index
                    best_dist = dist
            if best_index is not None:
                det = usable_dets[best_index]
                key = det.get('_key')
                key = tuple(key) if key is not None else None
                if key is not None:
                    self._night_key_to_tid[key] = int(active.track_id)
                self._update_or_create_target(
                    active.track_id,
                    det['bbox'],
                    det['cx'],
                    det['cy'],
                    det.get('conf', 0.0),
                    det.get('cls_id', -1),
                    DetectionSource.NIGHT,
                )
                seen_night_ids.add(active.track_id)
                used_det_index = best_index

        for index, det in enumerate(usable_dets):
            if index == used_det_index:
                continue
            key = det.get('_key')
            key = tuple(key) if key is not None else None
            tid = self._night_key_to_tid.get(key) if key is not None else None
            if tid is not None and tid not in self.targets:
                self._night_key_to_tid.pop(key, None)
                tid = None
            if tid is None:
                tid = self._find_nearby_track(det['cx'], det['cy'], max_dist=self.cfg.NIGHT_TRACK_DIST, sources={DetectionSource.NIGHT})
            if tid is None:
                tid = self._next_aux_id
                self._next_aux_id += 1
            if key is not None:
                self._night_key_to_tid[key] = int(tid)
            self._update_or_create_target(tid, det['bbox'], det['cx'], det['cy'], det.get('conf', 0.0), det.get('cls_id', -1), DetectionSource.NIGHT)
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
                if target.source == DetectionSource.OPERATOR:
                    ttl = max(int(self.cfg.YOLO_LOST_MAX), int(getattr(self.cfg, 'OPERATOR_HOLD_GRACE_FRAMES', 20)))
                else:
                    ttl = self.cfg.YOLO_LOST_MAX if self._is_primary_source(target.source) else self.cfg.NIGHT_LOST_MAX
                if target.lost_frames > ttl:
                    dead.append(tid)
        for tid in dead:
            del self.targets[tid]
            for key, mapped_tid in list(self._night_key_to_tid.items()):
                if mapped_tid == tid:
                    del self._night_key_to_tid[key]
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
            score_value += target.conf * self.cfg.SELECT_ACTIVE_CONF_WEIGHT
            score_value += min(self.cfg.SELECT_ACTIVE_STREAK_CAP, target.hit_streak * self.cfg.SELECT_ACTIVE_STREAK_WEIGHT)
            score_value -= target.lost_frames * self.cfg.SELECT_ACTIVE_LOST_PENALTY
            if self._is_primary_source(target.source):
                score_value += self.cfg.SELECT_ACTIVE_DRONE_WEIGHT * target.drone_score
            else:
                score_value -= self.cfg.SELECT_ACTIVE_LOST_PENALTY
            return score_value

        best = max(self.targets.values(), key=score)
        if best.speed > self.cfg.SELECT_ACTIVE_MIN_SPEED or self._is_drone_like_target(best, self.cfg.DRONE_REACQUIRE_SCORE_MIN):
            self._set_active_id(best.track_id)

    def pick_active_by_trust(self, scene: str = 'day') -> None:
        """TASK-103d — Scene-conditional target selection via trust×geometry score.

        Called AFTER select_active().  When no active target exists, promotes
        the top-trust proposal.  When an active target exists, switches only if
        a competing candidate scores >TRUST_SWITCH_MARGIN better — prevents
        oscillation between equally matched targets.

        Focus-mode and strict-lock guards are respected.
        """
        if not self.targets:
            return
        if self.cfg.ACTIVE_STRICT_LOCK_SWITCH and self.is_focus_mode():
            return

        proposals = build_proposals(self.targets, scene, normalize_source)
        if not proposals:
            return

        best = proposals[0]
        current = self.get_active_target()

        if current is None:
            # TASK-103f: count down suppression window each frame while no active target.
            if self._health_suppress_frames > 0:
                self._health_suppress_frames -= 1
            # No active target: promote best if it looks like a real drone.
            target = self.targets.get(best.target_id)
            if target is None:
                return
            # Skip suppressed tid to prevent immediate re-lock after health release.
            if (best.target_id == self._health_released_tid
                    and self._health_suppress_frames > 0):
                return
            if (target.speed > self.cfg.SELECT_ACTIVE_MIN_SPEED
                    or self._is_drone_like_target(target, self.cfg.DRONE_REACQUIRE_SCORE_MIN)):
                self._set_active_id(best.target_id)
            return

        # TASK-103e: Lock health gate — runs in both code paths below.
        # Tracks consecutive frames where the active source is untrusted for
        # the current scene (trust < LOCK_HEALTH_MIN_TRUST).  After
        # LOCK_HEALTH_RELEASE_STREAK consecutive untrusted frames the active
        # target is released (→ SCAN).  Default streak=80 is well above the
        # switch cooldown (60 frames in tracking_live_auto preset) so this
        # fires only as a last-resort when the standard trust-switch has also
        # failed to fire (i.e. no better alternative ever appeared).
        def _run_health_gate() -> None:
            _ha = self.get_active_target()
            if _ha is None:
                return
            _min_trust = float(getattr(self.cfg, 'LOCK_HEALTH_MIN_TRUST', 0.50))
            if source_trust(normalize_source(_ha.source), scene) < _min_trust:
                self._low_trust_streak += 1
                _streak = int(getattr(self.cfg, 'LOCK_HEALTH_RELEASE_STREAK', 80))
                if self._low_trust_streak >= _streak:
                    # TASK-103f: suppress re-lock on the same tid for one streak window
                    self._health_released_tid = _ha.track_id
                    self._health_suppress_frames = _streak
                    self._set_active_id(None)
            else:
                self._low_trust_streak = 0

        if best.target_id == current.track_id:
            _run_health_gate()
            return  # Best is already active — nothing to switch.

        # Build current proposal for comparison.
        curr_proposals = [p for p in proposals if p.target_id == current.track_id]
        if not curr_proposals:
            _run_health_gate()
            return
        curr = curr_proposals[0]

        margin = float(getattr(self.cfg, 'TRUST_SWITCH_MARGIN', 0.25))
        if best.total_score > curr.total_score * (1.0 + margin):
            if self._can_switch_active(best.target_id):
                self._set_active_id(best.target_id)

        _run_health_gate()

    def switch_target(self):
        ids = list(self.targets.keys())
        if not ids:
            return
        if self.active_id not in ids:
            self._set_active_id(ids[0], force=True)
            return
        idx = ids.index(self.active_id)
        self._set_active_id(ids[(idx + 1) % len(ids)], force=True)
