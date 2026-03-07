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
