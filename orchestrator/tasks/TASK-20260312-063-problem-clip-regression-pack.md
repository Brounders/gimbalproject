# TASK: TASK-20260312-063-problem-clip-regression-pack

Task ID: TASK-20260312-063
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Ввести короткий обязательный regression pack по самым проблемным operator-scene случаям, чтобы runtime hardening на `night` / `ir` проверялся не только общим aggregate.

## Scope
- In scope:
  - `configs/`
  - `RUNBOOK.md`
  - `python_scripts/run_quick_kpi_smoke.py` or adjacent local evaluation helpers if needed
  - short regression-pack docs/config artifacts
- Out of scope:
  - полный redesign benchmark system
  - замена existing day/night/ir packs
  - training changes

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `configs/regression_pack_night.csv`
  - `configs/regression_pack_ir.csv`
  - `RUNBOOK.md`
  - `python_scripts/run_quick_kpi_smoke.py`
- Context:
  - the known hard clips are `night_ground_large_drones`, `night_ground_indicator_lights`, `IR_DRONE_001`, and possibly `Demo_IR_DRONE_146`;
  - current aggregate packs hide whether runtime false-lock fixes actually help those scenes.

## Implementation Steps
1. Create one short canonical problem-clip pack for runtime-quality hardening.
2. Wire it into the local evaluation flow so it is easy to run before/after runtime tuning changes.
3. Document it as the required short-loop evidence for false-lock stability work.

## Acceptance Criteria
- [ ] there is one canonical short regression pack for the main problem clips
- [ ] the local evaluation flow documents how to run it
- [ ] runtime-hardening work can now be checked quickly on the exact difficult scenes

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --help`
  - `rg -n \"problem|night_ground_large_drones|night_ground_indicator_lights|IR_DRONE_001|Demo_IR_DRONE_146\" configs RUNBOOK.md python_scripts`
- Expected result:
  - compile clean
  - problem-clip pack is discoverable and wired into the local flow

## Risks
- Risk: this becomes just another CSV file without changing the actual team workflow
- Mitigation: bind it explicitly into `RUNBOOK.md` and the quick-smoke path
