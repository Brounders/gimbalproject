"""Lightweight AppState facade — read-only aggregate properties for QML guards.

Aggregates state from TrackerBridge and DtsBridge without duplicating business
logic.  QML button enabled states read from canTrain / canCompare / canAccept
instead of inlining bridge property combinations.
"""
from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal


class AppState(QObject):
    changed = Signal()

    def __init__(self, *, tracker_bridge: QObject, dts_bridge: QObject, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tracker = tracker_bridge
        self._dts = dts_bridge

        if hasattr(tracker_bridge, "isRunningChanged"):
            tracker_bridge.isRunningChanged.connect(self._on_changed)
        if hasattr(tracker_bridge, "currentSourceChanged"):
            tracker_bridge.currentSourceChanged.connect(self._on_changed)
        if hasattr(dts_bridge, "changed"):
            dts_bridge.changed.connect(self._on_changed)

    def _on_changed(self) -> None:
        self.changed.emit()

    # ── aggregate lifecycle ──────────────────────────────────────────────────

    @Property(str, notify=changed)
    def appMode(self) -> str:
        if getattr(self._dts, "compareRunning", False):
            return "COMPARING"
        if getattr(self._dts, "trainingRunning", False):
            return "TRAINING"
        if getattr(self._tracker, "isRunning", False):
            return "RUNNING"
        return "IDLE"

    # ── can* guards ──────────────────────────────────────────────────────────

    @Property(bool, notify=changed)
    def canChangeSource(self) -> bool:
        return True

    @Property(bool, notify=changed)
    def canOpenDts(self) -> bool:
        return True

    @Property(bool, notify=changed)
    def canTrain(self) -> bool:
        return (
            not getattr(self._dts, "trainingRunning", False)
            and not getattr(self._dts, "compareRunning", False)
        )

    @Property(bool, notify=changed)
    def canCompare(self) -> bool:
        return (
            bool(getattr(self._dts, "candidateModelReady", False))
            and not getattr(self._dts, "trainingRunning", False)
            and not getattr(self._dts, "compareRunning", False)
        )

    @Property(bool, notify=changed)
    def canAccept(self) -> bool:
        return (
            bool(getattr(self._dts, "compareDecisionReady", False))
            and not getattr(self._dts, "compareRunning", False)
            and not getattr(self._dts, "trainingRunning", False)
        )

    # ── context ──────────────────────────────────────────────────────────────

    @Property(str, notify=changed)
    def currentSource(self) -> str:
        return str(getattr(self._tracker, "currentSource", "") or "")

    @Property(str, notify=changed)
    def activeRunName(self) -> str:
        return str(getattr(self._dts, "activeRunName", "") or "")
