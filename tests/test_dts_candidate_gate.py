from __future__ import annotations

import json

import pytest

from app.dts_candidate_gate import (
    CandidateGateError,
    accept_candidate_model,
    promote_candidate_to_production,
    write_gate_decision,
)


def test_accept_candidate_requires_pass_decision_for_same_model(tmp_path):
    model_path = tmp_path / "weights" / "best.pt"
    model_path.parent.mkdir()
    model_path.write_bytes(b"candidate")
    result_dir = tmp_path / "compare"
    result_dir.mkdir()
    (result_dir / "summary.csv").write_text("model,context,passed\ncandidate,day,True\n", encoding="utf-8")

    write_gate_decision(
        result_dir,
        model_path,
        {
            "status": "PASS",
            "candidate_pass": 1,
            "candidate_total": 1,
            "baseline_pass": 1,
            "baseline_total": 1,
            "contexts": [{"name": "day", "passed": True}],
        },
    )

    manifest_path = accept_candidate_model(
        model_path,
        result_dir,
        output_root=tmp_path / "accepted",
        accepted_name="candidate_a",
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["decision"] == "ACCEPTED"
    assert manifest["gate_status"] == "PASS"
    assert (manifest_path.parent / "best.pt").read_bytes() == b"candidate"
    assert (manifest_path.parent / "summary.csv").exists()


def test_accept_candidate_rejects_retune_gate(tmp_path):
    model_path = tmp_path / "best.pt"
    model_path.write_bytes(b"candidate")
    result_dir = tmp_path / "compare"
    result_dir.mkdir()
    write_gate_decision(
        result_dir,
        model_path,
        {"status": "RETUNE", "candidate_pass": 1, "candidate_total": 2},
    )

    with pytest.raises(CandidateGateError, match="PASS"):
        accept_candidate_model(model_path, result_dir, output_root=tmp_path / "accepted")


def test_accept_candidate_rejects_decision_for_different_model(tmp_path):
    model_a = tmp_path / "a.pt"
    model_b = tmp_path / "b.pt"
    model_a.write_bytes(b"a")
    model_b.write_bytes(b"b")
    result_dir = tmp_path / "compare"
    result_dir.mkdir()
    write_gate_decision(
        result_dir,
        model_a,
        {"status": "PASS", "candidate_pass": 1, "candidate_total": 1},
    )

    with pytest.raises(CandidateGateError, match="другой модели"):
        accept_candidate_model(model_b, result_dir, output_root=tmp_path / "accepted")


def test_promote_candidate_rejects_smoke_gate_even_if_candidate_was_accepted(tmp_path):
    model_path = tmp_path / "weights" / "best.pt"
    model_path.parent.mkdir()
    model_path.write_bytes(b"candidate")
    result_dir = tmp_path / "compare_smoke"
    result_dir.mkdir()
    write_gate_decision(
        result_dir,
        model_path,
        {
            "status": "PASS",
            "scope": "smoke",
            "candidate_pass": 3,
            "candidate_total": 3,
            "contexts": [
                {"name": "day", "passed": True},
                {"name": "night", "passed": True},
                {"name": "ir", "passed": True},
            ],
        },
    )
    accepted_manifest = accept_candidate_model(
        model_path,
        result_dir,
        output_root=tmp_path / "accepted",
        accepted_name="candidate_a",
    )
    write_gate_decision(
        result_dir,
        accepted_manifest.parent / "best.pt",
        {
            "status": "PASS",
            "scope": "smoke",
            "candidate_pass": 3,
            "candidate_total": 3,
            "contexts": [
                {"name": "day", "passed": True},
                {"name": "night", "passed": True},
                {"name": "ir", "passed": True},
            ],
        },
    )

    with pytest.raises(CandidateGateError, match="full"):
        promote_candidate_to_production(
            accepted_manifest,
            result_dir,
            production_model_path=tmp_path / "models" / "baseline.pt",
        )


def test_promote_candidate_requires_full_gate_all_required_contexts(tmp_path):
    model_path = tmp_path / "weights" / "best.pt"
    model_path.parent.mkdir()
    model_path.write_bytes(b"candidate")
    smoke_dir = tmp_path / "compare_smoke"
    smoke_dir.mkdir()
    write_gate_decision(
        smoke_dir,
        model_path,
        {
            "status": "PASS",
            "scope": "smoke",
            "candidate_pass": 1,
            "candidate_total": 1,
            "contexts": [{"name": "day", "passed": True}],
        },
    )
    accepted_manifest = accept_candidate_model(
        model_path,
        smoke_dir,
        output_root=tmp_path / "accepted",
        accepted_name="candidate_a",
    )
    accepted_model = accepted_manifest.parent / "best.pt"
    full_dir = tmp_path / "compare_full"
    full_dir.mkdir()
    write_gate_decision(
        full_dir,
        accepted_model,
        {
            "status": "PASS",
            "scope": "full",
            "candidate_pass": 3,
            "candidate_total": 3,
            "contexts": [
                {"name": "day", "passed": True},
                {"name": "night", "passed": True},
                {"name": "ir", "passed": True},
            ],
        },
    )

    manifest_path = promote_candidate_to_production(
        accepted_manifest,
        full_dir,
        production_model_path=tmp_path / "models" / "baseline.pt",
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["decision"] == "PROMOTED_TO_PRODUCTION"
    assert manifest["gate_scope"] == "full"
    assert (tmp_path / "models" / "baseline.pt").read_bytes() == b"candidate"


def test_write_gate_decision_includes_baseline_model_hash(tmp_path):
    model = tmp_path / "candidate.pt"
    model.write_bytes(b"candidate")
    baseline = tmp_path / "baseline.pt"
    baseline.write_bytes(b"baselineweights")
    result_dir = tmp_path / "compare"
    path = write_gate_decision(
        result_dir, model,
        {"status": "PASS", "candidate_pass": 1, "candidate_total": 1},
        baseline_model_path=baseline,
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["baseline_model"].endswith("baseline.pt")
    assert len(data["baseline_model_sha256"]) == 64


def test_write_gate_decision_includes_regression_pack_hashes(tmp_path):
    model = tmp_path / "candidate.pt"
    model.write_bytes(b"candidate")
    pack_day = tmp_path / "regression_pack_day.csv"
    pack_day.write_text("source,scene\n", encoding="utf-8")
    result_dir = tmp_path / "compare"
    path = write_gate_decision(
        result_dir, model,
        {"status": "PASS", "candidate_pass": 1, "candidate_total": 1},
        regression_pack_paths={"day": pack_day},
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "day" in data["regression_pack_sha256"]
    assert len(data["regression_pack_sha256"]["day"]) == 64


def test_write_gate_decision_skips_missing_regression_pack(tmp_path):
    model = tmp_path / "candidate.pt"
    model.write_bytes(b"candidate")
    result_dir = tmp_path / "compare"
    path = write_gate_decision(
        result_dir, model,
        {"status": "PASS", "candidate_pass": 1, "candidate_total": 1},
        regression_pack_paths={"night": tmp_path / "nonexistent.csv"},
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("regression_pack_sha256", {}) == {}


def test_write_gate_decision_raises_if_baseline_model_missing(tmp_path):
    model = tmp_path / "candidate.pt"
    model.write_bytes(b"candidate")
    result_dir = tmp_path / "compare"
    with pytest.raises(CandidateGateError, match="baseline model"):
        write_gate_decision(
            result_dir, model,
            {"status": "PASS", "candidate_pass": 1, "candidate_total": 1},
            baseline_model_path=tmp_path / "nonexistent_baseline.pt",
        )


def test_accept_candidate_writes_gate_decision_sha256(tmp_path):
    model = tmp_path / "best.pt"
    model.write_bytes(b"candidate")
    result_dir = tmp_path / "compare"
    write_gate_decision(
        result_dir, model,
        {"status": "PASS", "candidate_pass": 1, "candidate_total": 1},
    )
    manifest_path = accept_candidate_model(
        model, result_dir,
        output_root=tmp_path / "accepted",
        accepted_name="acc_test",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest["gate_decision_sha256"]) == 64


def test_accept_candidate_copies_baseline_fields_from_decision(tmp_path):
    model = tmp_path / "best.pt"
    model.write_bytes(b"candidate")
    baseline = tmp_path / "baseline.pt"
    baseline.write_bytes(b"baselineweights")
    result_dir = tmp_path / "compare"
    write_gate_decision(
        result_dir, model,
        {"status": "PASS", "candidate_pass": 1, "candidate_total": 1},
        baseline_model_path=baseline,
    )
    manifest_path = accept_candidate_model(
        model, result_dir,
        output_root=tmp_path / "accepted",
        accepted_name="acc_bl",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["baseline_model"].endswith("baseline.pt")
    assert len(manifest["baseline_model_sha256"]) == 64


def test_accept_candidate_writes_training_job_dir_and_pack_dir(tmp_path):
    model = tmp_path / "best.pt"
    model.write_bytes(b"candidate")
    result_dir = tmp_path / "compare"
    write_gate_decision(
        result_dir, model,
        {"status": "PASS", "candidate_pass": 1, "candidate_total": 1},
    )
    manifest_path = accept_candidate_model(
        model, result_dir,
        output_root=tmp_path / "accepted",
        accepted_name="acc_dirs",
        training_job_dir=tmp_path / "jobs" / "job_001",
        pack_dir=tmp_path / "packs" / "pack_001",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "job_001" in manifest["training_job_dir"]
    assert "pack_001" in manifest["pack_dir"]


def test_promote_candidate_rejects_missing_required_context(tmp_path):
    model_path = tmp_path / "weights" / "best.pt"
    model_path.parent.mkdir()
    model_path.write_bytes(b"candidate")
    result_dir = tmp_path / "compare"
    result_dir.mkdir()
    write_gate_decision(
        result_dir,
        model_path,
        {
            "status": "PASS",
            "scope": "full",
            "candidate_pass": 2,
            "candidate_total": 2,
            "contexts": [
                {"name": "day", "passed": True},
                {"name": "night", "passed": True},
            ],
        },
    )
    accepted_manifest = accept_candidate_model(
        model_path,
        result_dir,
        output_root=tmp_path / "accepted",
        accepted_name="candidate_a",
    )
    write_gate_decision(
        result_dir,
        accepted_manifest.parent / "best.pt",
        {
            "status": "PASS",
            "scope": "full",
            "candidate_pass": 2,
            "candidate_total": 2,
            "contexts": [
                {"name": "day", "passed": True},
                {"name": "night", "passed": True},
            ],
        },
    )

    with pytest.raises(CandidateGateError, match="контексты"):
        promote_candidate_to_production(
            accepted_manifest,
            result_dir,
            production_model_path=tmp_path / "models" / "baseline.pt",
        )
