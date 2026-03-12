# TASK: TASK-20260312-066-problem-pack-ab-evidence

Task ID: TASK-20260312-066
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Сделать один канонический A/B evidence loop по проблемным клипам, чтобы before/after runtime hardening сравнивался на фиксированном коротком наборе сцен, а не вручную по разрозненным артефактам.

## Scope
- In scope:
  - `configs/regression_pack_problem.csv`
  - `RUNBOOK.md`
  - `python_scripts/run_quick_kpi_smoke.py`
  - `python_scripts/run_offline_benchmark.py`
  - `python_scripts/run_quality_gate.py` if a lightweight comparison path is needed
  - short evidence artifacts/docs/config updates
- Out of scope:
  - full benchmark redesign
  - training changes
  - UI changes

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `configs/regression_pack_problem.csv`
  - `RUNBOOK.md`
  - `python_scripts/run_quick_kpi_smoke.py`
  - `python_scripts/run_offline_benchmark.py`
  - `python_scripts/run_quality_gate.py`
- Context:
  - canonical problem clips are `night_ground_large_drones`, `night_ground_indicator_lights`, `IR_DRONE_001`, `Demo_IR_DRONE_146`;
  - runtime hardening needs one short before/after evidence loop that is fast enough to run every cycle.

## Implementation Steps
1. Define one canonical A/B loop for problem-clip runtime tuning using the existing local evaluation tools.
2. Make the required inputs/outputs explicit so before/after evidence is easy to compare.
3. Bind the loop into `RUNBOOK.md` so runtime hardening cycles always produce comparable evidence.

## Acceptance Criteria
- [ ] one canonical before/after evidence loop exists for the problem clips
- [ ] required outputs for comparison are explicit and reproducible
- [ ] runtime hardening no longer depends on ad-hoc manual evidence assembly

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --help`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quality_gate.py --help`
  - `rg -n "problem|A/B|night_ground_large_drones|night_ground_indicator_lights|IR_DRONE_001|Demo_IR_DRONE_146" RUNBOOK.md configs python_scripts`
- Expected result:
  - compile clean
  - the problem-pack evidence loop is discoverable, runnable, and tied to explicit outputs

## Risks
- Risk: the task degrades into documentation-only work without an actual repeatable comparison flow
- Mitigation: require explicit before/after outputs and bind them to real local commands
