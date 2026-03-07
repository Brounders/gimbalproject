from typing import Optional

import cv2
import numpy as np
from ultralytics import YOLO

from uav_tracker.config import Config


class MotionROIProposer:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._prev_gray: Optional[np.ndarray] = None

    def propose(self, frame: np.ndarray, max_candidates: Optional[int] = None) -> list[tuple[int, int, int, int]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        if self._prev_gray is None:
            self._prev_gray = gray
            return []

        diff = cv2.absdiff(gray, self._prev_gray)
        self._prev_gray = gray
        _, mask = cv2.threshold(diff, self.cfg.ROI_DIFF_THRESH, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        proposals = []
        h, w = frame.shape[:2]
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if not (self.cfg.ROI_MIN_AREA <= area <= self.cfg.ROI_MAX_AREA):
                continue
            x, y, bw, bh = cv2.boundingRect(cnt)
            cx, cy = x + bw // 2, y + bh // 2
            size = max(self.cfg.ROI_MIN_SIZE, max(bw, bh) + self.cfg.ROI_PADDING * 2)
            x1 = max(0, cx - size // 2)
            y1 = max(0, cy - size // 2)
            x2 = min(w, x1 + size)
            y2 = min(h, y1 + size)
            x1 = max(0, x2 - size)
            y1 = max(0, y2 - size)
            proposals.append((int(x1), int(y1), int(x2), int(y2), float(area)))

        proposals.sort(key=lambda r: r[4], reverse=True)
        merged: list[tuple[int, int, int, int, float]] = []
        limit = int(max_candidates) if max_candidates is not None else int(self.cfg.ROI_MAX_CANDIDATES)
        limit = max(1, limit)
        for roi in proposals:
            if len(merged) >= limit:
                break
            if any(self._iou4(roi[:4], m[:4]) > 0.2 for m in merged):
                continue
            merged.append(roi)
        return [m[:4] for m in merged]

    @staticmethod
    def _iou4(a, b) -> float:
        xi1, yi1 = max(a[0], b[0]), max(a[1], b[1])
        xi2, yi2 = min(a[2], b[2]), min(a[3], b[3])
        inter = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        if inter <= 0:
            return 0.0
        ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
        return inter / ua if ua > 0 else 0.0


def infer_roi_detections(
    model: YOLO,
    frame: np.ndarray,
    rois: list[tuple[int, int, int, int]],
    cfg: Config,
) -> list[dict]:
    if not rois:
        return []

    crops = []
    metas = []
    for roi in rois:
        x1, y1, x2, y2 = roi
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        crops.append(crop)
        metas.append(roi)
    if not crops:
        return []

    results = model.predict(
        crops,
        conf=cfg.ROI_CONF_THRESH,
        iou=cfg.IOU_THRESH,
        imgsz=cfg.ROI_IMG_SIZE,
        device=cfg.DEVICE,
        classes=cfg.CLASSES,
        verbose=False,
    )

    detections = []
    for res, (ox1, oy1, _ox2, _oy2) in zip(results, metas):
        if res.boxes is None:
            continue
        for box in res.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cls_id = int(box.cls.item()) if box.cls is not None else -1
            conf = float(box.conf.item()) if box.conf is not None else 0.0
            gx1, gy1 = ox1 + x1, oy1 + y1
            gx2, gy2 = ox1 + x2, oy1 + y2
            if gx2 <= gx1 or gy2 <= gy1:
                continue
            detections.append(
                {
                    "bbox": (gx1, gy1, gx2, gy2),
                    "conf": conf,
                    "cls_id": cls_id,
                    "cx": (gx1 + gx2) / 2,
                    "cy": (gy1 + gy2) / 2,
                    "source": "roi",
                }
            )
    return detections
