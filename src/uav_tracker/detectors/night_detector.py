from typing import Optional

import cv2
import numpy as np

from uav_tracker.config import Config


class NightSmallTargetDetector:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=cfg.NIGHT_MOG2_HISTORY, varThreshold=cfg.NIGHT_MOG2_VAR_THRESH, detectShadows=False
        )
        # BUG-005: store (cx, cy) per unique candidate so nearby objects in the
        # same grid cell don't merge their confidence counters.
        # key = (grid_x, grid_y, sub_id) where sub_id disambiguates collisions.
        # value = {"count": int, "cx": int, "cy": int}
        self._candidates: dict[tuple, dict] = {}
        self._prev_gray: Optional[np.ndarray] = None
        self._warmup = 0

    def detect(self, frame: np.ndarray) -> list[dict]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (self.cfg.NIGHT_BLUR_KERNEL, self.cfg.NIGHT_BLUR_KERNEL), 0)

        fg_mask = self.bg_subtractor.apply(gray)
        if self._prev_gray is None:
            self._prev_gray = gray
            return []

        frame_diff = cv2.absdiff(gray, self._prev_gray)
        self._prev_gray = gray
        _, diff_mask = cv2.threshold(
            frame_diff, self.cfg.NIGHT_DIFF_THRESH, 255, cv2.THRESH_BINARY
        )
        self._warmup += 1
        if self._warmup < self.cfg.NIGHT_HIST_LEN:
            return []

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.cfg.NIGHT_MORPH_KERNEL, self.cfg.NIGHT_MORPH_KERNEL))
        fg_mask = cv2.bitwise_and(fg_mask, diff_mask)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        _, thresh = cv2.threshold(
            fg_mask, self.cfg.NIGHT_MOT_THRESH, 255, cv2.THRESH_BINARY
        )

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        detections = []
        current_keys = set()
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if not (self.cfg.NIGHT_MIN_AREA <= area <= self.cfg.NIGHT_MAX_AREA):
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            if w == 0 or h == 0:
                continue
            ar = max(w / h, h / w)
            if ar > self.cfg.NIGHT_MAX_AR:
                continue
            if (
                x <= self.cfg.NIGHT_BORDER
                or y <= self.cfg.NIGHT_BORDER
                or (x + w) >= frame.shape[1] - self.cfg.NIGHT_BORDER
                or (y + h) >= frame.shape[0] - self.cfg.NIGHT_BORDER
            ):
                continue

            cx, cy = x + w // 2, y + h // 2
            cell = self.cfg.NIGHT_GRID_CELL
            gx, gy = cx // cell, cy // cell
            # BUG-005: find matching candidate within spatial radius, not just grid cell
            merge_key = None
            for sub_id in range(8):  # max 8 distinct objects per grid cell
                k = (gx, gy, sub_id)
                if k not in self._candidates:
                    merge_key = k   # first free slot → new candidate
                    break
                existing = self._candidates[k]
                dx = existing["cx"] - cx
                dy = existing["cy"] - cy
                if dx * dx + dy * dy <= cell * cell:  # within one grid cell radius
                    merge_key = k   # same spatial object
                    break
            if merge_key is None:
                continue  # too many distinct objects in this cell — skip

            current_keys.add(merge_key)
            if merge_key not in self._candidates:
                self._candidates[merge_key] = {"count": 0, "cx": cx, "cy": cy}
            entry = self._candidates[merge_key]
            entry["count"] += 1
            entry["cx"] = cx  # update to latest position
            entry["cy"] = cy
            if entry["count"] >= self.cfg.NIGHT_CONFIRM:
                conf = min(0.6, 0.2 + entry["count"] * 0.05)
                detections.append(
                    {
                        "bbox": (x, y, x + w, y + h),
                        "conf": conf,
                        "cx": cx,
                        "cy": cy,
                        "source": "night",
                    }
                )

        gone = set(self._candidates.keys()) - current_keys
        for key in gone:
            self._candidates[key]["count"] = max(0, self._candidates[key]["count"] - 1)
            if self._candidates[key]["count"] == 0:
                del self._candidates[key]

        return detections
