# TASK: TASK-20260311-029-false-lock-suppression-hardening

Task ID: TASK-20260311-029
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Точечно снизить `false_lock_rate` и `active_id_changes_per_min` на night/IR/noise сценах для текущего runtime-контура без нового обучения.

## Scope
- In scope:
  - ужесточить подтверждение lock и/или условия перехода в подтвержденный active target для шумных night/IR случаев;
  - скорректировать `unverified_active`/noise suppression логику, если именно она пропускает шум в operator-critical scenes;
  - сделать минимальные обратимые правки вокруг `lock confirm`, `reacquire` и scene-aware suppression.
- Out of scope:
  - новое обучение модели;
  - большой рефактор tracking pipeline;
  - UI-изменения.

## Files
- `src/uav_tracker/pipeline.py`
- `src/uav_tracker/config.py`
- `src/uav_tracker/tracking/*` только если без этого нельзя локализовать suppression fix

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `PYTHONPATH=src ./tracker_env/bin/python -m unittest -q tests.test_package_import tests.test_target_manager_lock_policy`
- локальный targeted smoke минимум на:
  - `test_videos/night_ground_large_drones.mp4`
  - `test_videos/Demo_IR_DRONE_146.mp4`
  - `test_videos/night_ground_indicator_lights.mp4`

## Acceptance Criteria
- [ ] Runtime hardening остается локальным и не превращается в rewrite.
- [ ] На targeted smoke есть аргументированное улучшение хотя бы по одному из главных KPI: `false_lock_rate` или `active_id_changes_per_min` на проблемных сценах.
- [ ] Нет явной деградации FPS более чем на ~10% на тех же targeted clips.
