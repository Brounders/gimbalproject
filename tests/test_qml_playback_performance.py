"""TASK-126 — QML playback data-path performance guards."""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage

from app.qml_bridge.frame_provider import FrameProvider
from app.qml_bridge.tracker_bridge import TrackerBridge
from app.workers import _qimage_from_bgr_frame


def test_worker_converts_bgr_frame_to_qimage():
    frame = np.zeros((8, 10, 3), dtype=np.uint8)
    frame[:, :, 2] = 255

    image = _qimage_from_bgr_frame(frame)

    assert isinstance(image, QImage)
    assert image.width() == 10
    assert image.height() == 8


def test_frame_provider_accepts_prebuilt_qimage():
    provider = FrameProvider()
    image = QImage(13, 7, QImage.Format_RGB888)

    provider.update_frame(image)
    size = QSize()
    returned = provider.requestImage("current", size, QSize())

    assert returned.width() == 13
    assert returned.height() == 7
    assert size.width() == 13
    assert size.height() == 7


def test_tracker_bridge_latency_uses_total_timing_not_sum():
    bridge = TrackerBridge(FrameProvider())
    bridge._on_stats_ready(
        {
            "mode": "SCAN",
            "timings_ms": {"global": 30.0, "night": 10.0, "manager": 1.0, "total": 45.0},
            "frame_width": 640,
            "frame_height": 480,
        }
    )

    assert bridge.latencyMs == 45
