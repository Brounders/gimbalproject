# TASK: TASK-20260311-020-auto-scene-detection-hardening

Task ID: TASK-20260311-020
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Сделать `Auto` режим реально scene-aware: надежнее распознавать night/IR/day сцену и не оставаться в дневном поведении на очевидно ночном видео.

## Scope
- In scope:
  - проанализировать текущую логику `Auto` в UI/runtime mapping;
  - ввести простой и объяснимый auto-scene heuristic для `Day/Night/IR`;
  - добавить hysteresis/confirmation, чтобы режим не прыгал между состояниями;
  - оставить expert/manual modes без изменений.
- Out of scope:
  - ML scene classifier;
  - расширение набора базовых режимов сверх `Auto/Day/Night/IR`.

## Files
- `app/main_gui.py`
- `src/uav_tracker/pipeline.py`
- `src/uav_tracker/config.py` (если нужен явный конфиг порогов)
- `configs/*.yaml` (только при необходимости каноничных threshold settings)

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- Локальный smoke-run хотя бы на одном night clip и одном normal/day clip, если возможно.
- Проверка, что auto mode не oscillates на коротком промежутке.

## Acceptance Criteria
- [ ] `Auto` на очевидной ночной сцене включает night-oriented behavior.
- [ ] `Auto` не переключается хаотично между day/night/IR.
- [ ] Ручные режимы `Day/Night/IR` не деградируют.
