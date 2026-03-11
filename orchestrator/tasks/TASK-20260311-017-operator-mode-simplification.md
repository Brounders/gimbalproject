# TASK: TASK-20260311-017-operator-mode-simplification

Task ID: TASK-20260311-017
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Свести операторский выбор режимов к четырем каноническим сценариям: `Auto`, `Day`, `Night`, `IR`, при этом скрыв лишние профили из базового UI и сохранив экспертный доступ к тонким настройкам.

## Scope
- In scope:
  - ограничить операторский UI каноническими режимами `Auto/Day/Night/IR`;
  - определить и зафиксировать mapping этих режимов на существующие профили/параметры;
  - все остальные профили вывести только в expert-контур;
  - обновить краткую документацию/подсказки в UI, если требуется.
- Out of scope:
  - добавление новых runtime-режимов detection/tracking;
  - изменение training/eval workflow.

## Files
- `app/main_gui.py`
- `src/uav_tracker/profile_io.py` (если требуется для mapping)
- `configs/*.yaml` (только если требуется явный канон профилей)

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- Smoke launch GUI without crash.
- Ручная проверка: в операторском UI доступны только `Auto`, `Day`, `Night`, `IR`.

## Acceptance Criteria
- [ ] Оператор видит только `Auto/Day/Night/IR`.
- [ ] Expert-контур сохраняет доступ к остальным профилям/тонким параметрам.
- [ ] Изменения не ломают текущий runtime.
