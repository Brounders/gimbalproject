# TASK: TASK-20260311-026-auto-ir-scene-hardening

Task ID: TASK-20260311-026
Owner: Claude Mac
Priority: P1
Status: Accepted — 2026-03-11 (Codex Mac review). Report: orchestrator/reports/REPORT-20260311-026.md

## Goal
Довести режим `Auto` до полноценного маршрутизатора `Day / Night / IR`, сохранив минимальный и объяснимый heuristic-based подход.

## Scope
- In scope:
  - расширить текущую auto scene adaptation логику так, чтобы она различала не только `day/night`, но и `ir`;
  - добавить гистерезис/подтверждение по кадрам, чтобы режимы не прыгали;
  - использовать простые признаки сцены: яркость, насыщенность/монохромность, стабильность thermal-like кадра;
  - не ломать существующие canonical operator modes.
- Out of scope:
  - ML-классификатор сцены;
  - переписывание pipeline целиком.

## Files
- `src/uav_tracker/pipeline.py`
- `src/uav_tracker/config.py`
- `app/main_gui.py` только если нужно синхронизировать operator labels/tooltips

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `PYTHONPATH=src ./tracker_env/bin/python -m unittest -q tests.test_package_import tests.test_target_manager_lock_policy`
- локальная проверка/мини-smoke, что `Auto` умеет уходить в `night` и `ir` на соответствующих клипах без дрожащих переключений

## Acceptance Criteria
- [ ] `Auto` больше не ограничен только `day/night`.
- [ ] Переходы имеют подтверждение по кадрам и не дрожат.
- [ ] Canonical operator buttons и existing presets остаются совместимыми.
