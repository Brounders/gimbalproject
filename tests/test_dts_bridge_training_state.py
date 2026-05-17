from __future__ import annotations

import json
import sys

from PySide6.QtCore import QCoreApplication

import app.qml_bridge.dts_bridge as dts_mod


def _app() -> QCoreApplication:
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
    return app


def _make_valid_job(tmp_path, *, run_name: str, created_at: str = "20260514_120000") -> dict:
    """Create a valid job.json + best.pt + pack manifest. Returns job dict."""
    pack_dir = tmp_path / "runs" / "operator_training_packs" / f"pack_{run_name}"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "manifest.json").write_text(json.dumps({"counts": {"ok": 2}}), encoding="utf-8")

    weights_dir = tmp_path / "runs" / "dts_candidate_training" / run_name / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)
    best_pt = weights_dir / "best.pt"
    best_pt.write_bytes(b"weights")

    job_dir = tmp_path / "runs" / "dts_candidate_jobs" / run_name
    job_dir.mkdir(parents=True, exist_ok=True)
    job = {
        "type": "dts_candidate_training",
        "created_at": created_at,
        "pack_dir": str(pack_dir),
        "run_name": run_name,
        "expected_best": str(best_pt),
        "project_dir": str(tmp_path / "runs" / "dts_candidate_training"),
    }
    (job_dir / "job.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
    return job


def test_dts_bridge_candidate_model_requires_best_pt(tmp_path, monkeypatch):
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    pack_dir = tmp_path / "runs" / "operator_training_packs" / "pack_a"
    pack_dir.mkdir(parents=True)
    (pack_dir / "manifest.json").write_text(json.dumps({"counts": {"ok": 1}}), encoding="utf-8")
    run_dir = tmp_path / "runs" / "dts_candidate_training" / "dts_pack_a_001" / "weights"
    run_dir.mkdir(parents=True)
    (run_dir / "last.pt").write_bytes(b"last")

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())

    assert bridge.candidateModelReady is False
    assert bridge._candidate_model_path() is None

    (run_dir / "best.pt").write_bytes(b"best")

    assert bridge.candidateModelReady is True
    assert bridge._candidate_model_path() == run_dir / "best.pt"


# ── _restore_candidate_context ─────────────────────────────────────────────


def test_restore_context_from_valid_job(tmp_path, monkeypatch):
    """Latest valid job.json restores run name, job dir, pack dir, expected best."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    job = _make_valid_job(tmp_path, run_name="dts_run_001")

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())

    assert bridge._last_candidate_name == "dts_run_001"
    assert "dts_run_001" in bridge._last_candidate_job_dir
    assert "pack_dts_run_001" in bridge._last_pack_dir
    assert bridge._training_expected_best != ""
    assert "best.pt" in bridge._training_expected_best


def test_restore_context_candidateModelReady_true(tmp_path, monkeypatch):
    """candidateModelReady is True after restore when best.pt exists."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    _make_valid_job(tmp_path, run_name="dts_run_002")

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())

    assert bridge.candidateModelReady is True


def test_restore_skips_job_without_best_pt(tmp_path, monkeypatch):
    """Job whose expected_best doesn't exist is not restored."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    pack_dir = tmp_path / "runs" / "operator_training_packs" / "pack_x"
    pack_dir.mkdir(parents=True)
    (pack_dir / "manifest.json").write_text("{}", encoding="utf-8")
    job_dir = tmp_path / "runs" / "dts_candidate_jobs" / "dts_no_best"
    job_dir.mkdir(parents=True)
    job = {
        "type": "dts_candidate_training",
        "created_at": "20260514_110000",
        "pack_dir": str(pack_dir),
        "run_name": "dts_no_best",
        "expected_best": str(tmp_path / "runs" / "dts_candidate_training" / "dts_no_best" / "weights" / "best.pt"),
    }
    (job_dir / "job.json").write_text(json.dumps(job), encoding="utf-8")

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())

    assert bridge._last_candidate_name == ""
    assert bridge.candidateModelReady is False


def test_restore_skips_job_without_manifest(tmp_path, monkeypatch):
    """Job whose pack_dir has no manifest.json is not restored."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    pack_dir = tmp_path / "runs" / "operator_training_packs" / "pack_nomanifest"
    pack_dir.mkdir(parents=True)
    # No manifest.json written
    weights_dir = tmp_path / "runs" / "dts_candidate_training" / "dts_nomanifest" / "weights"
    weights_dir.mkdir(parents=True)
    (weights_dir / "best.pt").write_bytes(b"w")
    job_dir = tmp_path / "runs" / "dts_candidate_jobs" / "dts_nomanifest"
    job_dir.mkdir(parents=True)
    job = {
        "type": "dts_candidate_training",
        "created_at": "20260514_110000",
        "pack_dir": str(pack_dir),
        "run_name": "dts_nomanifest",
        "expected_best": str(weights_dir / "best.pt"),
    }
    (job_dir / "job.json").write_text(json.dumps(job), encoding="utf-8")

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())

    assert bridge._last_candidate_name == ""


def test_restore_picks_newest_when_older_valid_exists(tmp_path, monkeypatch):
    """Newer invalid job does not hide older valid job — valid job is used."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    # Older valid job
    _make_valid_job(tmp_path, run_name="dts_old", created_at="20260514_090000")
    # Newer invalid job (best.pt missing)
    pack_dir2 = tmp_path / "runs" / "operator_training_packs" / "pack_new"
    pack_dir2.mkdir(parents=True)
    (pack_dir2 / "manifest.json").write_text("{}", encoding="utf-8")
    job_dir2 = tmp_path / "runs" / "dts_candidate_jobs" / "dts_new"
    job_dir2.mkdir(parents=True)
    invalid_job = {
        "type": "dts_candidate_training",
        "created_at": "20260514_130000",
        "pack_dir": str(pack_dir2),
        "run_name": "dts_new",
        "expected_best": str(tmp_path / "runs" / "dts_candidate_training" / "dts_new" / "weights" / "best.pt"),
    }
    (job_dir2 / "job.json").write_text(json.dumps(invalid_job), encoding="utf-8")

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())

    assert bridge._last_candidate_name == "dts_old"


def test_restore_picks_newest_valid_over_older_valid(tmp_path, monkeypatch):
    """When two valid jobs exist, the newer one wins."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    _make_valid_job(tmp_path, run_name="dts_older", created_at="20260514_090000")
    _make_valid_job(tmp_path, run_name="dts_newer", created_at="20260514_110000")

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())

    assert bridge._last_candidate_name == "dts_newer"
