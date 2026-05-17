"""Unit tests for DTS compare UX: human-readable result fields."""
from __future__ import annotations

import hashlib
import json
import sys
import time

from PySide6.QtCore import QCoreApplication

import app.qml_bridge.dts_bridge as dts_mod


def _app() -> QCoreApplication:
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
    return app


def _bridge(tmp_path, monkeypatch) -> dts_mod.DtsBridge:
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    return dts_mod.DtsBridge(dts_mod.DtsFrameProvider())


def _pass_data(n: int = 3) -> dict:
    return {
        "status": "PASS",
        "candidate_pass": n,
        "candidate_total": n,
        "baseline_pass": n,
        "baseline_total": n,
        "contexts": [{"name": c, "passed": True, "presence": 0.9, "delta_presence": 0.0, "false_lock": 0.1, "id_changes": 5.0} for c in ["day", "night", "ir"][:n]],
    }


def _fail_data(failed: list[str]) -> dict:
    all_ctxs = ["day", "night", "ir"]
    contexts = [{"name": c, "passed": c not in failed, "presence": 0.9, "delta_presence": 0.0, "false_lock": 0.1, "id_changes": 5.0} for c in all_ctxs]
    candidate_pass = sum(1 for c in contexts if c["passed"])
    return {
        "status": "FAIL" if candidate_pass == 0 else "RETUNE",
        "candidate_pass": candidate_pass,
        "candidate_total": len(all_ctxs),
        "baseline_pass": len(all_ctxs),
        "baseline_total": len(all_ctxs),
        "contexts": contexts,
    }


# --- _build_human_compare_fields tests ---

def test_pass_summary_gives_candidate_pass(tmp_path, monkeypatch):
    bridge = _bridge(tmp_path, monkeypatch)
    data = _pass_data(3)
    bridge._build_human_compare_fields(data, decision_ready=True, decision_missing=False)
    assert bridge.compareHumanTitle == "Candidate PASS"
    assert "3/3" in bridge.compareHumanSummary
    assert bridge.compareRejectReason == ""
    assert bridge.compareDecisionReady is True
    assert bridge.compareDecisionMissing is False


def test_fail_data_all_fail_gives_candidate_otklonen(tmp_path, monkeypatch):
    bridge = _bridge(tmp_path, monkeypatch)
    data = _fail_data(["day", "night", "ir"])
    bridge._build_human_compare_fields(data, decision_ready=True, decision_missing=False)
    assert bridge.compareHumanTitle == "Candidate отклонен"
    assert bridge.compareRejectReason != ""
    assert "FAIL" in bridge.compareRejectReason


def test_retune_data_gives_nuzna_dorabotka(tmp_path, monkeypatch):
    bridge = _bridge(tmp_path, monkeypatch)
    data = _fail_data(["night"])
    data["status"] = "RETUNE"
    bridge._build_human_compare_fields(data, decision_ready=True, decision_missing=False)
    assert bridge.compareHumanTitle == "Нужна доработка"
    assert "night" in bridge.compareRejectReason
    assert "FAIL" in bridge.compareRejectReason


def test_decision_missing_flag_overrides_status(tmp_path, monkeypatch):
    bridge = _bridge(tmp_path, monkeypatch)
    data = _pass_data(3)
    bridge._build_human_compare_fields(data, decision_ready=False, decision_missing=True)
    assert bridge.compareHumanTitle == "Результат неполный"
    assert bridge.compareDecisionMissing is True
    assert bridge.compareDecisionReady is False
    assert "gate decision" in bridge.compareRejectReason


def test_zero_candidate_total_gives_nepolunyy(tmp_path, monkeypatch):
    bridge = _bridge(tmp_path, monkeypatch)
    data = {"status": "FAIL", "candidate_pass": 0, "candidate_total": 0, "contexts": []}
    bridge._build_human_compare_fields(data, decision_ready=False, decision_missing=False)
    assert bridge.compareHumanTitle == "Результат неполный"
    assert "candidate строки" in bridge.compareRejectReason


# --- _load_latest_compare_summary decision check ---

def _make_summary_csv(result_dir, pass_ctx=True) -> None:
    result_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        "model,context,passed,active_presence_rate,false_lock_rate,active_id_changes_per_min",
        f"baseline,day,{'True' if pass_ctx else 'False'},0.90,0.10,5.0",
        f"candidate_model,day,{'True' if pass_ctx else 'False'},0.88,0.12,5.5",
    ]
    (result_dir / "summary.csv").write_text("\n".join(rows), encoding="utf-8")


def test_load_latest_decision_missing_sets_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    result_dir = tmp_path / "runs" / "dts_candidate_comparisons" / "dts_20260514_120000_abc"
    _make_summary_csv(result_dir, pass_ctx=True)
    # No candidate_gate_decision.json

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    assert bridge.compareDecisionMissing is True
    assert bridge.compareDecisionReady is False
    assert bridge.compareHumanTitle == "Результат неполный"


