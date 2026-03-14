"""uav_tracker/display_state_tracker.py — Display-only visual state.

Extracted from TrackerPipeline (A08 Stage 4).
Manages confidence EMA, reticle center EMA, and smooth display bbox —
three concerns that exist solely to produce stable visuals without
affecting quality-gate metrics.
"""
from __future__ import annotations

from typing import Optional

from uav_tracker.config import Config
from uav_tracker.tracking.target_manager import TrackedTarget


class DisplayStateTracker:
    """Accumulates display-smoothing state for one tracking session.

    All three sub-concerns (confidence, reticle, bbox) are updated per-frame
    by calling the respective update_*() methods.  Each returns the value for
    the current frame ready to pass directly to draw_frame().
    """

    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        # Confidence EMA
        self._confidence_ema: float = 0.0
        self._display_confidence: float = 0.0
        self._confidence_last_update_sec: float = 0.0
        # Reticle
        self._reticle_center: Optional[tuple[float, float]] = None
        self._reticle_missing_streak: int = 0
        # Smooth bbox
        self._smooth_bbox: Optional[list[float]] = None   # [cx, cy, w, h]
        self._smooth_bbox_missing: int = 0

    # ── Confidence ────────────────────────────────────────────────────────────

    def update_confidence(
        self,
        active: Optional[TrackedTarget],
        lock_score: float,
        video_elapsed_sec: float,
        frame_counter: int,
    ) -> float:
        """Return display-smoothed tracking confidence in [0, 1].

        Args:
            active: current active TrackedTarget or None.
            lock_score: template lock score (0 if not locked).
            video_elapsed_sec: cumulative elapsed video time in seconds.
            frame_counter: number of frames processed so far (for warm-up).
        """
        instant = self._instant_confidence(active, lock_score)
        alpha = max(0.01, min(0.95, float(self._cfg.CONFIDENCE_EMA_ALPHA)))
        self._confidence_ema = (1.0 - alpha) * self._confidence_ema + alpha * instant

        period = max(0.5, float(self._cfg.CONFIDENCE_DISPLAY_UPDATE_SEC))
        if video_elapsed_sec - self._confidence_last_update_sec >= period:
            self._display_confidence = self._confidence_ema
            self._confidence_last_update_sec = video_elapsed_sec

        if frame_counter <= 3:
            self._display_confidence = self._confidence_ema
        return max(0.0, min(1.0, self._display_confidence))

    def _instant_confidence(self, active: Optional[TrackedTarget], lock_score: float) -> float:
        if active is None:
            return 0.0
        streak_norm = min(1.0, float(active.hit_streak) / max(1.0, float(self._cfg.LOCK_CONFIRM_FRAMES)))
        lock_norm = float(lock_score) if lock_score > 0.0 else float(active.conf)
        value = 0.45 * float(active.conf) + 0.35 * lock_norm + 0.20 * streak_norm
        if active.lost_frames > 0:
            value *= max(0.2, 1.0 - 0.2 * float(active.lost_frames))
        return max(0.0, min(1.0, value))

    # ── Reticle ───────────────────────────────────────────────────────────────

    def update_reticle(self, active: Optional[TrackedTarget]) -> Optional[tuple[int, int]]:
        """Return EMA-smoothed reticle center pixel coordinates, or None."""
        if active is not None:
            x1, y1, x2, y2 = active.bbox
            cx = float((x1 + x2) * 0.5)
            cy = float((y1 + y2) * 0.5)
            if active.lost_frames > 0:
                horizon = max(1, min(int(self._cfg.LOCK_REACQUIRE_PREDICT_HORIZON_MAX), active.lost_frames))
                gain = float(self._cfg.LOCK_REACQUIRE_PREDICT_GAIN)
                cx += float(active.vx) * horizon * gain
                cy += float(active.vy) * horizon * gain
            alpha = max(0.01, min(0.95, float(self._cfg.RETICLE_CENTER_ALPHA)))
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
            if self._reticle_missing_streak > max(1, int(self._cfg.RETICLE_HOLD_FRAMES)):
                self._reticle_center = None
                self._reticle_missing_streak = 0

        if self._reticle_center is None:
            return None
        return int(self._reticle_center[0]), int(self._reticle_center[1])

    # ── Smooth bbox ───────────────────────────────────────────────────────────

    def update_smooth_bbox(
        self, active: Optional[TrackedTarget]
    ) -> Optional[tuple[int, int, int, int]]:
        """Return EMA-smoothed bbox (x1, y1, x2, y2) for display, or None.

        Center position uses SMOOTH_BBOX_ALPHA.
        Width/height use softer SMOOTH_BBOX_SIZE_ALPHA to damp size jitter.
        Holds last bbox for SMOOTH_BBOX_HOLD_FRAMES when target is absent.
        """
        alpha_pos = max(0.05, min(0.95, float(getattr(self._cfg, 'SMOOTH_BBOX_ALPHA', 0.35))))
        alpha_sz = max(0.05, min(0.95, float(getattr(self._cfg, 'SMOOTH_BBOX_SIZE_ALPHA', 0.20))))
        hold = max(0, int(getattr(self._cfg, 'SMOOTH_BBOX_HOLD_FRAMES', 4)))

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
