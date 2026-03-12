# TASK: TASK-20260312-059-baseline-candidate-decision-hardening

Task ID: TASK-20260312-059
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Сделать локальное решение `promote / hold_and_tune / reject` более жестким и менее зависимым от ручной трактовки за счет явного decision flow, привязанного к preset-specific quality evidence.

## Scope
- In scope:
  - `RUNBOOK.md`
  - `models/README.md`
  - `python_scripts/install_baseline.py`
  - local decision docs/artifacts if needed
- Out of scope:
  - model promotion itself
  - new training cycle
  - UI/runtime refactor

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `RUNBOOK.md`
  - `models/README.md`
  - `python_scripts/install_baseline.py`
- Context:
  - baseline governance exists, but local promotion decisions are still too manual;
  - accepted model install flow already exists and must remain the canonical path.

## Implementation Steps
1. Define an explicit local decision flow from candidate evidence to `promote / hold_and_tune / reject`.
2. Tie decision flow to preset-specific evidence rather than aggregate-only judgment.
3. Ensure the accepted-model install path stays traceable and canonical.

## Acceptance Criteria
- [ ] local decision flow from candidate to baseline is explicit and unambiguous
- [ ] `promote / hold_and_tune / reject` is tied to preset-specific evidence
- [ ] baseline install remains canonical through `install_baseline.py`

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/install_baseline.py --help`
  - `rg -n "promote|hold_and_tune|reject|baseline|candidate" RUNBOOK.md models/README.md python_scripts/install_baseline.py`
- Expected result:
  - compile clean
  - install_baseline help callable
  - decision flow documented consistently

## Risks
- Risk: decision rules become too vague and remain human-interpretation-heavy
- Mitigation: anchor decision flow to concrete artifacts, paths, and preset-specific evidence
