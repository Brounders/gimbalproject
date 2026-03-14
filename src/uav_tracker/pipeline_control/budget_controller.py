"""uav_tracker/budget_controller.py — CPU budget adaptation for TrackerPipeline.

Extracted from TrackerPipeline (A08 Stage 1).
Tracks CPU load EMA and adapts scan/validate/ROI/night frequencies accordingly.
"""
from __future__ import annotations

from uav_tracker.config import Config


class BudgetController:
    """Adapts pipeline scan frequency to stay within CPU budget.

    Tracks an EMA of per-frame processing time relative to a target FPS and
    raises/lowers a budget level (0–BUDGET_LEVEL_MAX) that callers use to
    skip expensive operations.

    Attributes:
        level: Current budget level (0 = normal, higher = more aggressive skipping).
        load_ema: EMA of normalised frame load (1.0 = exactly at target FPS).
        last_frame_ms: Total pipeline ms for the last completed frame.
        last_roi_candidates: Effective ROI candidate limit at last query.
        last_night_skip: Night-detector run-every-N-frames at last query.
    """

    def __init__(self, cfg: Config, initial_roi_candidates: int = 1) -> None:
        self._cfg = cfg
        self.level: int = 0
        self.load_ema: float = 1.0
        self.last_frame_ms: float = 0.0
        self.last_roi_candidates: int = initial_roi_candidates
        self.last_night_skip: int = 1

    # ── Effective parameter helpers ──────────────────────────────────────────

    def effective_global_scan_interval(self, frame_counter: int) -> int:
        base = max(1, int(self._cfg.GLOBAL_SCAN_INTERVAL))
        if not self._cfg.BUDGET_ENABLED:
            return base
        boost = max(0, int(self._cfg.BUDGET_SCAN_INTERVAL_BOOST_PER_LEVEL))
        return max(1, base + boost * self.level)

    def effective_local_validate_interval(self, frame_counter: int) -> int:
        base = max(1, int(self._cfg.LOCAL_VALIDATE_INTERVAL))
        if not self._cfg.BUDGET_ENABLED:
            return base
        boost = max(0, int(self._cfg.BUDGET_LOCAL_VALIDATE_BOOST_PER_LEVEL))
        return max(1, base + boost * self.level)

    def effective_roi_max_candidates(self) -> int:
        base = max(1, int(self._cfg.ROI_MAX_CANDIDATES))
        if not self._cfg.BUDGET_ENABLED:
            self.last_roi_candidates = base
            return base
        min_candidates = max(1, int(self._cfg.BUDGET_ROI_MIN_CANDIDATES))
        result = max(min_candidates, base - self.level)
        self.last_roi_candidates = result
        return result

    def _effective_night_skip(self) -> int:
        if not self._cfg.BUDGET_ENABLED:
            return 1
        if self.level <= 0:
            return 1
        if self.level == 1:
            return max(1, int(self._cfg.BUDGET_NIGHT_SKIP_LEVEL1))
        return max(1, int(self._cfg.BUDGET_NIGHT_SKIP_LEVEL2))

    # ── Run-gate helpers ─────────────────────────────────────────────────────

    def should_run_night(self, frame_counter: int) -> bool:
        skip = self._effective_night_skip()
        self.last_night_skip = skip
        if skip <= 1:
            return True
        return (frame_counter % skip) == 0

    def should_run_roi(self, frame_counter: int) -> bool:
        if not self._cfg.BUDGET_ENABLED:
            return True
        skip = max(1, int(self._cfg.BUDGET_ROI_SKIP_LEVEL2))
        if self.level < 2 or skip <= 1:
            return True
        return (frame_counter % skip) == 0

    # ── State update ─────────────────────────────────────────────────────────

    def update(self, timings_ms: dict[str, float]) -> None:
        """Update budget level based on last-frame timings."""
        self.last_frame_ms = (
            float(timings_ms.get('global', 0.0))
            + float(timings_ms.get('lock', 0.0))
            + float(timings_ms.get('local', 0.0))
            + float(timings_ms.get('roi', 0.0))
            + float(timings_ms.get('night', 0.0))
            + float(timings_ms.get('draw', 0.0))
        )
        if not self._cfg.BUDGET_ENABLED:
            self.level = 0
            self.load_ema = 1.0
            return

        target_fps = max(5.0, float(self._cfg.BUDGET_TARGET_FPS))
        target_ms = 1000.0 / target_fps
        load = self.last_frame_ms / max(target_ms, 1.0)
        self.load_ema = 0.86 * self.load_ema + 0.14 * load

        max_level = max(0, int(self._cfg.BUDGET_LEVEL_MAX))
        high = float(self._cfg.BUDGET_HIGH_LOAD)
        low = float(self._cfg.BUDGET_LOW_LOAD)
        if self.load_ema > high and self.level < max_level:
            self.level += 1
        elif self.load_ema < low and self.level > 0:
            self.level -= 1
