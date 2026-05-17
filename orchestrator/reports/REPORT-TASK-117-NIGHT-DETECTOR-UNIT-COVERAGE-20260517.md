# REPORT-TASK-117-NIGHT-DETECTOR-UNIT-COVERAGE-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted locally

## Scope

Human решил отложить RTX/training: обучение станет рутинной работой позже, если
оно не требуется прямо сейчас.

Следующий локальный шаг: закрыть safety gap вокруг `NightSmallTargetDetector`
перед дальнейшими detector/runtime изменениями.

## Changes

- Добавлен `tests/test_night_small_target_detector.py`.
- Покрыты synthetic contracts без видео, YOLO weights и обучения:
  - warmup no-detection contract;
  - peak-path detection small bright target;
  - border rejection;
  - area filter rejection;
  - grid-cell collision distinct sub-id contract;
  - sticky active target selection;
  - peak top-k/NMS bounded rows.

## Validation

- `PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_night_small_target_detector.py -q`
  - PASS: 7 tests.

## Decision

- RTX sync/training is deferred by Human.
- Local detector work may continue without training.
- Next task should be a no-training detector strategy gate: identify whether a
  bounded runtime/config/tooling change can improve weak clips before returning
  to dataset/training work.

## Non-Changes

- Runtime detector code was not changed.
- Training was not started.
- RTX was not used.
- File/folder restructure was not performed.
