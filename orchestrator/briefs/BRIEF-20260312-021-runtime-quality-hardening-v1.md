# BRIEF: BRIEF-20260312-021-runtime-quality-hardening-v1

## Context
После локальной целостности продукта, reproducibility, baseline governance, split `pipeline.py`/`main_gui.py` и жесткого local quality loop главный практический дефект проекта сместился в runtime behavior на `night` / `ir` / noise сценах. Candidate-модели чаще упираются не в raw detection, а в высокий `false_lock_rate`, шумовые reacquire и operator-unfriendly поведение на проблемных клипах.

## Objective
Сделать следующий короткий цикл только про runtime-quality hardening: снизить ложные lock на `night` / `ir` / noise сценах, сделать preset-specific runtime tuning явным и ввести короткий regression pack по самым проблемным клипам.

## Success Metrics
- `false_lock_rate` на проблемных `night` / `ir` сценах снижается или не ухудшается при сохранении operator continuity
- runtime knobs для `day`, `night`, `ir` становятся явными и непротиворечивыми
- problem-clip regression pack становится каноническим short-loop для runtime hardening

## Boundaries
- Must do:
  - работать только в локальном desktop-контуре проекта;
  - усиливать runtime behavior на `night` / `ir` / noise без смены модели;
  - использовать уже существующие `quality-gate`, `benchmark`, `RUNBOOK`, `OPERATOR_BASELINE` как опору.
- Must not do:
  - не открывать новый training cycle;
  - не делать deep refactor `pipeline.py` / `main_gui.py`;
  - не делать UI redesign;
  - не расширять RTX/GitHub/web-инфраструктуру как архитектурный центр.

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- Three focused implementation tasks for runtime-quality hardening
- Explicit preset-specific runtime tuning contract for `day`, `night`, `ir`
- Canonical short regression pack for problem clips
- Validation evidence on the problem scenes, not only on aggregate metrics
