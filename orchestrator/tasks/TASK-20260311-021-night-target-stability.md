# TASK: TASK-20260311-021-night-target-stability

Task ID: TASK-20260311-021
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Снизить дрожание рамки и улучшить плавность/точность сопровождения цели в ночных условиях через локальную стабилизацию bbox/center presentation без переписывания decision loop.

## Scope
- In scope:
  - separate smoothing for center and bbox size, if needed;
  - hold/freeze logic for very short target dropouts;
  - clamp or damp abrupt bbox width/height jumps;
  - использовать existing lock/template path where helpful for short night gaps;
  - минимальные изменения, подтвержденные smoke behavior.
- Out of scope:
  - полный Kalman rewrite, если локальных мер достаточно;
  - полный refactor TargetManager;
  - изменение training/model weights.

## Files
- `src/uav_tracker/pipeline.py`
- `src/uav_tracker/tracking/lock_tracker.py` (если нужен локальный hold aid)
- `src/uav_tracker/overlay.py`
- `configs/night.yaml` / `configs/default.yaml` (только если действительно нужны новые display/stability thresholds)

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- Короткий локальный smoke-run на night/IR clip, если возможен.
- Сравнение до/после по визуальной стабильности и отсутствию явного дополнительного lag.

## Acceptance Criteria
- [ ] Ночная рамка ведет себя заметно плавнее.
- [ ] Короткие пропуски детекции не вызывают резкого скачка/рывка.
- [ ] Нет явной деградации реакции на быстрые движения цели.
