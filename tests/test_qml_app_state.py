"""Tests for the lightweight AppState QML facade."""
from __future__ import annotations

import pytest
import sys
import os

# PySide6 requires QApplication — use offscreen platform
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Property, Signal
from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from app.qml_bridge.app_state import AppState


# ---------------------------------------------------------------------------
# Stub bridges
# ---------------------------------------------------------------------------

class _TrackerStub(QObject):
    isRunningChanged = Signal()
    currentSourceChanged = Signal()

    def __init__(self, running: bool = False, source: str = "") -> None:
        super().__init__()
        self.isRunning = running
        self.currentSource = source


class _DtsStub(QObject):
    changed = Signal()

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.trainingRunning = kwargs.get("trainingRunning", False)
        self.compareRunning = kwargs.get("compareRunning", False)
        self.candidateModelReady = kwargs.get("candidateModelReady", False)
        self.compareDecisionReady = kwargs.get("compareDecisionReady", False)
        self.activeRunName = kwargs.get("activeRunName", "")


def _make(tracker_kw=None, dts_kw=None) -> AppState:
    t = _TrackerStub(**(tracker_kw or {}))
    d = _DtsStub(**(dts_kw or {}))
    return AppState(tracker_bridge=t, dts_bridge=d)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_construction_does_not_raise():
    _make()


def test_construction_with_missing_signals_does_not_raise():
    # bridges with no signals — hasattr guards must protect
    class _Bare:
        isRunning = False
        currentSource = ""
        trainingRunning = False
        compareRunning = False
        candidateModelReady = False
        compareDecisionReady = False
        activeRunName = ""

    AppState(tracker_bridge=_Bare(), dts_bridge=_Bare())


# ---------------------------------------------------------------------------
# appMode priority
# ---------------------------------------------------------------------------

def test_app_mode_idle_by_default():
    s = _make()
    assert s.appMode == "IDLE"


def test_app_mode_running():
    s = _make(tracker_kw={"running": True})
    assert s.appMode == "RUNNING"


def test_app_mode_training_overrides_running():
    s = _make(tracker_kw={"running": True}, dts_kw={"trainingRunning": True})
    assert s.appMode == "TRAINING"


def test_app_mode_comparing_highest_priority():
    s = _make(
        tracker_kw={"running": True},
        dts_kw={"trainingRunning": True, "compareRunning": True},
    )
    assert s.appMode == "COMPARING"


# ---------------------------------------------------------------------------
# canTrain
# ---------------------------------------------------------------------------

def test_can_train_idle():
    s = _make()
    assert s.canTrain is True


def test_can_train_blocked_when_training():
    s = _make(dts_kw={"trainingRunning": True})
    assert s.canTrain is False


def test_can_train_blocked_when_comparing():
    s = _make(dts_kw={"compareRunning": True})
    assert s.canTrain is False


# ---------------------------------------------------------------------------
# canCompare
# ---------------------------------------------------------------------------

def test_can_compare_false_without_candidate():
    s = _make()
    assert s.canCompare is False


def test_can_compare_true_when_candidate_ready():
    s = _make(dts_kw={"candidateModelReady": True})
    assert s.canCompare is True


def test_can_compare_blocked_when_training():
    s = _make(dts_kw={"candidateModelReady": True, "trainingRunning": True})
    assert s.canCompare is False


def test_can_compare_blocked_when_compare_running():
    s = _make(dts_kw={"candidateModelReady": True, "compareRunning": True})
    assert s.canCompare is False


# ---------------------------------------------------------------------------
# canAccept
# ---------------------------------------------------------------------------

def test_can_accept_false_without_decision():
    s = _make()
    assert s.canAccept is False


def test_can_accept_true_when_decision_ready():
    s = _make(dts_kw={"compareDecisionReady": True})
    assert s.canAccept is True


def test_can_accept_blocked_when_training():
    s = _make(dts_kw={"compareDecisionReady": True, "trainingRunning": True})
    assert s.canAccept is False


def test_can_accept_blocked_when_compare_running():
    s = _make(dts_kw={"compareDecisionReady": True, "compareRunning": True})
    assert s.canAccept is False


# ---------------------------------------------------------------------------
# context strings
# ---------------------------------------------------------------------------

def test_current_source_propagated():
    s = _make(tracker_kw={"source": "rtsp://cam"})
    assert s.currentSource == "rtsp://cam"


def test_active_run_name_propagated():
    s = _make(dts_kw={"activeRunName": "run_42"})
    assert s.activeRunName == "run_42"


def test_current_source_empty_when_none():
    s = _make(tracker_kw={"source": ""})
    assert s.currentSource == ""
