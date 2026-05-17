from __future__ import annotations

import math
import time
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot

from app.qml_bridge.settings_bridge import SettingsBridge


EARTH_RADIUS_M = 6_371_000.0


def _destination(lat_deg: float, lon_deg: float, bearing_deg: float, distance_m: float) -> tuple[float, float]:
    lat1 = math.radians(lat_deg)
    lon1 = math.radians(lon_deg)
    brng = math.radians(bearing_deg)
    dr = max(0.0, distance_m) / EARTH_RADIUS_M
    lat2 = math.asin(
        math.sin(lat1) * math.cos(dr)
        + math.cos(lat1) * math.sin(dr) * math.cos(brng)
    )
    lon2 = lon1 + math.atan2(
        math.sin(brng) * math.sin(dr) * math.cos(lat1),
        math.cos(dr) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


class GeoBridge(QObject):
    """Compute map geometry from settings and tracker stats."""

    changed = Signal()

    def __init__(self, settings: SettingsBridge, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._target_lat = settings.deviceLat
        self._target_lon = settings.deviceLon
        self._target_bearing = settings.headingDeg + settings.gimbalYawOffsetDeg
        self._target_range_m = settings.manualRangeM
        self._target_valid = False
        self._target_x = 0.5
        self._target_y = 0.5
        self._last_update_s = 0.0
        self._trail: list[tuple[float, float]] = []
        settings.changed.connect(self._on_settings_changed)

    @Property(float, notify=changed)
    def targetLat(self) -> float:
        return float(self._target_lat)

    @Property(float, notify=changed)
    def targetLon(self) -> float:
        return float(self._target_lon)

    @Property(float, notify=changed)
    def targetBearingDeg(self) -> float:
        return float(self._target_bearing)

    @Property(float, notify=changed)
    def targetRangeM(self) -> float:
        return float(self._target_range_m)

    @Property(bool, notify=changed)
    def targetValid(self) -> bool:
        return bool(self._target_valid)

    @Property(float, notify=changed)
    def targetX(self) -> float:
        return float(self._target_x)

    @Property(float, notify=changed)
    def targetY(self) -> float:
        return float(self._target_y)

    @Property(str, notify=changed)
    def trailJson(self) -> str:
        items = [{"x": round(x, 5), "y": round(y, 5)} for x, y in self._trail[-80:]]
        import json

        return json.dumps(items, separators=(",", ":"))

    @Slot(dict)
    def updateFromStats(self, stats: dict) -> None:
        bbox = stats.get("active_bbox")
        frame_w = int(stats.get("frame_width") or 0)
        frame_h = int(stats.get("frame_height") or 0)
        if not bbox or frame_w <= 0 or frame_h <= 0:
            self._target_valid = False
            self.changed.emit()
            return
        try:
            x1, y1, x2, y2 = [float(v) for v in bbox[:4]]
        except (TypeError, ValueError):
            self._target_valid = False
            self.changed.emit()
            return

        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        norm_x = (cx / max(1.0, float(frame_w))) - 0.5
        norm_y = (cy / max(1.0, float(frame_h))) - 0.5
        bearing_offset = norm_x * float(self._settings.cameraFovHDeg)
        bearing = (
            float(self._settings.headingDeg)
            + float(self._settings.gimbalYawOffsetDeg)
            + bearing_offset
        ) % 360.0
        distance = max(1.0, float(self._settings.manualRangeM))
        lat, lon = _destination(
            float(self._settings.deviceLat),
            float(self._settings.deviceLon),
            bearing,
            distance,
        )

        # Relative tactical canvas coordinate: device in center, range scaled by configured range.
        radius = min(0.42, 0.16 + min(1.0, distance / max(distance, 1.0)) * 0.20)
        br = math.radians(bearing)
        tx = max(0.06, min(0.94, 0.5 + math.sin(br) * radius))
        ty = max(0.06, min(0.94, 0.5 - math.cos(br) * radius))

        self._target_lat = lat
        self._target_lon = lon
        self._target_bearing = bearing
        self._target_range_m = distance
        self._target_valid = True
        self._target_x = tx
        self._target_y = ty
        now = time.monotonic()
        if now - self._last_update_s > 0.6:
            self._trail.append((tx, ty))
            max_points = max(8, int(float(self._settings.trailLengthSec) / 1.4))
            self._trail = self._trail[-max_points:]
            self._last_update_s = now
        self.changed.emit()

    @Slot()
    def resetTarget(self) -> None:
        self._target_valid = False
        self._trail.clear()
        self.changed.emit()

    def _on_settings_changed(self) -> None:
        if not self._target_valid:
            self._target_bearing = float(self._settings.headingDeg) + float(self._settings.gimbalYawOffsetDeg)
            self._target_range_m = float(self._settings.manualRangeM)
            self.changed.emit()
