# TASK: TASK-20260312-050-accepted-model-install-flow

Task ID: TASK-20260312-050
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Сделать accepted-model install flow воспроизводимым: установить принятую модель в `models/baseline.pt` должно быть можно по каноническому локальному пути и с понятной metadata/traceability.

## Scope
- In scope:
  - локальный install/update flow для `models/baseline.pt`
  - metadata/manifest contract для установленной baseline-модели
  - `RUNBOOK.md`
  - `models/` sidecar file(s) or helper script(s)
- Out of scope:
  - хранение бинарной baseline-модели в git
  - promotion новой candidate-модели как часть этой задачи
  - remote artifact delivery redesign

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `models/`
  - `RUNBOOK.md`
  - `OPERATOR_BASELINE.md`
- Context:
  - baseline model path уже стабилизирован как local contract, но flow установки и traceability еще не формализованы.

## Implementation Steps
1. Зафиксировать локальный install flow для accepted model в `models/baseline.pt`.
2. Добавить sidecar metadata/manifest или helper script, чтобы baseline update был traceable.
3. Обновить docs так, чтобы установка baseline была воспроизводимой на новой машине.

## Acceptance Criteria
- [ ] Есть канонический локальный flow установки accepted model
- [ ] У baseline есть понятная metadata/traceability без хранения `.pt` в git
- [ ] Документация и локальный contract согласованы

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `rg -n "baseline.pt|baseline" RUNBOOK.md OPERATOR_BASELINE.md models -g '!models/*.pt'`
- Expected result:
  - accepted-model install flow documented and traceable
  - compile still works

## Risks
- Risk: flow будет опираться на ручные действия без фиксированной metadata
- Mitigation: требовать explicit sidecar contract or helper path
