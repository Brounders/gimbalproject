from typing import Optional

import cv2
import numpy as np

from uav_tracker.config import Config


class NightSmallTargetDetector:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=50, varThreshold=25, detectShadows=False
        )
        self._candidates: dict[tuple, int] = {}
        self._prev_gray: Optional[np.ndarray] = None
        self._warmup = 0

    def detect(self, frame: np.ndarray) -> list[dict]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

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

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
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
            key = (cx // 8, cy // 8)
            current_keys.add(key)
            self._candidates[key] = self._candidates.get(key, 0) + 1
            if self._candidates[key] >= self.cfg.NIGHT_CONFIRM:
                conf = min(0.6, 0.2 + self._candidates[key] * 0.05)
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
            self._candidates[key] = max(0, self._candidates[key] - 1)
            if self._candidates[key] == 0:
                del self._candidates[key]

        return detections
