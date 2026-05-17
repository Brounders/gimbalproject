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
        # value = {"count": int, "cx": int, "cy": int, "speed": float}
        self._candidates: dict[tuple, dict] = {}
        self._prev_gray: Optional[np.ndarray] = None
        self._warmup = 0
        self._active_key: tuple | None = None
        self._active_missing = 0

    def _find_candidate_key(self, cx: int, cy: int, used_keys: set[tuple]) -> tuple | None:
        cell = self.cfg.NIGHT_GRID_CELL
        max_dist = max(float(cell), float(getattr(self.cfg, "NIGHT_TRACK_DIST", cell)))
        max_dist_sq = max_dist * max_dist
        best_key = None
        best_dist_sq = max_dist_sq
        for key, existing in self._candidates.items():
            if key in used_keys:
                continue
            dx = float(existing["cx"] - cx)
            dy = float(existing["cy"] - cy)
            dist_sq = dx * dx + dy * dy
            if dist_sq <= best_dist_sq:
                best_key = key
                best_dist_sq = dist_sq
        if best_key is not None:
            return best_key

        gx, gy = cx // cell, cy // cell
        for sub_id in range(16):
            key = (gx, gy, sub_id)
            if key not in self._candidates and key not in used_keys:
                return key
        return None

    def _hotspot_response(self, gray: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        kernel_size = max(3, int(getattr(self.cfg, "NIGHT_HOTSPOT_KERNEL", 17) or 17))
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        top_hat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
        _, mask = cv2.threshold(
            top_hat,
            int(getattr(self.cfg, "NIGHT_HOTSPOT_THRESH", 18) or 18),
            255,
            cv2.THRESH_BINARY,
        )
        return mask, top_hat

    def _peak_rows(
        self,
        top_hat: np.ndarray,
        frame_shape: tuple[int, ...],
        motion_mask: np.ndarray,
    ) -> list[tuple[float, float, int, int, int, int]]:
        if not bool(getattr(self.cfg, "NIGHT_PEAK_ENABLED", False)):
            return []

        thresh = int(getattr(self.cfg, "NIGHT_PEAK_THRESH", 28) or 28)
        box = max(3, int(getattr(self.cfg, "NIGHT_PEAK_BOX", 24) or 24))
        nms_dist = max(1, int(getattr(self.cfg, "NIGHT_PEAK_NMS_DIST", 12) or 12))
        top_k = int(getattr(self.cfg, "NIGHT_PEAK_TOP_K", 0) or 0)
        require_motion = bool(getattr(self.cfg, "NIGHT_PEAK_REQUIRE_MOTION", False))
        min_motion_pixels = int(getattr(self.cfg, "NIGHT_PEAK_MIN_MOTION_PIXELS", 1) or 1)
        height, width = frame_shape[:2]

        dilated = cv2.dilate(top_hat, np.ones((3, 3), dtype=np.uint8))
        peak_mask = (top_hat >= thresh) & (top_hat == dilated)
        ys, xs = np.where(peak_mask)
        if xs.size == 0:
            return []

        rows = sorted(
            ((float(top_hat[y, x]), int(x), int(y)) for x, y in zip(xs, ys)),
            key=lambda row: row[0],
            reverse=True,
        )
        selected: list[tuple[float, int, int]] = []
        nms_dist_sq = float(nms_dist * nms_dist)
        for score, cx, cy in rows:
            if any((cx - sx) * (cx - sx) + (cy - sy) * (cy - sy) <= nms_dist_sq for _, sx, sy in selected):
                continue
            selected.append((score, cx, cy))
            if top_k > 0 and len(selected) >= top_k:
                break

        half = box // 2
        peak_rows = []
        for score, cx, cy in selected:
            x = max(0, min(width - 1, cx - half))
            y = max(0, min(height - 1, cy - half))
            x2 = max(x + 1, min(width, x + box))
            y2 = max(y + 1, min(height, y + box))
            motion_pixels = int(cv2.countNonZero(motion_mask[y:y2, x:x2]))
            if require_motion and motion_pixels < min_motion_pixels:
                continue
            peak_rows.append((score + float(motion_pixels) * 0.05, float((x2 - x) * (y2 - y)), x, y, x2 - x, y2 - y))
        return peak_rows

    def _select_sticky_detections(self, detections: list[dict]) -> list[dict]:
        max_detections = int(getattr(self.cfg, "NIGHT_MAX_DETECTIONS", 0) or 0)
        if not detections:
            self._active_missing += 1
            if self._active_missing > int(getattr(self.cfg, "NIGHT_STICKY_MISSING_MAX", 4) or 4):
                self._active_key = None
            return detections

        detections.sort(key=lambda det: float(det.get("score", det.get("conf", 0.0))), reverse=True)
        if not bool(getattr(self.cfg, "NIGHT_STICKY_ENABLED", False)):
            return detections[:max_detections] if max_detections > 0 else detections

        selected = None
        if self._active_key is not None:
            for det in detections:
                if det.get("_key") == self._active_key:
                    selected = det
                    break

        if selected is None and self._active_key is not None and self._active_key in self._candidates:
            active = self._candidates[self._active_key]
            radius = float(getattr(self.cfg, "NIGHT_STICKY_RADIUS", 80) or 80)
            radius_sq = radius * radius
            best_dist_sq = radius_sq
            for det in detections:
                dx = float(det["cx"]) - float(active["cx"])
                dy = float(det["cy"]) - float(active["cy"])
                dist_sq = dx * dx + dy * dy
                if dist_sq <= best_dist_sq:
                    selected = det
                    best_dist_sq = dist_sq

        if selected is None:
            selected = detections[0]

        self._active_key = selected.get("_key")
        self._active_missing = 0
        if max_detections <= 1:
            return [selected]
        rest = [det for det in detections if det is not selected]
        return [selected] + rest[: max_detections - 1]

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
        motion_thresh = thresh.copy()
        top_hat = None
        if bool(getattr(self.cfg, "NIGHT_HOTSPOT_ENABLED", False)) or bool(getattr(self.cfg, "NIGHT_PEAK_ENABLED", False)):
            hotspot, top_hat = self._hotspot_response(gray)
            thresh = cv2.bitwise_or(thresh, hotspot)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        candidate_rows = []
        if bool(getattr(self.cfg, "NIGHT_CONTOUR_ENABLED", True)):
            for cnt in contours:
                area = cv2.contourArea(cnt)
                x, y, w, h = cv2.boundingRect(cnt)
                if w <= 0 or h <= 0:
                    continue
                patch = gray[y:y + h, x:x + w]
                peak = float(patch.max()) if patch.size else 0.0
                score = peak - float(area) * 0.02
                candidate_rows.append((score, area, x, y, w, h))
        if top_hat is not None:
            candidate_rows.extend(self._peak_rows(top_hat, frame.shape, motion_thresh))
        candidate_rows.sort(key=lambda row: row[0], reverse=True)
        top_k = int(getattr(self.cfg, "NIGHT_HOTSPOT_TOP_K", 0) or 0)
        if top_k > 0:
            candidate_rows = candidate_rows[:top_k]

        detections = []
        current_keys = set()
        for _score, area, x, y, w, h in candidate_rows:
            if not (self.cfg.NIGHT_MIN_AREA <= area <= self.cfg.NIGHT_MAX_AREA):
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
            merge_key = self._find_candidate_key(cx, cy, current_keys)
            if merge_key is None:
                continue

            current_keys.add(merge_key)
            if merge_key not in self._candidates:
                self._candidates[merge_key] = {
                    "count": 0,
                    "cx": cx,
                    "cy": cy,
                    "speed": 0.0,
                    "area": float(area),
                    "response": float(_score),
                }
            entry = self._candidates[merge_key]
            dx = float(cx - entry["cx"])
            dy = float(cy - entry["cy"])
            speed = (dx * dx + dy * dy) ** 0.5
            entry["speed"] = 0.65 * float(entry.get("speed", 0.0)) + 0.35 * speed
            entry["area"] = 0.70 * float(entry.get("area", area)) + 0.30 * float(area)
            entry["response"] = 0.60 * float(entry.get("response", _score)) + 0.40 * float(_score)
            entry["count"] += 1
            entry["cx"] = cx  # update to latest position
            entry["cy"] = cy
            if entry["count"] >= self.cfg.NIGHT_CONFIRM:
                min_speed = float(getattr(self.cfg, "NIGHT_MIN_SPEED", 0.0) or 0.0)
                max_speed = float(getattr(self.cfg, "NIGHT_MAX_SPEED", 0.0) or 0.0)
                if min_speed > 0.0 and float(entry["speed"]) < min_speed:
                    continue
                if max_speed > 0.0 and float(entry["speed"]) > max_speed:
                    continue
                conf = min(0.6, 0.2 + entry["count"] * 0.05)
                score = (
                    float(entry["count"])
                    + float(entry["speed"]) * 0.20
                    + float(entry.get("response", 0.0)) * 0.04
                    - float(entry["area"]) * 0.004
                )
                detections.append(
                    {
                        "bbox": (x, y, x + w, y + h),
                        "conf": conf,
                        "cx": cx,
                        "cy": cy,
                        "source": "night",
                        "score": score,
                        "speed": float(entry["speed"]),
                        "_key": merge_key,
                    }
                )

        gone = set(self._candidates.keys()) - current_keys
        for key in gone:
            self._candidates[key]["count"] = max(0, self._candidates[key]["count"] - 1)
            if self._candidates[key]["count"] == 0:
                del self._candidates[key]

        return self._select_sticky_detections(detections)
