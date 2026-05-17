from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any


class CandidateGateError(RuntimeError):
    """Raised when a DTS candidate cannot be safely accepted."""


REQUIRED_PRODUCTION_CONTEXTS = frozenset({"day", "night", "ir"})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical(path: Path) -> str:
    return str(path.expanduser().resolve())


def write_gate_decision(
    result_dir: str | Path,
    model_path: str | Path,
    data: dict[str, Any],
    *,
    baseline_model_path: str | Path | None = None,
    regression_pack_paths: dict[str, str | Path] | None = None,
) -> Path:
    result_path = Path(result_dir)
    model = Path(model_path)
    if not model.exists():
        raise CandidateGateError(f"candidate model не найден: {model}")

    candidate_pass = int(data.get("candidate_pass", 0) or 0)
    candidate_total = int(data.get("candidate_total", 0) or 0)
    status = str(data.get("status", "FAIL") or "FAIL")
    allowed = status == "PASS" and candidate_total > 0 and candidate_pass == candidate_total
    decision = {
        "schema_version": 1,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_model": _canonical(model),
        "source_model_sha256": _sha256(model),
        "compare_result_dir": _canonical(result_path),
        "gate_status": status,
        "gate_scope": str(data.get("scope", "unknown") or "unknown"),
        "candidate_pass": candidate_pass,
        "candidate_total": candidate_total,
        "baseline_pass": int(data.get("baseline_pass", 0) or 0),
        "baseline_total": int(data.get("baseline_total", 0) or 0),
        "contexts": list(data.get("contexts", []) or []),
        "accept_allowed": bool(allowed),
    }
    if baseline_model_path is not None:
        bm = Path(baseline_model_path)
        if not bm.exists():
            raise CandidateGateError(f"baseline model не найден: {bm}")
        decision["baseline_model"] = _canonical(bm)
        decision["baseline_model_sha256"] = _sha256(bm)
    if regression_pack_paths:
        decision["regression_pack_sha256"] = {
            name: _sha256(Path(p)) for name, p in regression_pack_paths.items() if Path(p).exists()
        }
    result_path.mkdir(parents=True, exist_ok=True)
    path = result_path / "candidate_gate_decision.json"
    path.write_text(json.dumps(decision, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _load_gate_decision(result_dir: Path) -> dict[str, Any]:
    path = result_dir / "candidate_gate_decision.json"
    if not path.exists():
        raise CandidateGateError("candidate_gate_decision.json не найден: сначала запустите сравнение")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CandidateGateError(f"gate decision не читается: {exc}") from exc
    if not isinstance(data, dict):
        raise CandidateGateError("gate decision имеет неверный формат")
    return data


def _passed_contexts(data: dict[str, Any]) -> set[str]:
    contexts = data.get("contexts", []) or []
    passed: set[str] = set()
    if not isinstance(contexts, list):
        return passed
    for item in contexts:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "") or "").strip().lower()
        if name and bool(item.get("passed", False)):
            passed.add(name)
    return passed


def _assert_accept_allowed(model_path: Path, result_dir: Path) -> dict[str, Any]:
    if not model_path.exists():
        raise CandidateGateError(f"candidate best.pt не найден: {model_path}")
    if not result_dir.exists():
        raise CandidateGateError(f"compare result dir не найден: {result_dir}")

    data = _load_gate_decision(result_dir)
    if str(data.get("source_model", "")) != _canonical(model_path):
        raise CandidateGateError("gate decision относится к другой модели")
    if str(data.get("source_model_sha256", "")) != _sha256(model_path):
        raise CandidateGateError("candidate model изменился после сравнения")

    status = str(data.get("gate_status", "FAIL"))
    candidate_pass = int(data.get("candidate_pass", 0) or 0)
    candidate_total = int(data.get("candidate_total", 0) or 0)
    if status != "PASS" or candidate_total <= 0 or candidate_pass != candidate_total:
        raise CandidateGateError(
            f"candidate нельзя принять без PASS: status={status}, candidate={candidate_pass}/{candidate_total}"
        )
    if not bool(data.get("accept_allowed", False)):
        raise CandidateGateError("gate decision не разрешает принятие candidate")
    return data


