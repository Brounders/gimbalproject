# Task ID
- TASK-20260313-083

# Owner
- Claude Mac

# Priority
- P1

# Goal
- Produce a reproducible hard-gate evidence artifact for the large-target night fix, with an explicit verdict based on `night_ground_large_drones` and a no-regression check on `night_ground_indicator_lights`.

# Files
- `python_scripts/run_problem_pack_gate.py`
- `python_scripts/compare_kpi_snapshots.py`
- `configs/problem_pack_gate_contract.json`
- `RUNBOOK.md`
- `orchestrator/reports/REPORT-20260313-083.md`

# Expected Result
- One canonical before/after evidence loop exists for the large-target night case.
- The report states one explicit verdict:
  - improvement
  - no improvement
  - regression
- The hard gate is tied to real local commands and current accepted thresholds.

# Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
- Execute the problem-pack loop and include concrete before/after numbers in the report.

# Constraints
- Do not redesign the whole quality-gate system.
- No code changes outside the narrow evidence path for this cycle.

# Status
- Accepted
