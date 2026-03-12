# TASK: TASK-20260312-069-problem-pack-threshold-contract

Task ID: TASK-20260312-069
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Сделать из `regression_pack_problem.csv` не только A/B evidence loop, но и короткий threshold-based mini-gate для runtime hardening cycles.

## Scope
- In scope:
  - `configs/regression_pack_problem.csv`
  - `RUNBOOK.md`
  - `python_scripts/compare_kpi_snapshots.py`
  - `python_scripts/run_quick_kpi_smoke.py`
  - add one small threshold contract file and/or helper script if needed
- Out of scope:
  - full quality-gate redesign
  - training changes
  - UI changes

## Constraints
- Minimal reversible diff
- The result must be runnable locally and tied to explicit outputs
- Do not redesign the full benchmark stack
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `configs/regression_pack_problem.csv`
  - `RUNBOOK.md`
  - `python_scripts/compare_kpi_snapshots.py`
  - `python_scripts/run_quick_kpi_smoke.py`
- Context:
  - runtime hardening cycles now have a canonical problem-pack loop, but they still lack one explicit mini-gate contract for threshold-based acceptance

## Implementation Steps
1. Define a small explicit threshold contract for the canonical problem pack (`false_lock_rate`, `active_id_changes_per_min`, `continuity`, and any other justified metric).
2. Make the before/after comparison and threshold evaluation reproducible with concrete local commands and outputs.
3. Bind the contract into `RUNBOOK.md` so future runtime cycles use the same mini-gate.

## Acceptance Criteria
- [ ] the problem pack has an explicit mini-gate contract instead of documentation-only A/B comparison
- [ ] required inputs/outputs and threshold fields are reproducible locally
- [ ] future runtime cycles can say pass/fail on the problem pack without ad-hoc interpretation

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/compare_kpi_snapshots.py --help`
  - `rg -n "problem|threshold|A/B|night_ground_large_drones|night_ground_indicator_lights|IR_DRONE_001|Demo_IR_DRONE_146" RUNBOOK.md configs python_scripts`
- Expected result:
  - compile clean
  - the problem-pack mini-gate is discoverable, explicit, and runnable with local artifacts

## Risks
- Risk: this remains “another document” without an executable threshold flow
- Mitigation: require concrete local commands, explicit artifact fields, and one canonical threshold contract file or helper path