def accept_candidate_model(
    model_path: str | Path,
    result_dir: str | Path,
    *,
    output_root: str | Path,
    accepted_name: str | None = None,
    training_job_dir: str | Path | None = None,
    pack_dir: str | Path | None = None,
) -> Path:
    model = Path(model_path)
    compare_dir = Path(result_dir)
    decision = _assert_accept_allowed(model, compare_dir)

    stem = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in model.stem).strip("._") or "candidate"
    name = accepted_name or f"accepted_{time.strftime('%Y%m%d_%H%M%S')}_{stem}"
    out_dir = Path(output_root) / name
    out_dir.mkdir(parents=True, exist_ok=False)

    accepted_model = out_dir / "best.pt"
    shutil.copy2(model, accepted_model)
    summary_csv = compare_dir / "summary.csv"
    if summary_csv.exists():
        shutil.copy2(summary_csv, out_dir / "summary.csv")
    decision_json = compare_dir / "candidate_gate_decision.json"
    if decision_json.exists():
        shutil.copy2(decision_json, out_dir / "candidate_gate_decision.json")

    decision_json = compare_dir / "candidate_gate_decision.json"
    gate_decision_sha256 = _sha256(decision_json) if decision_json.exists() else ""
    manifest = {
        "schema_version": 1,
        "decision": "ACCEPTED",
        "accepted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_model": _canonical(model),
        "accepted_model": _canonical(accepted_model),
        "accepted_model_sha256": _sha256(accepted_model),
        "compare_result_dir": _canonical(compare_dir),
        "gate_status": decision.get("gate_status"),
        "candidate_pass": decision.get("candidate_pass"),
        "candidate_total": decision.get("candidate_total"),
        "gate_decision_sha256": gate_decision_sha256,
    }
    if decision.get("baseline_model"):
        manifest["baseline_model"] = decision["baseline_model"]
    if decision.get("baseline_model_sha256"):
        manifest["baseline_model_sha256"] = decision["baseline_model_sha256"]
    if training_job_dir is not None:
        manifest["training_job_dir"] = str(training_job_dir)
    if pack_dir is not None:
        manifest["pack_dir"] = str(pack_dir)
    manifest_path = out_dir / "acceptance.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def promote_candidate_to_production(
    accepted_manifest_path: str | Path,
    result_dir: str | Path,
    *,
    production_model_path: str | Path,
    production_manifest_path: str | Path | None = None,
    required_contexts: set[str] | frozenset[str] = REQUIRED_PRODUCTION_CONTEXTS,
) -> Path:
    accepted_manifest = Path(accepted_manifest_path)
    compare_dir = Path(result_dir)
    if not accepted_manifest.exists():
        raise CandidateGateError(f"accepted candidate manifest не найден: {accepted_manifest}")
    try:
        accepted = json.loads(accepted_manifest.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CandidateGateError(f"accepted candidate manifest не читается: {exc}") from exc
    if not isinstance(accepted, dict) or accepted.get("decision") != "ACCEPTED":
        raise CandidateGateError("accepted candidate manifest не подтверждает ACCEPTED")

    accepted_model = Path(str(accepted.get("accepted_model", "")))
    if not accepted_model.exists():
        raise CandidateGateError(f"accepted model не найден: {accepted_model}")
    if str(accepted.get("accepted_model_sha256", "")) != _sha256(accepted_model):
        raise CandidateGateError("accepted model изменился после принятия")

    gate = _assert_accept_allowed(accepted_model, compare_dir)
    if str(gate.get("gate_scope", "unknown")) != "full":
        raise CandidateGateError("production promotion требует full gate")

    required = {str(item).strip().lower() for item in required_contexts}
    passed = _passed_contexts(gate)
    missing = sorted(required - passed)
    if missing:
        raise CandidateGateError(f"production promotion требует PASS контексты: {', '.join(missing)}")

    target_model = Path(production_model_path)
    target_manifest = (
        Path(production_manifest_path)
        if production_manifest_path is not None
        else target_model.with_name(f"{target_model.stem}_manifest.json")
    )
    target_model.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(accepted_model, target_model)

    manifest = {
        "schema_version": 1,
        "decision": "PROMOTED_TO_PRODUCTION",
        "promoted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_acceptance_manifest": _canonical(accepted_manifest),
        "source_model": _canonical(accepted_model),
        "production_model": _canonical(target_model),
        "production_model_sha256": _sha256(target_model),
        "compare_result_dir": _canonical(compare_dir),
        "gate_status": gate.get("gate_status"),
        "gate_scope": gate.get("gate_scope"),
        "required_contexts": sorted(required),
        "passed_contexts": sorted(passed),
    }
    target_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return target_manifest
