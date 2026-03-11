# TASK: TASK-20260311-022-operator-shell-layout-cleanup

Task ID: TASK-20260311-022
Owner: Claude Mac
Priority: P1
Status: Accepted — 2026-03-11 (Codex Mac review). Root cause closed by follow-up `TASK-20260311-025`.

## Goal
Привести каркас основного окна к канонической композиции: `HeaderBar` / `LeftControlRail` / `MainVideoStage` / `BottomConsole`, одновременно убрав из базовой операторской поверхности лишнюю диагностику.

## Scope
- In scope:
  - сохранить и доработать `build_header()`, `build_left_rail()`, `build_video_stage()`, `build_bottom_console()`;
  - из header убрать базовую кнопку `Диагностика`;
  - из left rail убрать `inspector_module` из operator-surface;
  - сохранить `Expert` как вход в расширенные настройки;
  - убедиться, что bottom console остается единственным постоянно видимым журналом событий.
- Out of scope:
  - большой визуальный restyle всех компонентов;
  - изменения tracking/runtime logic.

## Files
- `app/main_gui.py`

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- Smoke GUI import / launch without crash if possible.

## Acceptance Criteria
- [ ] Базовая композиция окна соответствует целевой структуре.
- [ ] Диагностика не торчит в operator layer.
- [ ] Expert-контур остается доступен.