def test_load_latest_decision_present_sets_ready(tmp_path, monkeypatch):
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    result_dir = tmp_path / "runs" / "dts_candidate_comparisons" / "dts_20260514_120000_abc"
    _make_summary_csv(result_dir, pass_ctx=True)
    decision = {
        "schema_version": 1, "gate_status": "PASS", "candidate_pass": 1, "candidate_total": 1,
        "baseline_pass": 1, "baseline_total": 1, "contexts": [], "accept_allowed": True,
    }
    (result_dir / "candidate_gate_decision.json").write_text(json.dumps(decision), encoding="utf-8")

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    assert bridge.compareDecisionReady is True
    assert bridge.compareDecisionMissing is False


# --- _write_compare_diagnostics tests ---

def test_write_compare_diagnostics_creates_file_without_telemetry(tmp_path):
    """diagnostics.md is written even when telemetry_report.json is absent."""
    result_dir = tmp_path / "dts_20260514_result"
    result_dir.mkdir()
    decision = {
        "schema_version": 1, "gate_status": "PASS",
        "candidate_pass": 1, "candidate_total": 1,
        "accept_allowed": True, "contexts": [],
    }
    (result_dir / "candidate_gate_decision.json").write_text(json.dumps(decision), encoding="utf-8")

    dts_mod._write_compare_diagnostics(result_dir)

    assert (result_dir / "diagnostics.md").exists()


def test_write_compare_diagnostics_contains_telemetry_not_available(tmp_path):
    """diagnostics.md says 'Frame telemetry not available' when no telemetry JSON."""
    result_dir = tmp_path / "dts_result"
    result_dir.mkdir()
    decision = {"gate_status": "FAIL", "candidate_pass": 0, "candidate_total": 1,
                "accept_allowed": False, "contexts": []}
    (result_dir / "candidate_gate_decision.json").write_text(json.dumps(decision), encoding="utf-8")

    dts_mod._write_compare_diagnostics(result_dir)

    md = (result_dir / "diagnostics.md").read_text(encoding="utf-8")
    assert "Frame telemetry not available" in md


def test_write_compare_diagnostics_handles_broken_summary_csv(tmp_path):
    """Helper does not raise on corrupt summary.csv."""
    result_dir = tmp_path / "dts_result"
    result_dir.mkdir()
    (result_dir / "summary.csv").write_text("{not csv\x00", encoding="utf-8")
    # No gate decision either — should still produce a file without raising

    dts_mod._write_compare_diagnostics(result_dir)

    assert (result_dir / "diagnostics.md").exists()


def test_write_compare_diagnostics_with_telemetry_includes_operator_data(tmp_path):
    """When telemetry_report.json is present, operator data appears in diagnostics.md."""
    result_dir = tmp_path / "dts_result"
    result_dir.mkdir()
    decision = {"gate_status": "PASS", "candidate_pass": 1, "candidate_total": 1,
                "accept_allowed": True, "contexts": []}
    (result_dir / "candidate_gate_decision.json").write_text(json.dumps(decision), encoding="utf-8")
    telemetry = {
        "operator_hint_count": 4,
        "operator_applied_count": 3,
        "operator_confirmed_count": 2,
        "operator_rejected_count": 1,
        "operator_lost_count": 0,
        "dts_event_count": 6,
        "dts_operator_bbox_count": 4,
        "avg_click_to_lock_frames": 8.5,
        "median_click_to_lock_frames": 7.0,
        "max_click_to_lock_frames": 14.0,
        "latency_p95_ms": 22.0,
        "latency_p99_ms": 35.0,
    }
    (result_dir / "telemetry_report.json").write_text(json.dumps(telemetry), encoding="utf-8")

    dts_mod._write_compare_diagnostics(result_dir)

    md = (result_dir / "diagnostics.md").read_text(encoding="utf-8")
    assert "operator_hint_count" in md
    assert "dts_operator_bbox_count" in md
    assert "Frame telemetry not available" not in md


# --- reload debounce ---

def test_reload_debounce_skips_rapid_second_reload(tmp_path, monkeypatch):
    """A second reload() within 350ms is silently skipped."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    # write a new annotation file after the initial reload
    log_dir = tmp_path / "runs" / "operator_annotations"
    log_dir.mkdir(parents=True, exist_ok=True)
    row = {"frame_index": 1, "source": "/tmp/a.mp4", "bbox_xyxy": [1, 2, 3, 4], "event": "operator_bbox"}
    (log_dir / "extra.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    count_before = bridge.totalCount
    # Simulate that a reload just happened
    bridge._last_reload_time = time.monotonic()
    bridge.reload()  # should be debounced
    assert bridge.totalCount == count_before  # new file not picked up


def test_reload_debounce_allows_reload_after_window(tmp_path, monkeypatch):
    """A reload() after the debounce window always runs."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    log_dir = tmp_path / "runs" / "operator_annotations"
    log_dir.mkdir(parents=True, exist_ok=True)
    row = {"frame_index": 2, "source": "/tmp/b.mp4", "bbox_xyxy": [1, 2, 3, 4], "event": "operator_bbox"}
    (log_dir / "extra2.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    count_before = bridge.totalCount
    # Force last reload to be in the past (well outside the debounce window)
    bridge._last_reload_time = time.monotonic() - 1.0
    bridge.reload()
    assert bridge.totalCount > count_before  # new record picked up


# --- compare context cross-check ---

def _make_best_pt(tmp_path, run_name: str) -> object:
    """Create a best.pt and return its Path."""
    weights_dir = tmp_path / "runs" / "dts_candidate_training" / run_name / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)
    best_pt = weights_dir / "best.pt"
    best_pt.write_bytes(b"fake_model_weights")
    return best_pt


