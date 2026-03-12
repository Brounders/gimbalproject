# TASK: TASK-20260312-053-pipeline-overlay-extract

Task ID: TASK-20260312-053
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Вынести overlay/draw helpers из `src/uav_tracker/pipeline.py` в отдельный модуль, оставив визуальное поведение операторского слоя неизменным.

## Scope
- In scope:
  - `src/uav_tracker/pipeline.py`
  - новый overlay/draw module
  - helper functions directly related to frame rendering
- Out of scope:
  - изменение operator HUD design
  - refactor `app/main_gui.py`
  - изменение tracking algorithms

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `src/uav_tracker/pipeline.py`
  - any helpers used only for drawing / overlay composition
- Context:
  - operator overlay behavior after recent UI cycles must not regress.

## Implementation Steps
1. Выделить draw/overlay helpers в отдельный module.
2. Оставить в `pipeline.py` только вызов render helpers, а не их реализацию.
3. Не менять visual contract intentionally; only extract and wire.

## Acceptance Criteria
- [ ] overlay/draw helpers физически вынесены из `pipeline.py`
- [ ] `pipeline.py` больше не содержит весь rendering code inline
- [ ] quick smoke / GUI launch do not regress visually by code path

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `PYTHONPATH=src ./tracker_env/bin/python main_tracker.py --help`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --sources test_videos/cli_smoke_test.mp4 --max-frames 30 --preset default`
- Expected result:
  - compile clean
  - CLI callable
  - smoke script still runs

## Risks
- Risk: extracted overlay helpers accidentally capture runtime state or introduce circular imports
- Mitigation: keep new module render-focused and pass explicit inputs only
