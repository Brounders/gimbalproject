# BRIEF: BRIEF-20260312-017-local-baseline-governance-v1

## Context
После циклов локальной целостности продукта и локальной воспроизводимости проект стал понятнее как desktop-программа, но baseline/candidate governance все еще слишком зависит от ручной интерпретации. Финальный продукт остается локальной программой; временный RTX/GitHub/automation-контур не должен определять, как локально принимается и устанавливается рабочая модель.

## Objective
Зафиксировать локальный baseline governance contract: однозначно описать baseline/candidate/hold/reject states, сделать локальный flow установки принятой модели воспроизводимым и стандартизировать decision artifacts quality-gate контура.

## Success Metrics
- Локально однозначно понятно, что считается baseline, candidate и решением по модели.
- Accepted model можно установить в `models/baseline.pt` по каноническому flow без ручной двусмысленности.
- Quality decision artifacts имеют один понятный локальный формат и могут использоваться как source of truth для operator/model decisions.

## Boundaries
- Must do:
  - работать только в локальном desktop-контуре проекта;
  - укреплять local baseline governance без расширения web/RTX/GitHub как основного контура;
  - сохранить текущий runtime behavior без deep refactor ядра.
- Must not do:
  - не менять `pipeline.py` / `main_gui.py` архитектурно в этом цикле;
  - не запускать новый training cycle;
  - не продвигать candidate модель без отдельного review.

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- Three focused implementation tasks for local baseline governance
- Canonical local baseline/candidate decision contract
- Reproducible accepted-model install flow
- Standardized local quality decision artifact format
