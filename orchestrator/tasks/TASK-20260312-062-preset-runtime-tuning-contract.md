# TASK: TASK-20260312-062-preset-runtime-tuning-contract

Task ID: TASK-20260312-062
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Сделать runtime tuning для `day`, `night`, `ir` явным и читаемым: закрепить, какие параметры реально различаются между preset-контекстами и исключить неочевидные/магические пересечения.

## Scope
- In scope:
  - `configs/default.yaml`
  - `configs/night.yaml`
  - `configs/antiuav_thermal.yaml`
  - `configs/small_target.yaml` if it participates in operator runtime behavior
  - `src/uav_tracker/config.py`
  - `RUNBOOK.md`
  - `OPERATOR_BASELINE.md`
- Out of scope:
  - новая UI configuration system
  - большой config redesign
  - training artifacts

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `configs/default.yaml`
  - `configs/night.yaml`
  - `configs/antiuav_thermal.yaml`
  - `src/uav_tracker/config.py`
  - `RUNBOOK.md`
  - `OPERATOR_BASELINE.md`
- Context:
  - local quality-gate is now split by `day` / `night` / `ir`;
  - runtime tuning still needs one explicit contract for which knobs differ between those contexts.

## Implementation Steps
1. Inventory runtime knobs that actually matter for `day`, `night`, and `ir`.
2. Make the preset-specific runtime contract explicit in config and docs without redesigning the whole config system.
3. Ensure the documented contract matches what the runtime really reads.

## Acceptance Criteria
- [ ] `day`, `night`, and `ir` runtime tuning differences are explicit and traceable
- [ ] config files and docs no longer disagree about the active runtime knobs
- [ ] no new hidden magic values or silent preset overlaps are introduced

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `rg -n \"conf_thresh|night_enabled|imgsz|lock|reacquire|verify|noise|ir\" configs src/uav_tracker/config.py RUNBOOK.md OPERATOR_BASELINE.md`
- Expected result:
  - compile clean
  - runtime tuning differences are explicit in both config and docs

## Risks
- Risk: task degrades into documentation only without aligning runtime behavior
- Mitigation: require a direct mapping between config fields, runtime readers, and docs
