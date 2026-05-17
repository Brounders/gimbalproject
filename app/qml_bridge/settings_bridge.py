from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot


ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = ROOT / "app" / "state" / "operator_settings.json"


DEFAULTS: dict[str, Any] = {
    "device_lat": 59.9386,
    "device_lon": 30.3141,
    "device_alt_m": 25.0,
    "heading_deg": 87.0,
    "gimbal_yaw_offset_deg": 0.0,
    "camera_pitch_deg": -8.0,
    "camera_fov_h_deg": 62.0,
    "camera_fov_v_deg": 38.0,
    "range_mode": "manual",
    "manual_range_m": 500.0,
    "trail_length_sec": 60.0,
    "prediction_horizon_sec": 12.0,
    "map_zoom": 1.0,
    "map_rotation_deg": 0.0,
    "tracker_conf_thresh": 0.30,
    "tracker_small_target_conf": 0.15,
    "tracker_img_size": 640,
    "tracker_small_target_img_size": 960,
    "tracker_night_enabled": 1,
    "tracker_night_confirm": 3,
    "tracker_lock_tracker_enabled": 1,
    "tracker_lock_confirm_frames": 5,
    "tracker_track_state_lost_frames": 8,
    "tracker_yolo_lost_max": 12,
    "tracker_roi_assist_enabled": 1,
    "tracker_roi_conf_thresh": 0.12,
    "tracker_roi_max_candidates": 3,
    "tracker_operator_annotation_enabled": 0,
    "last_video_path": "test_videos/cli_smoke_test.mp4",
}


class SettingsBridge(QObject):
    """Persistent operator settings exposed to QML."""

    changed = Signal()
    lastMessageChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data = dict(DEFAULTS)
        self._last_message = "Настройки загружены"
        self.load()

    def load(self) -> None:
        if SETTINGS_PATH.exists():
            try:
                loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self._data.update({k: loaded[k] for k in DEFAULTS if k in loaded})
            except Exception as exc:
                self._last_message = f"Ошибка чтения настроек: {exc}"
                self.lastMessageChanged.emit()
        self.changed.emit()

    @Slot()
    def save(self) -> None:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self._last_message = "Настройки сохранены"
        self.lastMessageChanged.emit()

    @Slot()
    def resetMapDefaults(self) -> None:
        for key in (
            "device_lat",
            "device_lon",
            "device_alt_m",
            "heading_deg",
            "gimbal_yaw_offset_deg",
            "camera_pitch_deg",
            "camera_fov_h_deg",
            "camera_fov_v_deg",
            "range_mode",
            "manual_range_m",
            "trail_length_sec",
            "prediction_horizon_sec",
            "map_zoom",
            "map_rotation_deg",
        ):
            self._data[key] = DEFAULTS[key]
        self.save()
        self.changed.emit()

    @Slot(str, str)
    def setValue(self, key: str, value: str) -> None:
        if key not in DEFAULTS:
            return
        old = self._data.get(key)
        try:
            if isinstance(DEFAULTS[key], bool):
                parsed: Any = str(value).strip().lower() in {"1", "true", "yes", "on", "вкл"}
            elif isinstance(DEFAULTS[key], int):
                parsed = int(round(float(str(value).replace(",", "."))))
            elif isinstance(DEFAULTS[key], float):
                parsed: Any = float(str(value).replace(",", "."))
            else:
                parsed = str(value)
        except ValueError:
            self._last_message = f"Некорректное значение: {key}"
            self.lastMessageChanged.emit()
            return
        if old == parsed:
            return
        self._data[key] = parsed
        self.save()
        self.changed.emit()

    @Slot(str, result=str)
    def value(self, key: str) -> str:
        if key not in DEFAULTS:
            return ""
        value = self._data.get(key, DEFAULTS[key])
        if isinstance(value, float):
            return f"{value:g}"
        return str(value)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, DEFAULTS.get(key, default))

    @Property(str, notify=lastMessageChanged)
    def lastMessage(self) -> str:
        return self._last_message

    @Property(float, notify=changed)
    def deviceLat(self) -> float:
        return float(self._data.get("device_lat", DEFAULTS["device_lat"]))

    @Property(float, notify=changed)
    def deviceLon(self) -> float:
        return float(self._data.get("device_lon", DEFAULTS["device_lon"]))

    @Property(float, notify=changed)
    def deviceAltM(self) -> float:
        return float(self._data.get("device_alt_m", DEFAULTS["device_alt_m"]))

    @Property(float, notify=changed)
    def headingDeg(self) -> float:
        return float(self._data.get("heading_deg", DEFAULTS["heading_deg"]))

    @Property(float, notify=changed)
    def gimbalYawOffsetDeg(self) -> float:
        return float(self._data.get("gimbal_yaw_offset_deg", DEFAULTS["gimbal_yaw_offset_deg"]))

    @Property(float, notify=changed)
    def cameraPitchDeg(self) -> float:
        return float(self._data.get("camera_pitch_deg", DEFAULTS["camera_pitch_deg"]))

    @Property(float, notify=changed)
    def cameraFovHDeg(self) -> float:
        return float(self._data.get("camera_fov_h_deg", DEFAULTS["camera_fov_h_deg"]))

    @Property(float, notify=changed)
    def cameraFovVDeg(self) -> float:
        return float(self._data.get("camera_fov_v_deg", DEFAULTS["camera_fov_v_deg"]))

    @Property(float, notify=changed)
    def manualRangeM(self) -> float:
        return float(self._data.get("manual_range_m", DEFAULTS["manual_range_m"]))

    @Property(float, notify=changed)
    def trailLengthSec(self) -> float:
        return float(self._data.get("trail_length_sec", DEFAULTS["trail_length_sec"]))

    @Property(float, notify=changed)
    def predictionHorizonSec(self) -> float:
        return float(self._data.get("prediction_horizon_sec", DEFAULTS["prediction_horizon_sec"]))

    @Property(float, notify=changed)
    def mapZoom(self) -> float:
        return float(self._data.get("map_zoom", DEFAULTS["map_zoom"]))

    @Property(float, notify=changed)
    def mapRotationDeg(self) -> float:
        return float(self._data.get("map_rotation_deg", DEFAULTS["map_rotation_deg"]))

    @Property(str, notify=changed)
    def rangeMode(self) -> str:
        return str(self._data.get("range_mode", DEFAULTS["range_mode"]))
