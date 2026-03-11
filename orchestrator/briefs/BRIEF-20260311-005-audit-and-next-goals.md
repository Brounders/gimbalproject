# BRIEF: BRIEF-20260311-005-audit-and-next-goals

## Context
Human direction: провести аудит выполненной работы, зафиксировать слабые точки и определить следующие глобальные/локальные цели.

## Objective
Перевести audit-результаты в проверяемый инженерный backlog:
1) устранить неоднозначность entrypoints и запусков,
2) добавить быстрый KPI smoke-контур перед тяжелыми evaluation-прогонами,
3) подготовить stage-0 план безопасной декомпозиции монолитных модулей.

## Success Metrics
- Есть единый операторский runbook и карта входных команд.
- Есть воспроизводимый quick-smoke KPI запуск (короткий, детерминированный).
- Есть модульная карта разбиения `main_gui.py` и `pipeline.py` с рисками/rollback.

## Boundaries
- Must do:
  - минимальные и обратимые изменения;
  - без изменения tracking decision-loop в этой фазе;
  - обязательная локальная валидация.
- Must not do:
  - крупный runtime-рефактор в одной задаче;
  - смена model/training policy в рамках этого brief.

## Deliverables
- 3 задачи Claude (локальные, проверяемые, low-risk).
- Обновленные `active_plan`, `open_tasks`, `project_state`.
