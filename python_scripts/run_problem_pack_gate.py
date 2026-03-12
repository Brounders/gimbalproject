#!/usr/bin/env python3
"""Run the problem-pack mini-gate using configs/problem_pack_gate_contract.json."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "problem_pack_gate_contract.json"
SCRIPT = Path(__file__).parent / "run_quality_gate.py"


def main() -> int:
    if not CONTRACT.exists():
        print(f"[error] Contract not found: {CONTRACT}", file=sys.stderr)
        return 2
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    t = contract["thresholds"]
    threshold_args = [
        "--max-id-changes-per-min", str(t["max_id_changes_per_min"]),
        "--min-continuity", str(t["min_continuity"]),
        "--min-presence", str(t["min_presence"]),
        "--max-false-lock-rate", str(t["max_false_lock_rate"]),
        "--max-noise-false-lock-rate", str(t["max_noise_false_lock_rate"]),
        "--max-noise-id-changes-per-min", str(t["max_noise_id_changes_per_min"]),
    ]
    runs = [
        (contract["night_clips_preset"], ROOT / contract["night_pack_file"]),
        (contract["ir_clips_preset"],    ROOT / contract["ir_pack_file"]),
    ]
    results = []
    for preset, pack_path in runs:
        if not pack_path.exists():
            print(f"[error] Pack not found: {pack_path}", file=sys.stderr)
            return 2
        cmd = [sys.executable, str(SCRIPT),
               "--pack-file", str(pack_path),
               "--preset", preset] + threshold_args
        print(f"\n[problem-pack-gate] preset={preset}  pack={pack_path.name}")
        result = subprocess.run(cmd, cwd=ROOT)
        results.append(result.returncode)
    all_passed = all(r == 0 for r in results)
    status = "PASS" if all_passed else "FAIL"
    print(f"\n[problem-pack-gate] {status}  exit_codes={results}")
    return 0 if all_passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
