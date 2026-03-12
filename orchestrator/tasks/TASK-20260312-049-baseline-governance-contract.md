# TASK: TASK-20260312-049-baseline-governance-contract

Task ID: TASK-20260312-049
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Зафиксировать локальный baseline governance contract: что такое `baseline`, `candidate`, `hold_and_tune`, `reject`, где живут эти сущности локально и какие артефакты являются источником истины.

## Scope
- In scope:
  - `RUNBOOK.md`
  - `OPERATOR_BASELINE.md`
  - `PROJECT_ARCHITECTURE.md`
  - при необходимости `models/README.md` или аналогичный локальный contract file
- Out of scope:
  - новый training cycle
  - promotion новой candidate-модели
  - web/RTX/automation redesign

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
  - `OPERATOR_BASELINE.md`
  - `PROJECT_ARCHITECTURE.md`
  - `configs/*.yaml`
- Context:
  - baseline path уже зафиксирован как `models/baseline.pt`;
  - decision flow после quality-gate все еще слишком зависит от ручной трактовки.

## Implementation Steps
1. Зафиксировать один локальный governance contract для baseline/candidate/decision states.
2. Выравнять docs и локальные contracts так, чтобы они не противоречили друг другу.
3. Убедиться, что source of truth для model decision определен явно и локально.

## Acceptance Criteria
- [ ] Есть один однозначный локальный baseline governance contract
- [ ] `baseline`, `candidate`, `hold_and_tune`, `reject` определены явно и непротиворечиво
- [ ] Документы проекта не спорят друг с другом о model decision flow

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `rg -n "baseline|candidate|hold_and_tune|reject" RUNBOOK.md OPERATOR_BASELINE.md PROJECT_ARCHITECTURE.md models -g '!models/*.pt'`
- Expected result:
  - governance terms documented consistently
  - compile still works

## Risks
- Risk: contract станет слишком теоретическим и не привязанным к реальным локальным файлам
- Mitigation: привязывать definitions к конкретным paths и artifacts
