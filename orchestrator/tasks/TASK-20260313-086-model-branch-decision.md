# Task: Model Branch Decision

## Task ID
- TASK-20260313-086

## Owner
- Claude Mac

## Priority
- P0

## Goal
- Convert the local baseline check and curriculum candidate re-intake evidence into one explicit branch decision for the current `drone-bird-yolo` curriculum branch.

## Files
- `automation/state/decision_log.json`
- `models/README.md`
- `python_scripts/install_baseline.py`
- `orchestrator/reports/`
- `orchestrator/state/project_state.md`

## Expected Result
- One explicit decision:
  - `promote`
  - `hold_and_tune`
  - `reject_and_reset_training_strategy`
- If a candidate is promotable, use the documented install-baseline flow and record the decision.
- If no candidate is promotable, record the non-promotion decision and the reasons.

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
- Decision must reference preset-specific local quality evidence.

## Constraints
- No new training cycle.
- No broader backlog reshaping.
- No unrelated runtime/UI changes.

## Status
- Open
