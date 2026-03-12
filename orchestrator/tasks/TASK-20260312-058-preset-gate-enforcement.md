# TASK: TASK-20260312-058-preset-gate-enforcement

Task ID: TASK-20260312-058
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Сделать preset-specific gate обязательным и однозначным: `day`, `night`, `ir` должны оцениваться как отдельные quality contexts, а не прятаться внутри одного aggregate.

## Scope
- In scope:
  - `python_scripts/run_quality_gate.py`
  - `RUNBOOK.md`
  - `configs/regression_pack_day.csv`
  - `configs/regression_pack_night.csv`
  - `configs/regression_pack_ir.csv`
  - related local docs/config helpers if needed
- Out of scope:
  - new training cycle
  - runtime/tracking refactor
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
  - `python_scripts/run_quality_gate.py`
  - `RUNBOOK.md`
  - `configs/regression_pack_day.csv`
  - `configs/regression_pack_night.csv`
  - `configs/regression_pack_ir.csv`
- Context:
  - regression packs are already split by scenario;
  - the local decision flow still allows aggregate-only interpretation.

## Implementation Steps
1. Add or refine quality-gate handling so `day`, `night`, and `ir` can be enforced as explicit local quality contexts.
2. Ensure the contract is reflected in local docs and examples.
3. Keep aggregate output, but make preset-specific evidence first-class.

## Acceptance Criteria
- [ ] preset-specific gate contexts for `day`, `night`, and `ir` are explicit and usable
- [ ] local documentation shows how to run quality-gate per preset/scenario
- [ ] aggregate output no longer hides preset-specific results as the only decision path

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quality_gate.py --help`
  - `rg -n "regression_pack_(day|night|ir)|preset|quality-gate" RUNBOOK.md python_scripts/run_quality_gate.py configs`
- Expected result:
  - compile clean
  - quality-gate help remains callable
  - per-preset contract is explicit

## Risks
- Risk: implementation stays purely documentary and does not affect the real local decision flow
- Mitigation: bind the contract to actual `run_quality_gate.py` behavior and real regression pack files
