"""TASK-103b — Bbox stability layer.

EMA smoother on bbox size (w, h) with:
- rate-limited updates (max_rate per frame in each dimension)
- conf-dependent braking (no growth when conf < conf_threshold)
- area-ratio gate (clamp to EMA size if raw/ema area ratio outside [min, max])

Center of bbox is preserved; only size is smoothed.
"""
from __future__ import annotations

__all__ = ["BboxStabilizer"]


class BboxStabilizer:
    """EMA-based bbox size smoother.

    Parameters
    ----------
    max_rate:
        Maximum fractional change per frame in each dimension (default 0.08 = 8%).
    conf_threshold:
        Detections with conf < this value may not grow the EMA.
    area_ratio_min / area_ratio_max:
        Raw-to-EMA area ratio gate.  If raw area / ema area is outside
        [min, max], the raw size is discarded and the EMA size is kept
        (center from the raw bbox is preserved).
    """

    def __init__(
        self,
        max_rate: float = 0.08,
        conf_threshold: float = 0.4,
        area_ratio_min: float = 0.4,
        area_ratio_max: float = 2.5,
    ) -> None:
        self.max_rate = max_rate
        self.conf_threshold = conf_threshold
        self.area_ratio_min = area_ratio_min
        self.area_ratio_max = area_ratio_max
        self._ema_w: float | None = None
        self._ema_h: float | None = None

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Forget EMA state.  Call on operator confirm / override so the
        next detection re-seeds without resistance from stale history."""
        self._ema_w = None
        self._ema_h = None

    # ------------------------------------------------------------------
    def update(
        self,
        bbox: tuple[int, int, int, int] | None,
        conf: float = 1.0,
    ) -> tuple[int, int, int, int] | None:
        """Return a stabilized bbox with the same center as *bbox* but
        smoothed size.  Returns ``None`` when *bbox* is ``None``.

        Args:
            bbox: Raw (x1, y1, x2, y2) from the tracker. May be None.
            conf: Detection confidence used for growth braking.
        """
        if bbox is None:
            return None

        x1, y1, x2, y2 = bbox
        raw_w = float(x2 - x1)
        raw_h = float(y2 - y1)
        if raw_w <= 0 or raw_h <= 0:
            return bbox

        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        # First detection — seed EMA and return raw bbox unchanged.
        if self._ema_w is None:
            self._ema_w = raw_w
            self._ema_h = raw_h
            return bbox

        # ---- Area-ratio gate ----------------------------------------
        raw_area = raw_w * raw_h
        ema_area = self._ema_w * self._ema_h
        if ema_area > 0:
            ratio = raw_area / ema_area
            if not (self.area_ratio_min <= ratio <= self.area_ratio_max):
                # Out of gate — hold EMA size, keep center from raw bbox.
                return self._bbox_from_center(cx, cy, self._ema_w, self._ema_h)

        # ---- Conf-dependent braking ---------------------------------
        target_w = raw_w
        target_h = raw_h
        if conf < self.conf_threshold:
            # Low confidence: allow shrink only, clamp growth.
            target_w = min(raw_w, self._ema_w)
            target_h = min(raw_h, self._ema_h)

        # ---- Rate-limited EMA step ----------------------------------
        delta_w = target_w - self._ema_w
        delta_h = target_h - self._ema_h
        cap_w = self._ema_w * self.max_rate
        cap_h = self._ema_h * self.max_rate
        self._ema_w += max(-cap_w, min(cap_w, delta_w))
        self._ema_h += max(-cap_h, min(cap_h, delta_h))

        return self._bbox_from_center(cx, cy, self._ema_w, self._ema_h)

    # ------------------------------------------------------------------
    @staticmethod
    def _bbox_from_center(
        cx: float, cy: float, w: float, h: float
    ) -> tuple[int, int, int, int]:
        hw = w / 2.0
        hh = h / 2.0
        return (int(cx - hw), int(cy - hh), int(cx + hw), int(cy + hh))
