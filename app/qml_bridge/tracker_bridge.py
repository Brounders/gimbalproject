from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtWidgets import QFileDialog

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.source_controller import split_source
from app.ui.training_desk import TrainingDeskDialog
from app.workers import TrackerWorker
from uav_tracker.config import Config
from uav_tracker.profile_io import load_preset


class TrackerBridge(QObject):
    """QObject facade used by QML; owns TrackerWorker lifecycle."""

    isRunningChanged = Signal()
    isRecordingChanged = Signal()
    trackingStateChanged = Signal()
    targetLifecycleChanged = Signal()
    activeSourceChanged = Signal()
    currentModeChanged = Signal()
    currentSourceChanged = Signal()
    targetIdChanged = Signal()
    confidenceChanged = Signal()
    fpsChanged = Signal()
    latencyMsChanged = Signal()
    activeTargetsChanged = Signal()
    idSwitchesChanged = Signal()
    falseLockRiskChanged = Signal()
    lockScoreChanged = Signal()
    targetReliabilityChanged = Signal()
    targetPresentProbabilityChanged = Signal()
    activeBboxJsonChanged = Signal()
    displayTargetsJsonChanged = Signal()
    frameWidthChanged = Signal()
    frameHeightChanged = Signal()
    lastActionChanged = Signal()
    frameIdChanged = Signal()

    def __init__(
        self,
        frame_provider,
        parent: QObject | None = None,
        geo_bridge: QObject | None = None,
        settings_bridge: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._frame_provider = frame_provider
        self._geo_bridge = geo_bridge
        self._settings_bridge = settings_bridge
        self._worker: TrackerWorker | None = None
        self._dts_dialog: TrainingDeskDialog | None = None

        self._is_running = False
        self._is_recording = False
        self._tracking_state = "SEARCH"
        self._target_lifecycle = "SEARCH"
        self._active_source = "—"
        self._current_mode = "ДЕНЬ"
        self._current_source = ""
        self._target_id = 0
        self._confidence = 0.0
        self._fps = 0
        self._latency_ms = 0
        self._active_targets = 0
        self._id_switches = 0
        self._false_lock_risk = 0.0
        self._lock_score = 0.0
        self._target_reliability = 0.0
        self._target_present_probability = 0.0
        self._active_bbox_json = "[]"
        self._display_targets_json = "[]"
        self._frame_width = 0
        self._frame_height = 0
        self._last_action = "Система готова"
        self._frame_id = 0

    def _set(self, name: str, value: Any, signal: Signal) -> None:
        attr = f"_{name}"
        if getattr(self, attr) == value:
            return
        setattr(self, attr, value)
        signal.emit()

    @Property(bool, notify=isRunningChanged)
    def isRunning(self) -> bool:
        return self._is_running

    @Property(bool, notify=isRecordingChanged)
    def isRecording(self) -> bool:
        return self._is_recording

    @Property(str, notify=trackingStateChanged)
    def trackingState(self) -> str:
        return self._tracking_state

    @Property(str, notify=targetLifecycleChanged)
    def targetLifecycle(self) -> str:
        return self._target_lifecycle

    @Property(str, notify=activeSourceChanged)
    def activeSource(self) -> str:
        return self._active_source

    @Property(str, notify=currentModeChanged)
    def currentMode(self) -> str:
        return self._current_mode

    @Property(str, notify=currentSourceChanged)
    def currentSource(self) -> str:
        return self._current_source

    @Property(int, notify=targetIdChanged)
    def targetId(self) -> int:
        return self._target_id

    @Property(float, notify=confidenceChanged)
    def confidence(self) -> float:
        return self._confidence

    @Property(int, notify=fpsChanged)
    def fps(self) -> int:
        return self._fps

    @Property(int, notify=latencyMsChanged)
    def latencyMs(self) -> int:
        return self._latency_ms

    @Property(int, notify=activeTargetsChanged)
    def activeTargets(self) -> int:
        return self._active_targets

    @Property(int, notify=idSwitchesChanged)
    def idSwitches(self) -> int:
        return self._id_switches

    @Property(float, notify=falseLockRiskChanged)
    def falseLockRisk(self) -> float:
        return self._false_lock_risk

    @Property(float, notify=lockScoreChanged)
    def lockScore(self) -> float:
        return self._lock_score

    @Property(float, notify=targetReliabilityChanged)
    def targetReliability(self) -> float:
        return self._target_reliability

    @Property(float, notify=targetPresentProbabilityChanged)
    def targetPresentProbability(self) -> float:
        return self._target_present_probability

    @Property(str, notify=activeBboxJsonChanged)
    def activeBboxJson(self) -> str:
        return self._active_bbox_json

    @Property(str, notify=displayTargetsJsonChanged)
    def displayTargetsJson(self) -> str:
        return self._display_targets_json

    @Property(int, notify=frameWidthChanged)
    def frameWidth(self) -> int:
        return self._frame_width

    @Property(int, notify=frameHeightChanged)
    def frameHeight(self) -> int:
        return self._frame_height

    @Property(str, notify=lastActionChanged)
    def lastAction(self) -> str:
        return self._last_action

    @Property(int, notify=frameIdChanged)
    def frameId(self) -> int:
        return self._frame_id

    def _build_config(self) -> Config:
        preset = {
            "ДЕНЬ": "default",
            "НОЧЬ": "night",
            "ИК": "antiuav_thermal",
        }.get(self._current_mode, "default")
        try:
            cfg, _ = load_preset(preset)
        except Exception:
            cfg = Config()
        for attr, value in {
            "SHOW_GT_OVERLAY": False,
            "SHOW_DEBUG_TIMINGS": False,
            "SHOW_FOCUS_WINDOW": False,
            "SHOW_TRAILS": False,
            "OPERATOR_MINIMAL_OVERLAY": True,
            "RETICLE_OVERLAY_ENABLED": False,
        }.items():
            if hasattr(cfg, attr):
                setattr(cfg, attr, value)
        self._apply_tracker_settings(cfg)
        # QML is operator-first: click-to-select must always be active, and
        # accepted operator clicks are the intake path for DTS annotations.
        cfg.OPERATOR_OVERRIDE_ENABLED = True
        cfg.OPERATOR_OVERRIDE_INSTANT_LOCK = False
        cfg.OPERATOR_ANNOTATION_LOG_ENABLED = True
        cfg.OPERATOR_ANNOTATION_LOG_PATH = str(ROOT / "runs" / "operator_annotations" / "qml_operator_annotations.jsonl")
        cfg.FRAME_TELEMETRY_LOG_ENABLED = bool(int(self._setting("tracker_frame_telemetry_enabled", 1)))
        cfg.FRAME_TELEMETRY_LOG_PATH = str(ROOT / "runs" / "telemetry" / "frame_results.jsonl")
        cfg.validate()
        return cfg

    def _setting(self, key: str, default: Any) -> Any:
        if self._settings_bridge is None:
            return default
        getter = getattr(self._settings_bridge, "get", None)
        if getter is None:
            return default
        return getter(key, default)

    def _apply_tracker_settings(self, cfg: Config) -> None:
        numeric = {
            "CONF_THRESH": ("tracker_conf_thresh", float, 0.01, 0.99),
            "SMALL_TARGET_CONF": ("tracker_small_target_conf", float, 0.01, 0.99),
            "IMG_SIZE": ("tracker_img_size", int, 32, 4096),
            "SMALL_TARGET_IMG_SIZE": ("tracker_small_target_img_size", int, 32, 4096),
            "NIGHT_CONFIRM": ("tracker_night_confirm", int, 1, 60),
            "LOCK_CONFIRM_FRAMES": ("tracker_lock_confirm_frames", int, 1, 60),
            "TRACK_STATE_LOST_FRAMES": ("tracker_track_state_lost_frames", int, 1, 300),
            "YOLO_LOST_MAX": ("tracker_yolo_lost_max", int, 1, 300),
            "ROI_CONF_THRESH": ("tracker_roi_conf_thresh", float, 0.01, 0.99),
            "ROI_MAX_CANDIDATES": ("tracker_roi_max_candidates", int, 1, 20),
        }
        for attr, (key, typ, min_v, max_v) in numeric.items():
            try:
                value = typ(self._setting(key, getattr(cfg, attr)))
            except (TypeError, ValueError):
                continue
            if typ is int:
                value = int(max(min_v, min(max_v, value)))
                if attr in {"IMG_SIZE", "SMALL_TARGET_IMG_SIZE"}:
                    value = max(32, int(round(value / 32)) * 32)
            else:
                value = float(max(min_v, min(max_v, value)))
            setattr(cfg, attr, value)

        for attr, key in {
            "NIGHT_ENABLED": "tracker_night_enabled",
            "LOCK_TRACKER_ENABLED": "tracker_lock_tracker_enabled",
            "ROI_ASSIST_ENABLED": "tracker_roi_assist_enabled",
            "OPERATOR_ANNOTATION_LOG_ENABLED": "tracker_operator_annotation_enabled",
        }.items():
            setattr(cfg, attr, bool(int(self._setting(key, int(bool(getattr(cfg, attr)))))))

        if bool(getattr(cfg, "OPERATOR_ANNOTATION_LOG_ENABLED", False)):
            cfg.OPERATOR_ANNOTATION_LOG_PATH = str(ROOT / "runs" / "operator_annotations" / "qml_operator_annotations.jsonl")
        cfg.validate()

    def _resolve_source(self, source_type: str, source_value: str, camera_index: int) -> Any:
        normalized = source_type.strip().lower()
        if normalized in {"камера", "camera"}:
            return int(camera_index)
        if normalized in {"поток", "stream"}:
            return source_value.strip()
        if normalized in {"видео", "video"}:
            return source_value.strip()
        split_type, split_camera, split_path = split_source(source_value)
        if split_type == "camera":
            return split_camera
        return split_path

    @Slot(str, str, int)
    def startTracking(self, sourceType: str = "video", sourceValue: str = "", cameraIndex: int = 0) -> None:
        if self._worker is not None:
            self._set("last_action", "Трекинг уже запущен", self.lastActionChanged)
            return
        source = self._resolve_source(sourceType, sourceValue, cameraIndex)
        if source == "":
            self._set("last_action", "Источник не задан", self.lastActionChanged)
            return

        cfg = self._build_config()
        self._worker = TrackerWorker(
            cfg,
            source,
            output_path="",
            small_target_mode=True,
            render_overlays=False,
        )
        self._worker.frame_ready.connect(self._on_frame_ready)
        self._worker.stats_ready.connect(self._on_stats_ready)
        self._worker.log_ready.connect(self._on_log_ready)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._set("current_source", str(source), self.currentSourceChanged)
        self._set("is_running", True, self.isRunningChanged)
        self._set("tracking_state", "SEARCH", self.trackingStateChanged)
        self._set("target_lifecycle", "SEARCH", self.targetLifecycleChanged)
        self._set("last_action", f"Трекинг запущен: {source}", self.lastActionChanged)
        self._worker.start()

    @Slot()
    def stopTracking(self) -> None:
        if self._worker is None:
            self._reset_runtime_state("Трекинг остановлен")
            return
        self._worker.stop()
        self._set("last_action", "Остановка трекинга...", self.lastActionChanged)

    @Slot()
    def nextTarget(self) -> None:
        if self._worker is not None:
            self._worker.request_switch_target()
            self._set("last_action", "Запрошена следующая цель", self.lastActionChanged)

    @Slot()
    def confirmTarget(self) -> None:
        if self._worker is not None:
            self._worker.request_operator_confirm()
            self._set("last_action", "Подтверждение текущей цели", self.lastActionChanged)

    @Slot()
    def releaseTarget(self) -> None:
        if self._worker is not None:
            self._worker.request_operator_release()
            self._set("last_action", "Сброс текущей цели", self.lastActionChanged)

    @Slot()
    def toggleRecording(self) -> None:
        self._set("is_recording", not self._is_recording, self.isRecordingChanged)
        action = "Запись включена (QML MVP)" if self._is_recording else "Запись выключена"
        self._set("last_action", action, self.lastActionChanged)

    @Slot(result=str)
    def browseVideoFile(self) -> str:
        path, _ = QFileDialog.getOpenFileName(
            None,
            "Выбрать видео",
            str(ROOT / "test_videos"),
            "Video files (*.mp4 *.avi *.mov *.mkv);;All files (*)",
        )
        if path:
            self._set("last_action", f"Выбрано видео: {Path(path).name}", self.lastActionChanged)
        return path or ""

    @Slot()
    def markBBox(self) -> None:
        self._set("last_action", "BBox отмечен оператором", self.lastActionChanged)

    @Slot(int, int)
    def selectTargetAtFrame(self, frameX: int, frameY: int) -> None:
        if self._worker is None:
            self._set("last_action", "Сначала запустите источник", self.lastActionChanged)
            return
        x = max(0, min(int(self._frame_width or 0), int(frameX)))
        y = max(0, min(int(self._frame_height or 0), int(frameY)))
        self._worker.request_operator_target(x, y)
        self._set("last_action", f"ручное указание цели ({x},{y}) — поиск вокруг клика...", self.lastActionChanged)

    @Slot()
    def openDts(self) -> None:
        if self._dts_dialog is None:
            self._dts_dialog = TrainingDeskDialog(ROOT)
        self._dts_dialog.showMaximized()
        self._dts_dialog.raise_()
        self._dts_dialog.activateWindow()
        self._set("last_action", "DTS открыт", self.lastActionChanged)

    @Slot(str)
    def setMode(self, mode: str) -> None:
        self._set("current_mode", mode, self.currentModeChanged)
        self._set("last_action", f"Режим: {mode}", self.lastActionChanged)

    @Slot()
    def shutdown(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker.wait(3000)
            self._worker = None
        self._reset_runtime_state("Трекинг остановлен")

    def _on_frame_ready(self, frame: object) -> None:
        self._frame_provider.update_frame(frame)
        self._set("frame_id", self._frame_id + 1, self.frameIdChanged)

    def _on_stats_ready(self, stats: dict) -> None:
        if self._geo_bridge is not None:
            self._geo_bridge.updateFromStats(stats)
        mode = str(stats.get("mode", "SEARCH")).split(".")[-1]
        self._set("tracking_state", mode, self.trackingStateChanged)
        self._set("target_lifecycle", self._derive_target_lifecycle(stats, mode), self.targetLifecycleChanged)
        self._set("active_source", self._format_source(stats.get("active_source")), self.activeSourceChanged)
        self._set("fps", int(round(float(stats.get("fps", 0.0)))), self.fpsChanged)
        self._set("target_id", int(stats.get("active_id") or 0), self.targetIdChanged)
        self._set("active_targets", int(stats.get("visible_target_count", stats.get("target_count", 0)) or 0), self.activeTargetsChanged)
        self._set("id_switches", int(stats.get("active_id_changes", 0) or 0), self.idSwitchesChanged)
        self._set("confidence", float(stats.get("display_confidence", 0.0) or 0.0), self.confidenceChanged)
        self._set("lock_score", float(stats.get("lock_score", 0.0) or 0.0), self.lockScoreChanged)
        self._set("target_reliability", float(stats.get("target_reliability", 0.0) or 0.0), self.targetReliabilityChanged)
        self._set("target_present_probability", float(stats.get("target_p_present", 0.0) or 0.0), self.targetPresentProbabilityChanged)
        self._set("frame_width", int(stats.get("frame_width", 0) or 0), self.frameWidthChanged)
        self._set("frame_height", int(stats.get("frame_height", 0) or 0), self.frameHeightChanged)
        self._set("active_bbox_json", self._bbox_json(stats.get("active_bbox")), self.activeBboxJsonChanged)
        self._set("display_targets_json", self._targets_json(stats.get("display_targets")), self.displayTargetsJsonChanged)
        timings = stats.get("timings_ms") or {}
        latency = sum(float(v) for v in timings.values()) if isinstance(timings, dict) else 0.0
        self._set("latency_ms", int(round(latency)), self.latencyMsChanged)
        gt_iou = float(stats.get("gt_iou", 0.0) or 0.0)
        self._set("false_lock_risk", max(0.0, min(1.0, 1.0 - gt_iou)) if stats.get("gt_visible") else 0.0, self.falseLockRiskChanged)

    def _derive_target_lifecycle(self, stats: dict, mode: str) -> str:
        active_id = stats.get("active_id")
        active_bbox = stats.get("active_bbox")
        visible_count = int(stats.get("visible_target_count", stats.get("target_count", 0)) or 0)
        lock_score = float(stats.get("lock_score", 0.0) or 0.0)
        confidence = float(stats.get("display_confidence", 0.0) or 0.0)
        operator_status = str(stats.get("operator_override_status", "none") or "none")
        workflow_state = str(stats.get("operator_workflow_state", "") or "")
        tracking_action = str(stats.get("tracking_action", "") or "")

        if not self._is_running:
            return "OFFLINE"
        if workflow_state in {"SEARCH", "CANDIDATE", "VERIFYING", "TRACKING", "WEAK_TRACK", "LOST"}:
            return workflow_state
        if mode == "LOST":
            if active_id is not None or active_bbox is not None or tracking_action in {"hold", "reacquire", "local_validate"}:
                return "REACQUIRE"
            return "LOST"
        if operator_status == "applied":
            return "VERIFIED"
        if mode == "LOCK":
            return "LOCKED"
        if mode == "TRACK":
            return "TRACKING" if lock_score >= 0.35 else "ACQUIRE"
        if active_id is not None or active_bbox is not None:
            return "CANDIDATE" if confidence >= 0.35 else "DETECTED"
        if visible_count > 0:
            return "DETECTED"
        return "SEARCH"

    @staticmethod
    def _format_source(source: object) -> str:
        text = str(source or "").split(".")[-1].upper()
        return text if text and text != "NONE" else "—"

    @staticmethod
    def _bbox_json(bbox: object) -> str:
        if not bbox:
            return "[]"
        try:
            values = [int(v) for v in list(bbox)[:4]]
        except (TypeError, ValueError):
            return "[]"
        return json.dumps(values, separators=(",", ":"))

    @staticmethod
    def _targets_json(targets: object) -> str:
        if not isinstance(targets, list):
            return "[]"
        safe = []
        for item in targets[:3]:
            if not isinstance(item, dict):
                continue
            bbox = item.get("bbox")
            if not bbox:
                continue
            try:
                safe.append(
                    {
                        "id": int(item.get("id", 0) or 0),
                        "bbox": [int(v) for v in list(bbox)[:4]],
                        "conf": float(item.get("conf", 0.0) or 0.0),
                        "score": float(item.get("score", 0.0) or 0.0),
                        "source": str(item.get("source", "") or ""),
                        "active": bool(item.get("active", False)),
                    }
                )
            except (TypeError, ValueError):
                continue
        return json.dumps(safe, separators=(",", ":"))

    def _on_log_ready(self, message: str) -> None:
        self._set("last_action", message, self.lastActionChanged)

    def _on_worker_failed(self, message: str) -> None:
        self._worker = None
        self._reset_runtime_state(f"Ошибка: {message}")

    def _on_worker_finished(self, reason: str) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
        self._worker = None
        self._reset_runtime_state(f"Трекинг завершён: {reason}")

    def _reset_runtime_state(self, action: str) -> None:
        self._set("is_running", False, self.isRunningChanged)
        self._set("tracking_state", "SEARCH", self.trackingStateChanged)
        self._set("target_lifecycle", "OFFLINE", self.targetLifecycleChanged)
        self._set("active_source", "—", self.activeSourceChanged)
        self._set("fps", 0, self.fpsChanged)
        self._set("latency_ms", 0, self.latencyMsChanged)
        self._set("target_id", 0, self.targetIdChanged)
        self._set("confidence", 0.0, self.confidenceChanged)
        self._set("lock_score", 0.0, self.lockScoreChanged)
        self._set("target_reliability", 0.0, self.targetReliabilityChanged)
        self._set("target_present_probability", 0.0, self.targetPresentProbabilityChanged)
        self._set("active_bbox_json", "[]", self.activeBboxJsonChanged)
        self._set("display_targets_json", "[]", self.displayTargetsJsonChanged)
        self._set("frame_width", 0, self.frameWidthChanged)
        self._set("frame_height", 0, self.frameHeightChanged)
        self._set("active_targets", 0, self.activeTargetsChanged)
        self._set("id_switches", 0, self.idSwitchesChanged)
        self._set("false_lock_risk", 0.0, self.falseLockRiskChanged)
        self._set("last_action", action, self.lastActionChanged)
