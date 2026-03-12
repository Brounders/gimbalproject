# BRIEF: BRIEF-20260312-019-main-gui-stage0-split-v1

## Context
После stage-1 split `src/uav_tracker/pipeline.py` следующим крупнейшим архитектурным монолитом проекта остается `app/main_gui.py`. Финальный продукт остается локальной desktop-программой; временный RTX/GitHub/web слой не должен определять порядок архитектурного ремонта. Следующий рациональный шаг — безопасная stage-0 декомпозиция GUI-shell без редизайна и без вмешательства в tracking logic.

## Objective
Сделать первый безопасный split `app/main_gui.py`: вынести theme/style wiring, display-card/HUD helpers и не-worker UI plumbing так, чтобы `main_gui.py` стал orchestration-first модулем окна без изменения текущего operator behavior.

## Success Metrics
- `main_gui.py` заметно уменьшается и становится orchestration-first.
- Theme/style-related code живет в dedicated UI helper module(s).
- Display/HUD card helpers живут отдельно от window orchestration.
- GUI launch, CLI help, compile and current tests continue to work.

## Boundaries
- Must do:
  - работать только в локальном desktop-контуре проекта;
  - сохранить текущий operator layout и current runtime behavior;
  - не переносить business/tracking logic в view layer.
- Must not do:
  - не делать новый UI redesign;
  - не трогать `src/uav_tracker/pipeline.py` архитектурно в этом цикле;
  - не менять training/eval/orchestration logic;
  - не трогать embedded/Hailo migration.

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words instead of synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- theme/style helper extraction around `app/ui/theme.py`
- display-card/HUD helper extraction out of `app/main_gui.py`
- non-worker UI plumbing extraction that leaves `main_gui.py` as a clearer window orchestrator
