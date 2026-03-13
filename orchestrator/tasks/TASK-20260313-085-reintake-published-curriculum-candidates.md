# Task: Reintake Published Curriculum Candidates

## Task ID
- TASK-20260313-085

## Owner
- Claude Mac

## Priority
- P0

## Goal
- Re-evaluate already published `drone-bird-yolo` curriculum candidates under the current accepted runtime and local `day/night/ir` quality contract.

## Files
- `automation/state/artifact_manifest.json`
- `automation/state/training_ledger.json`
- `python_scripts/fetch_training_artifact.py`
- `python_scripts/run_quality_gate.py`
- `python_scripts/run_offline_benchmark.py`
- `runs/evaluations/`
- `orchestrator/reports/`

## Expected Result
- One evidence-based comparison report for:
  - `chunk10`
  - `chunk6`
  - `chunk8` only if needed to break a tie or resolve ambiguity
- The report must identify the best candidate or conclude that none are promotable.

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
- Use the existing local `day/night/ir` quality contract and report the exact artifacts used.

## Constraints
- No new training.
- No runtime or preset changes.
- Do not evaluate more artifacts than necessary.

## Status
- Open
