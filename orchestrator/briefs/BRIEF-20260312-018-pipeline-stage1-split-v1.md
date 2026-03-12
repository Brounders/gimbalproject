# BRIEF: BRIEF-20260312-018-pipeline-stage1-split-v1

## Context
После закрытия циклов локальной целостности продукта, воспроизводимости и baseline governance главный архитектурный долг проекта остается в `src/uav_tracker/pipeline.py`. Файл сохраняет одновременно data contract (`FrameOutput`), orchestration logic и overlay/draw helpers. Финальный продукт остается локальной desktop-программой; training/automation и web-layer не должны определять порядок архитектурного ремонта.

## Objective
Сделать первый безопасный split `pipeline.py`: вынести `FrameOutput` в отдельный модуль-контракт, вынести overlay/draw helpers, и оставить в `pipeline.py` только orchestration-логику без изменения runtime semantics.

## Success Metrics
- `pipeline.py` заметно уменьшается и становится оркестратором, а не контейнером всех слоев сразу.
- `FrameOutput` живет в отдельном модуле и остается совместимым с текущим GUI/CLI/runtime.
- Overlay/draw helpers живут отдельно от core orchestration и не меняют operator behavior.
- Compile, current tests, CLI help, and GUI smoke continue to work.

## Boundaries
- Must do:
  - работать только в локальном desktop-контуре проекта;
  - сохранить текущий runtime behavior и contract с GUI;
  - избегать algorithm rewrite и behavior changes.
- Must not do:
  - не трогать `app/main_gui.py` архитектурно в этом цикле;
  - не менять training/eval/orchestration logic вне необходимого wiring;
  - не открывать новый UI redesign или embedded migration.

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- `FrameOutput` extracted into a dedicated module
- overlay/draw helpers extracted out of `pipeline.py`
- `pipeline.py` thinned to orchestration-first structure
- no behavior regressions in current local desktop flow
