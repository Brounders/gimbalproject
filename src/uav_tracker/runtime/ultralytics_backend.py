from __future__ import annotations

import logging
from typing import Iterable

import numpy as np
from ultralytics import YOLO

from uav_tracker.config import Config
from uav_tracker.runtime.base import Detection

logger = logging.getLogger(__name__)


class UltralyticsBackend:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    @staticmethod
    def _box_to_detection(box, source: str, offset: tuple[int, int] = (0, 0)) -> Detection:
        ox, oy = offset
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        x1 += ox
        y1 += oy
        x2 += ox
        y2 += oy
        cls_id = int(box.cls.item()) if box.cls is not None else -1
        conf = float(box.conf.item()) if box.conf is not None else 0.0
        track_id = int(box.id.item()) if getattr(box, 'id', None) is not None else None
        return Detection(
            bbox=(x1, y1, x2, y2),
            conf=conf,
            cls_id=cls_id,
            cx=(x1 + x2) / 2,
            cy=(y1 + y2) / 2,
            source=source,
            track_id=track_id,
        )

    def _predict_impl(
        self,
        inputs: np.ndarray | list[np.ndarray],
        cfg: Config,
        *,
        conf: float,
        imgsz: int,
        track: bool,
    ):
        if track:
            return self.model.track(
                inputs,
                conf=conf,
                iou=cfg.IOU_THRESH,
                imgsz=imgsz,
                device=cfg.DEVICE,
                persist=True,
                classes=cfg.CLASSES,
                tracker='bytetrack.yaml',
                verbose=False,
            )
        return self.model.predict(
            inputs,
            conf=conf,
            iou=cfg.IOU_THRESH,
            imgsz=imgsz,
            device=cfg.DEVICE,
            classes=cfg.CLASSES,
            verbose=False,
        )

    def track_frame(self, frame: np.ndarray, cfg: Config) -> list[Detection]:
        try:
            results = self._predict_impl(frame, cfg, conf=cfg.CONF_THRESH, imgsz=cfg.IMG_SIZE, track=True)
        except Exception:
            logger.exception('track_frame: ошибка при вызове YOLO track')
            return []
        if not results or results[0].boxes is None:
            return []
        return [self._box_to_detection(box, 'yolo') for box in results[0].boxes if getattr(box, 'id', None) is not None]

    def predict_frame(
        self,
        frame: np.ndarray,
        cfg: Config,
        *,
        conf: float | None = None,
        imgsz: int | None = None,
        source: str = 'local',
    ) -> list[Detection]:
        try:
            results = self._predict_impl(frame, cfg, conf=conf or cfg.CONF_THRESH, imgsz=imgsz or cfg.IMG_SIZE, track=False)
        except Exception:
            logger.exception('predict_frame: ошибка при вызове YOLO predict')
            return []
        if not results or results[0].boxes is None:
            return []
        return [self._box_to_detection(box, source) for box in results[0].boxes]

    def predict_crops(
        self,
        frame: np.ndarray,
        rois: list[tuple[int, int, int, int]],
        cfg: Config,
        *,
        conf: float | None = None,
        imgsz: int | None = None,
        source: str = 'roi',
    ) -> list[Detection]:
        if not rois:
            return []

        crops: list[np.ndarray] = []
        metas: list[tuple[int, int, int, int]] = []
        for x1, y1, x2, y2 in rois:
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            crops.append(crop)
            metas.append((x1, y1, x2, y2))
        if not crops:
            return []

        results = self._predict_impl(crops, cfg, conf=conf or cfg.ROI_CONF_THRESH, imgsz=imgsz or cfg.ROI_IMG_SIZE, track=False)
        detections: list[Detection] = []
        for result, (x1, y1, _x2, _y2) in zip(results, metas):
            if result.boxes is None:
                continue
            for box in result.boxes:
                detections.append(self._box_to_detection(box, source, offset=(x1, y1)))
        return detections
