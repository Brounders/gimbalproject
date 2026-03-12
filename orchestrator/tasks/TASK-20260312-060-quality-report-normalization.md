# TASK: TASK-20260312-060-quality-report-normalization

Task ID: TASK-20260312-060
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Привести benchmark/gate outputs к одному каноническому локальному формату, чтобы baseline vs candidate comparison был проще, а ручная сборка итогов сокращалась.

## Scope
- In scope:
  - `python_scripts/run_offline_benchmark.py`
  - `python_scripts/run_quality_gate.py`
  - `RUNBOOK.md`
  - local report/summary artifact docs or helpers if needed
- Out of scope:
  - changing tracking/runtime semantics
  - UI changes
  - new training cycle

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `python_scripts/run_offline_benchmark.py`
  - `python_scripts/run_quality_gate.py`
  - `RUNBOOK.md`
- Context:
  - aggregate output is better than before but still awkward to use as one canonical local decision artifact.

## Implementation Steps
1. Define one canonical local summary format for benchmark/gate outputs.
2. Align script outputs and docs around that format without breaking existing local workflows.
3. Make baseline vs candidate comparison easier to consume locally.

## Acceptance Criteria
- [ ] benchmark and quality-gate outputs converge on one understandable local summary contract
- [ ] local docs point to one canonical summary artifact
- [ ] baseline vs candidate comparison is easier without manual reconstruction

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_offline_benchmark.py --help`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quality_gate.py --help`
  - `rg -n "summary|quality-gate|benchmark|candidate|baseline" RUNBOOK.md python_scripts/run_offline_benchmark.py python_scripts/run_quality_gate.py`
- Expected result:
  - compile clean
  - both scripts remain callable
  - canonical summary contract is explicit

## Risks
- Risk: report normalization turns into a cosmetic rename rather than a practical usability fix
- Mitigation: normalize around actual local decision consumption, not just file naming
