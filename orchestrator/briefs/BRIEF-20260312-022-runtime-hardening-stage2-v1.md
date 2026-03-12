# BRIEF: BRIEF-20260312-022-runtime-hardening-stage2-v1

## Context
После stage-1/0 архитектурной декомпозиции, local baseline governance и первого цикла runtime-quality hardening главный практический дефект проекта остается операторским: `false_lock_rate` и шумовые reacquire на `night` / `ir` / noise сценах все еще ограничивают полезность локального desktop-продукта. Последний cycle (`061/062/063`) дал bounded improvement, но не закрыл проблему полностью.

## Objective
Сделать второй короткий runtime-hardening cycle только про operator-critical behavior: отдельно усилить lock gating на шумовых сценах, ужесточить reacquire/hold policy на коротких разрывах и ввести обязательный A/B evidence loop по canonical problem clips.

## Success Metrics
- `false_lock_rate` на `night_ground_indicator_lights` и других canonical problem clips снижается или явно не ухудшается
- reacquire/hold behavior становится более предсказуемым и менее шумным на коротких разрывах
- появляется один канонический before/after evidence flow для problem-clip runtime tuning

## Boundaries
- Must do:
  - работать только в локальном desktop-контуре проекта;
  - усиливать runtime behavior без нового training cycle;
  - использовать существующие `RUNBOOK`, `OPERATOR_BASELINE`, `regression_pack_problem.csv`, `run_quick_kpi_smoke.py`, `run_quality_gate.py` как опору.
- Must not do:
  - не открывать новый training cycle;
  - не делать новый UI redesign;
  - не делать deep refactor `pipeline.py` / `main_gui.py`;
  - не расширять RTX/GitHub/web-инфраструктуру как центр архитектуры.

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- One targeted noise-scene lock/reacquire hardening pass
- One explicit reacquire/hold policy hardening pass
- One canonical A/B evidence loop on problem clips with before/after comparison artifacts