def _make_job_json(tmp_path, run_name: str, best_pt_path) -> None:
    job_dir = tmp_path / "runs" / "dts_candidate_jobs" / run_name
    job_dir.mkdir(parents=True, exist_ok=True)
    pack_dir = tmp_path / "runs" / "operator_training_packs" / f"pack_{run_name}"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "manifest.json").write_text(json.dumps({"counts": {"ok": 2}}), encoding="utf-8")
    job = {
        "type": "dts_candidate_training",
        "created_at": "20260514_120000",
        "pack_dir": str(pack_dir),
        "run_name": run_name,
        "expected_best": str(best_pt_path),
        "project_dir": str(tmp_path / "runs" / "dts_candidate_training"),
    }
    (job_dir / "job.json").write_text(json.dumps(job, indent=2), encoding="utf-8")


def test_load_latest_decision_hash_mismatch_sets_missing(tmp_path, monkeypatch):
    """If best.pt SHA256 doesn't match gate decision's candidate_model_sha256, compareDecisionReady=False."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    best_pt = _make_best_pt(tmp_path, "dts_mismatch")
    _make_job_json(tmp_path, "dts_mismatch", best_pt)

    result_dir = tmp_path / "runs" / "dts_candidate_comparisons" / "dts_20260514_mismatch"
    result_dir.mkdir(parents=True)
    rows = [
        "model,context,passed,active_presence_rate,false_lock_rate,active_id_changes_per_min",
        "candidate,day,True,0.90,0.10,5.0",
    ]
    (result_dir / "summary.csv").write_text("\n".join(rows), encoding="utf-8")
    decision = {
        "schema_version": 1, "gate_status": "PASS",
        "candidate_pass": 1, "candidate_total": 1,
        "baseline_pass": 1, "baseline_total": 1,
        "contexts": [], "accept_allowed": True,
        "candidate_model_sha256": "0000deadbeef",  # wrong hash
    }
    (result_dir / "candidate_gate_decision.json").write_text(json.dumps(decision), encoding="utf-8")

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    assert bridge.compareDecisionReady is False
    assert bridge.compareDecisionMissing is True


def test_load_latest_decision_matching_hash_sets_ready(tmp_path, monkeypatch):
    """If best.pt SHA256 matches gate decision, compareDecisionReady=True."""
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    best_pt = _make_best_pt(tmp_path, "dts_match")
    _make_job_json(tmp_path, "dts_match", best_pt)

    actual_sha = hashlib.sha256(best_pt.read_bytes()).hexdigest()

    result_dir = tmp_path / "runs" / "dts_candidate_comparisons" / "dts_20260514_match"
    result_dir.mkdir(parents=True)
    rows = [
        "model,context,passed,active_presence_rate,false_lock_rate,active_id_changes_per_min",
        "candidate,day,True,0.90,0.10,5.0",
    ]
    (result_dir / "summary.csv").write_text("\n".join(rows), encoding="utf-8")
    decision = {
        "schema_version": 1, "gate_status": "PASS",
        "candidate_pass": 1, "candidate_total": 1,
        "baseline_pass": 1, "baseline_total": 1,
        "contexts": [], "accept_allowed": True,
        "candidate_model_sha256": actual_sha,
    }
    (result_dir / "candidate_gate_decision.json").write_text(json.dumps(decision), encoding="utf-8")

    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    assert bridge.compareDecisionReady is True


# --- candidateStatusLabel ---

def test_candidate_status_label_no_data(tmp_path, monkeypatch):
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    assert bridge.candidateStatusLabel == "нет данных"


def test_candidate_status_label_compare_pass(tmp_path, monkeypatch):
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    bridge._compare_decision_ready = True
    bridge._compare_status = "PASS"
    assert bridge.candidateStatusLabel == "compare PASS"


def test_candidate_status_label_accepted(tmp_path, monkeypatch):
    _app()
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)
    bridge = dts_mod.DtsBridge(dts_mod.DtsFrameProvider())
    bridge._last_accepted_candidate_dir = "models/candidates/accepted/run_001"
    assert bridge.candidateStatusLabel == "candidate принят"
