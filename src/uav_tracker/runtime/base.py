from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from uav_tracker.config import Config


@dataclass
class Detection:
    bbox: tuple[int, int, int, int]
    conf: float
    cls_id: int
    cx: float
    cy: float
    source: str
    track_id: int | None = None

    @classmethod
    def from_yolo(cls, box, source: str, offset: tuple[int, int] = (0, 0)) -> 'Detection':
        """Build from an Ultralytics box object.  ``offset`` is applied for crop detections."""
        ox, oy = offset
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        x1 += ox; y1 += oy; x2 += ox; y2 += oy
        return cls(
            bbox=(x1, y1, x2, y2),
            conf=float(box.conf.item()) if box.conf is not None else 0.0,
            cls_id=int(box.cls.item()) if box.cls is not None else -1,
            cx=(x1 + x2) / 2.0,
            cy=(y1 + y2) / 2.0,
            source=source,
            track_id=int(box.id.item()) if getattr(box, 'id', None) is not None else None,
        )

    @classmethod
    def from_night(cls, det: dict) -> 'Detection':
        """Build from a night-detector result dict with keys bbox/cx/cy/conf/cls_id."""
        x1, y1, x2, y2 = det['bbox']
        return cls(
            bbox=(int(x1), int(y1), int(x2), int(y2)),
            conf=float(det.get('conf', 0.0)),
            cls_id=int(det.get('cls_id', -1)),
            cx=float(det['cx']),
            cy=float(det['cy']),
            source='night',
        )

    @classmethod
    def from_lock(cls, cx: float, cy: float, bbox: tuple[int, int, int, int], conf: float) -> 'Detection':
        """Build from a template lock tracker result."""
        return cls(bbox=bbox, conf=conf, cls_id=-1, cx=cx, cy=cy, source='lock')


class DetectorBackend(Protocol):
    def track_frame(self, frame: np.ndarray, cfg: Config) -> list[Detection]:
        ...

    def predict_frame(
        self,
        frame: np.ndarray,
        cfg: Config,
        *,
        conf: float | None = None,
        imgsz: int | None = None,
        source: str = 'local',
    ) -> list[Detection]:
        ...

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
        ...
