# BRIEF: BRIEF-20260312-016-local-reproducibility-and-quality-v1

## Context
Аудит `REPORT-20260312-032` и последующий цикл локальной целостности продукта подтвердили, что проект стал чище как desktop-программа, но его следующая слабая зона теперь не в теме UI и не в корне проекта, а в локальной воспроизводимости и discipline контуре качества. Финальный продукт остается локальной программой; RTX/GitHub/automation-контур рассматривается как временный вспомогательный слой и не должен диктовать архитектуру продукта.

## Objective
Зафиксировать локальную воспроизводимость и quality discipline проекта: создать явный dependency contract, разделить regression clips по preset/scenario и сделать локальный quality-gate понятным и каноническим для baseline/candidate решений.

## Success Metrics
- Локальный bootstrap проекта больше не зависит от неявного состояния `tracker_env`.
- Regression/evaluation assets разделены минимум на `day`, `night`, `ir`.
- Для локального разработчика и оператора однозначно понятно, что запускать в цепочке `quick smoke -> benchmark -> quality-gate`.

## Boundaries
- Must do:
  - работать в рамках локального desktop-контура;
  - улучшать reproducibility и docs без расширения web/RTX/automation как ядра проекта;
  - сохранить совместимость существующих validation-команд и текущего benchmark/gate tooling.
- Must not do:
  - не делать deep refactor `pipeline.py` и `main_gui.py` в этом цикле;
  - не менять `datasets/`, `runs/`, `tracker_env/`;
  - не открывать новый training cycle и не менять operator runtime behavior.

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- Three focused implementation tasks for local reproducibility and quality discipline
- Updated local dependency/bootstrap contract
- Preset-specific regression pack contract
- Canonical local `quick smoke -> benchmark -> quality-gate` decision flow
