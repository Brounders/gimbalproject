# TASK: TASK-20260312-072-problem-pack-mini-gate-enforcement

Task ID: TASK-20260312-072
Owner: Claude Mac
Priority: P2
Status: Open

## Goal
Закрепить problem-pack mini-gate как обязательный короткий барьер для future runtime cycles, чтобы улучшения по noise/night сценам проверялись по воспроизводимому before/after contract, а не вручную.

## Scope
- In scope:
  - `configs/problem_pack_gate_contract.json`
  - `configs/regression_pack_problem.csv`
  - `python_scripts/run_quality_gate.py`
  - `python_scripts/compare_kpi_snapshots.py`
  - `RUNBOOK.md`
- Out of scope:
  - training changes
  - UI changes
  - replacing the main quality-gate flow

## Constraints
- Minimal reversible diff
- Keep the main local quality flow intact
- Do not redesign the full benchmark system
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `configs/problem_pack_gate_contract.json`
  - `configs/regression_pack_problem.csv`
  - `python_scripts/run_quality_gate.py`
  - `python_scripts/compare_kpi_snapshots.py`
  - `RUNBOOK.md`
- Context:
  - the project already has a problem-pack loop, but the next runtime cycles need it to act as a short mandatory mini-gate with explicit thresholds and reproducible outputs.

## Implementation Steps
1. Tighten the problem-pack gate contract so its thresholds and pass/fail meaning are explicit and reusable.
2. Ensure the existing scripts can produce the short evidence needed for before/after runtime comparisons.
3. Update the runbook so the mini-gate is a mandatory short loop for future night/noise runtime work.

## Acceptance Criteria
- [ ] the problem-pack mini-gate has one explicit threshold contract for future runtime cycles
- [ ] the before/after comparison loop is reproducible with existing local scripts
- [ ] the runbook describes the mini-gate as an operational short barrier, not just an optional report

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/compare_kpi_snapshots.py --help`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quality_gate.py --help`
- Expected result:
  - compile clean
  - existing tests still pass
  - one short reproducible problem-pack gate path is documented and supported by the local scripts

## Risks
- Risk: the mini-gate stays purely documentary and does not influence real runtime loops
- Mitigation: tie the contract to actual local scripts and the canonical runbook flow
