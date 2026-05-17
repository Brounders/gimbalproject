from __future__ import annotations

import threading

import numpy as np
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider


class FrameProvider(QQuickImageProvider):
    """Expose the latest OpenCV frame to QML as image://frames/current."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)
        self._lock = threading.RLock()
        self._image = QImage(960, 540, QImage.Format_RGB32)
        self._image.fill(0x050810)

    def update_frame(self, frame: np.ndarray) -> None:
        if frame is None or frame.size == 0:
            return
        if frame.ndim != 3 or frame.shape[2] < 3:
            return
        height, width = frame.shape[:2]
        rgb = frame[:, :, :3][:, :, ::-1].copy()
        image = QImage(rgb.data, width, height, rgb.strides[0], QImage.Format_RGB888).copy()
        with self._lock:
            self._image = image

    def requestImage(self, id_: str, size: QSize, requested_size: QSize) -> QImage:
        _ = id_
        with self._lock:
            image = self._image.copy()
        if requested_size.isValid() and requested_size.width() > 0 and requested_size.height() > 0:
            image = image.scaled(
                requested_size,
                aspectMode=Qt.KeepAspectRatio,
                mode=Qt.SmoothTransformation,
            )
        size.setWidth(image.width())
        size.setHeight(image.height())
        return image
