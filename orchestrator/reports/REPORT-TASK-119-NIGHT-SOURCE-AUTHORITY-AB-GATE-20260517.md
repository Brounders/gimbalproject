# REPORT-TASK-119-NIGHT-SOURCE-AUTHORITY-AB-GATE-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted locally

## Scope

TASK-20260517-119 проверяла no-training runtime lever: может ли `night` source
быть безопасно подготовлен как primary/confirmable candidate for IR/night A/B,
не меняя текущие пресеты по умолчанию.

## Finding

До изменения `DetectionSource.NIGHT` не входил в primary source set. Поэтому
night target мог быть выбран как active по скорости/score, но не мог стать
confirmed drone lock через `has_confirmed_drone_lock()`. Для weak IR clips, где
YOLO отсутствует, это ограничивает путь к устойчивому lock без обучения.

## Changes

Добавлен default-off runtime switch:

- `Config.NIGHT_PRIMARY_SOURCE_ENABLED = False`
- `Config.NIGHT_PRIMARY_DRONE_SCORE = 0.70`
- YAML/profile mapping:
  - `night_primary_source_enabled`
  - `night_primary_drone_score`

TargetManager behavior:

- default behavior unchanged;
- when `NIGHT_PRIMARY_SOURCE_ENABLED=True`, `DetectionSource.NIGHT` is treated as
  primary by the manager instance;
- newly created night targets receive configurable initial drone score only when
  the flag is enabled.

Tests:

- added `tests/test_night_source_authority.py`;
- verifies default night source is not confirmable;
- verifies guarded night source can become confirmed when explicitly enabled.

## Validation

Passed:

- `PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_night_source_authority.py tests/test_night_small_target_detector.py tests/test_proposal_trust.py tests/test_target_manager_lock_policy.py -q`
- `PYTHONPATH=src tracker_env/bin/python -m pytest -q`
- `python3 orchestrator/scripts/check_orchestration_state.py`
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `git diff --check`

## Decision

The runtime lever is now available but not active in any preset by default.

Next step must be a candidate A/B gate, not promotion:

- create or use a candidate preset/config enabling `night_primary_source_enabled`
  only for IR/night evaluation;
- run weak4/protected problem-pack gates;
- accept only if weak IR recall improves without protected/noise/airplane/bird
  regression.

## Open TASK-20260517-120

Task: Night-primary candidate A/B gate.

Constraints:

- no RTX;
- no training;
- no production model replacement;
- do not enable the flag in operator default presets unless A/B passes.
