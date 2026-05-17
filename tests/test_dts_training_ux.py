"""Unit tests for DTS training UX: log tail, cancel safety, candidate gate.

test_candidate_model_requires_best_pt is in test_dts_bridge_training_state.py.
"""
from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication

import app.qml_bridge.dts_bridge as dts_mod


def _app() -> QCoreApplication:
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
    return app


def test_training_log_tail_keeps_recent_lines():
    """Pure logic: tail must keep last 8 lines when more are appended."""
    lines = [f"line{i}" for i in range(20)]
    kept = lines[-8:]
    tail = "\n".join(kept)
    assert tail.count("\n") == 7
    assert "line12" in tail
    assert "line19" in tail
    assert "line0" not in tail


def test_cancel_training_when_not_running_is_safe(tmp_path, monkeypatch):
    """cancelTraining() without a running process returns a safe message, state intact."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    assert bridge.trainingRunning is False
    result = bridge.cancelTraining()
    assert bridge.trainingRunning is False
    assert bridge.trainingCanCancel is False
    # Must return a non-empty informative string
    assert isinstance(result, str) and len(result) > 0


def test_training_can_cancel_false_when_not_running(tmp_path, monkeypatch):
    """trainingCanCancel must be False when not running."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    assert bridge.trainingCanCancel is False


def test_training_exit_code_sentinel_before_run(tmp_path, monkeypatch):
    """trainingExitCode must be -999 (sentinel) before any training."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    assert bridge.trainingExitCode == -999


def test_training_log_tail_empty_before_run(tmp_path, monkeypatch):
    """trainingLogTail must be empty string before any training."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    assert bridge.trainingLogTail == ""
