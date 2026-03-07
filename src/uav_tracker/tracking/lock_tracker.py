from __future__ import annotations

import cv2
import numpy as np

from uav_tracker.config import Config


class TemplateLockTracker:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.template: np.ndarray | None = None
        self.bbox: tuple[int, int, int, int] | None = None
        self.last_score: float = 0.0

    def reset(self) -> None:
        self.template = None
        self.bbox = None
        self.last_score = 0.0

    def _gray(self, frame: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def _clip_bbox(self, bbox: tuple[int, int, int, int], shape: tuple[int, int]) -> tuple[int, int, int, int] | None:
        h, w = shape
        x1, y1, x2, y2 = bbox
        x1 = max(0, min(w - 1, int(x1)))
        y1 = max(0, min(h - 1, int(y1)))
        x2 = max(0, min(w, int(x2)))
        y2 = max(0, min(h, int(y2)))
        if x2 - x1 < 4 or y2 - y1 < 4:
            return None
        return x1, y1, x2, y2

    def sync_from_bbox(self, frame: np.ndarray, bbox: tuple[int, int, int, int]) -> None:
        clipped = self._clip_bbox(bbox, frame.shape[:2])
        if clipped is None:
            return
        x1, y1, x2, y2 = clipped
        gray = self._gray(frame)
        patch = gray[y1:y2, x1:x2]
        if patch.size == 0:
            return
        if self.template is None or self.template.shape != patch.shape:
            self.template = patch.copy()
        else:
            alpha = float(self.cfg.LOCK_TRACKER_UPDATE_ALPHA)
            self.template = cv2.addWeighted(patch, alpha, self.template, 1.0 - alpha, 0.0)
        self.bbox = clipped

    def predict(self, frame: np.ndarray) -> tuple[dict, float, tuple[int, int, int, int]] | tuple[None, float, None]:
        if self.template is None or self.bbox is None:
            return None, 0.0, None

        h, w = frame.shape[:2]
        x1, y1, x2, y2 = self.bbox
        bw = x2 - x1
        bh = y2 - y1
        search_scale = float(self.cfg.LOCK_TRACKER_SEARCH_SCALE)
        pad_x = int(max(bw, 12) * search_scale)
        pad_y = int(max(bh, 12) * search_scale)
        sx1 = max(0, x1 - pad_x)
        sy1 = max(0, y1 - pad_y)
        sx2 = min(w, x2 + pad_x)
        sy2 = min(h, y2 + pad_y)
        if sx2 - sx1 <= bw or sy2 - sy1 <= bh:
            return None, 0.0, None

        gray = self._gray(frame)
        search = gray[sy1:sy2, sx1:sx2]
        if search.shape[0] < self.template.shape[0] or search.shape[1] < self.template.shape[1]:
            return None, 0.0, None

        response = cv2.matchTemplate(search, self.template, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(response)
        score = float(max_val)
        self.last_score = score
        if score < self.cfg.LOCK_TRACKER_MIN_SCORE:
            return None, score, (sx1, sy1, sx2, sy2)

        px1 = sx1 + int(max_loc[0])
        py1 = sy1 + int(max_loc[1])
        px2 = px1 + self.template.shape[1]
        py2 = py1 + self.template.shape[0]
        pred_bbox = self._clip_bbox((px1, py1, px2, py2), frame.shape[:2])
        if pred_bbox is None:
            return None, score, (sx1, sy1, sx2, sy2)
        self.bbox = pred_bbox
        px1, py1, px2, py2 = pred_bbox
        return (
            {
                'bbox': pred_bbox,
                'conf': score,
                'cls_id': -1,
                'cx': (px1 + px2) / 2,
                'cy': (py1 + py2) / 2,
                'source': 'lock',
            },
            score,
            (sx1, sy1, sx2, sy2),
        )
