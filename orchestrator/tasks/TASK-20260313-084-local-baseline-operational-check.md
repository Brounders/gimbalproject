# Task: Local Baseline Operational Check

## Task ID
- TASK-20260313-084

## Owner
- Claude Mac

## Priority
- P1

## Goal
- Verify whether the current Mac machine is in a valid local baseline state and whether the documented baseline install flow is operational.

## Files
- `models/`
- `models/README.md`
- `RUNBOOK.md`
- `python_scripts/install_baseline.py`
- `orchestrator/reports/`

## Expected Result
- One report that answers:
  - whether `models/baseline.pt` exists;
  - whether `models/baseline_manifest.json` exists;
  - whether the current documented install flow is sufficient and consistent with the machine state.
- Minimal doc/state alignment only if required by findings.

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
- `PYTHONPATH=src ./tracker_env/bin/python python_scripts/install_baseline.py --help`

## Constraints
- No baseline installation or replacement in this task.
- No runtime code changes.
- Analysis-first, with minimal doc/state alignment only if necessary.

## Status
- Accepted
