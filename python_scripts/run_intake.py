#!/usr/bin/env python3
"""
MG-001 — Model intake orchestrator.

Reads thresholds from configs/promotion_contract.yaml, runs run_quality_gate.py
for each requested context, collects JSON results, and emits:
  - Console verdict  (ACCEPTED / HOLD / REJECTED)
  - orchestrator/reports/REPORT-INTAKE-<model_stem>.md

Usage:
    python python_scripts/run_intake.py path/to/model.pt
    python python_scripts/run_intake.py path/to/model.pt --contexts night day
    python python_scripts/run_intake.py path/to/model.pt --contexts night --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("[error] PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]

# ── constants ────────────────────────────────────────────────────────────────

CONTRACT_PATH = ROOT / "configs" / "promotion_contract.yaml"
REPORTS_DIR   = ROOT / "orchestrator" / "reports"
GATE_OUT_DIR  = ROOT / "runs" / "evaluations" / "quality_gate"
GATE_SCRIPT   = ROOT / "python_scripts" / "run_quality_gate.py"

BASELINE_JSONS: dict[str, Path] = {
    "night": GATE_OUT_DIR / "quality_gate_night.json",
    "day":   GATE_OUT_DIR / "quality_gate_default.json",
    "ir":    GATE_OUT_DIR / "quality_gate_antiuav_thermal.json",
}

# Flags passed to run_quality_gate.py, keyed by context.
# Values come from promotion_contract.yaml at runtime.
_CONTEXT_GATE_FLAGS: dict[str, dict[str, str]] = {
    "night": {
        "--context":                       "night",
        "--max-false-lock-rate":           "{night_false_lock}",
        "--max-night-id-changes-per-min":  "{night_id_chg}",
    },
    "day": {
        "--context":                       "day",
        "--max-false-lock-rate":           "{day_false_lock}",
    },
    "ir": {
        "--context":                       "ir",
        "--max-false-lock-rate":           "{ir_false_lock}",
    },
}

ALL_CONTEXTS = ("night", "day", "ir")


# ── helpers ──────────────────────────────────────────────────────────────────

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_contract(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _thresholds_from_contract(contract: dict[str, Any]) -> dict[str, Any]:
    t = contract.get("thresholds", {})
    return {
        "night_false_lock": str(t.get("night", {}).get("false_lock_rate", {}).get("max", 0.55)),
        "night_id_chg":     str(t.get("night", {}).get("id_chg_per_min",  {}).get("max", 18.0)),
        "day_false_lock":   str(t.get("day",   {}).get("false_lock_rate", {}).get("max", 0.10)),
        "ir_false_lock":    str(t.get("ir",    {}).get("false_lock_rate", {}).get("max", 0.70)),
    }


def _known_gap_contexts(contract: dict[str, Any]) -> set[str]:
    """Contexts covered by acknowledged known_gaps."""
    gaps = contract.get("known_gaps", [])
    result: set[str] = set()
    for gap in gaps:
        for ctx in gap.get("affected_contexts", []):
            result.add(ctx)
    return result


def _build_gate_cmd(context: str, model_path: str, thresholds: dict[str, str],
                    baseline: Path | None) -> list[str]:
    flags = _CONTEXT_GATE_FLAGS[context]
    cmd = [sys.executable, str(GATE_SCRIPT)]
    for flag, val_template in flags.items():
        cmd += [flag, val_template.format(**thresholds)]
    cmd += ["--model", model_path]
    if baseline and baseline.exists():
        cmd += ["--baseline", str(baseline)]
    return cmd


def _run_gate(context: str, cmd: list[str], dry_run: bool) -> dict[str, Any]:
    """Run one gate subprocess, return parsed JSON summary or error dict."""
    print(f"\n[intake] ── context={context} ──")
    print(f"[intake] cmd: {' '.join(cmd)}")

    if dry_run:
        print("[intake] DRY-RUN: skipping execution")
        return {"gate_passed": None, "mean": {}, "failures": [], "_dry_run": True}

    result = subprocess.run(cmd, capture_output=False, cwd=str(ROOT))
    exit_code = result.returncode

    # Locate output JSON written by run_quality_gate.py
    ctx_to_preset = {"night": "night", "day": "default", "ir": "antiuav_thermal"}
    preset = ctx_to_preset.get(context, context)
    out_json = GATE_OUT_DIR / f"quality_gate_{preset}.json"

    if not out_json.exists():
        return {
            "gate_passed": False,
            "mean": {},
            "failures": [f"output JSON not found: {out_json}"],
            "_exit_code": exit_code,
        }

    try:
        data = json.loads(out_json.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "gate_passed": False,
            "mean": {},
            "failures": [f"JSON parse error: {exc}"],
            "_exit_code": exit_code,
        }

    data["_exit_code"] = exit_code
    return data


# ── verdict logic ────────────────────────────────────────────────────────────

def _compute_verdict(
    results: dict[str, dict[str, Any]],
    requested: list[str],
    gap_contexts: set[str],
) -> tuple[str, list[str]]:
    """
    Returns (verdict, notes):
      ACCEPTED  — all requested contexts PASS
      HOLD      — some FAIL but covered by known_gaps
      REJECTED  — at least one FAIL not covered by known_gaps
    """
    notes: list[str] = []
    failed_non_gap: list[str] = []
    failed_gap: list[str] = []

    for ctx in requested:
        r = results.get(ctx, {})
        if r.get("_dry_run"):
            notes.append(f"{ctx}: dry-run (не выполнялся)")
            continue
        passed = r.get("gate_passed", False)
        if not passed:
            if ctx in gap_contexts:
                failed_gap.append(ctx)
                notes.append(f"{ctx}: FAIL — покрыт known_gap (HOLD)")
            else:
                failed_non_gap.append(ctx)
                notes.append(f"{ctx}: FAIL — не покрыт known_gap → REJECTED")
        else:
            notes.append(f"{ctx}: PASS")

    if failed_non_gap:
        return "REJECTED", notes
    if failed_gap:
        return "HOLD", notes
    return "ACCEPTED", notes


# ── markdown report ──────────────────────────────────────────────────────────

def _write_report(
    model_path: Path,
    sha: str,
    contexts: list[str],
    results: dict[str, dict[str, Any]],
    verdict: str,
    notes: list[str],
    contract: dict[str, Any],
) -> Path:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stem = model_path.stem
    report_path = REPORTS_DIR / f"REPORT-INTAKE-{stem}.md"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    thresholds = contract.get("thresholds", {})
    gap_ids = [g.get("id", "?") for g in contract.get("known_gaps", [])]

    lines: list[str] = [
        f"# REPORT-INTAKE: {stem}",
        "",
        f"**Date:** {now}",
        f"**Verdict:** {verdict}",
        f"**Model:** `{model_path}`",
        f"**SHA256:** `{sha}`",
        f"**Contexts run:** {', '.join(contexts)}",
        "",
        "---",
        "",
        "## Gate Results",
        "",
        "| Context | Passed | false_lock | id_chg/min | Failures |",
        "|---------|--------|------------|------------|----------|",
    ]

    for ctx in contexts:
        r = results.get(ctx, {})
        if r.get("_dry_run"):
            lines.append(f"| {ctx} | DRY-RUN | — | — | — |")
            continue
        passed = "✅ PASS" if r.get("gate_passed") else "❌ FAIL"
        mean = r.get("mean", {})
        fl = f"{mean.get('false_lock_rate', '?'):.3f}" if isinstance(mean.get('false_lock_rate'), float) else "?"
        ic = f"{mean.get('active_id_changes_per_min', '?'):.2f}" if isinstance(mean.get('active_id_changes_per_min'), float) else "?"
        fails = "; ".join(r.get("failures", [])) or "—"
        lines.append(f"| {ctx} | {passed} | {fl} | {ic} | {fails} |")

    lines += [
        "",
        "## Thresholds (from promotion_contract.yaml)",
        "",
        "| Context | false_lock max | id_chg/min max |",
        "|---------|---------------|----------------|",
    ]
    for ctx in ("night", "day", "ir"):
        t = thresholds.get(ctx, {})
        fl_max = t.get("false_lock_rate", {}).get("max", "—")
        ic_max = t.get("id_chg_per_min",  {}).get("max", "—")
        status = " *(provisional)*" if t.get("status") == "provisional" else ""
        lines.append(f"| {ctx}{status} | {fl_max} | {ic_max} |")

    lines += [
        "",
        "## Verdict Notes",
        "",
    ]
    for note in notes:
        lines.append(f"- {note}")

    lines += [
        "",
        "## Known Gaps",
        "",
        f"Active gap IDs: {', '.join(gap_ids) if gap_ids else 'none'}",
        "",
        "---",
        "",
        f"*Generated by `python_scripts/run_intake.py`*",
    ]

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


# ── main ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MG-001 Model intake orchestrator.")
    p.add_argument("model", type=Path, help="Path to .pt model file")
    p.add_argument(
        "--contexts", nargs="+", choices=list(ALL_CONTEXTS),
        default=None,
        help="Contexts to run (default: night day — IR skipped unless explicitly requested)",
    )
    p.add_argument(
        "--all-contexts", action="store_true",
        help="Run all three contexts: night, day, ir",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Print gate commands without executing them",
    )
    p.add_argument(
        "--contract", type=Path, default=CONTRACT_PATH,
        help="Path to promotion_contract.yaml",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    model_path = args.model.resolve()
    if not model_path.exists():
        print(f"[error] Model not found: {model_path}")
        return 1

    if not args.contract.exists():
        print(f"[error] Contract not found: {args.contract}")
        return 1

    contract = _load_contract(args.contract)
    thresholds = _thresholds_from_contract(contract)
    gap_contexts = _known_gap_contexts(contract)

    # Determine which contexts to run
    if args.all_contexts:
        contexts = list(ALL_CONTEXTS)
    elif args.contexts:
        contexts = args.contexts
    else:
        contexts = ["night", "day"]  # IR skipped by default (provisional threshold)

    print(f"[intake] Model:    {model_path}")
    sha = _sha256(model_path)
    print(f"[intake] SHA256:   {sha}")
    print(f"[intake] Contexts: {contexts}")
    print(f"[intake] Contract: {args.contract}")
    if gap_contexts:
        print(f"[intake] Known gaps cover: {sorted(gap_contexts)}")

    results: dict[str, dict[str, Any]] = {}
    for ctx in contexts:
        baseline = BASELINE_JSONS.get(ctx)
        cmd = _build_gate_cmd(ctx, str(model_path), thresholds, baseline)
        results[ctx] = _run_gate(ctx, cmd, dry_run=args.dry_run)

    verdict, notes = _compute_verdict(results, contexts, gap_contexts)

    report_path = _write_report(
        model_path, sha, contexts, results, verdict, notes, contract
    )

    print(f"\n{'='*60}")
    print(f"  VERDICT: {verdict}")
    print(f"{'='*60}")
    for note in notes:
        print(f"  {note}")
    print(f"\n[intake] Report: {report_path}")

    return 0 if verdict in ("ACCEPTED", "HOLD") else 4


if __name__ == "__main__":
    sys.exit(main())
