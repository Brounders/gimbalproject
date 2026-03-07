from __future__ import annotations

import numpy as np

from uav_tracker.config import Config


class HailoBackend:
    def __init__(self, model_path: str):
        self.model_path = model_path

    def _not_ready(self):
        raise NotImplementedError(
            'Hailo backend scaffold создан, но runtime интеграция ещё не подключена. '
            'Следующий этап: hailort + postprocess adapter для .hef.'
        )

    def track_frame(self, frame: np.ndarray, cfg: Config):
        self._not_ready()

    def predict_frame(self, frame: np.ndarray, cfg: Config, *, conf=None, imgsz=None, source='local'):
        self._not_ready()

    def predict_crops(self, frame: np.ndarray, rois, cfg: Config, *, conf=None, imgsz=None, source='roi'):
        self._not_ready()
