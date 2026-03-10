# TASK: TASK-20260311-003-package-import-decoupling

## Goal
Снизить связанность package-level import в `src/uav_tracker/__init__.py`, чтобы unit-тесты могли импортировать `uav_tracker.config` и `uav_tracker.tracking.*` без обязательной загрузки тяжёлого runtime (cv2/YOLO pipeline).

## Scope
- In scope:
  - минимально изменить `src/uav_tracker/__init__.py` (lazy import или безопасный экспорт);
  - сохранить текущий публичный API для runtime-точек входа;
  - обновить/добавить тест импорта.
- Out of scope:
  - изменение логики трекера;
  - изменения GUI/CLI поведения.

## Constraints
- Минимальный обратимый diff.
- Без новых зависимостей.
- Без изменения runtime-алгоритмов.

## Inputs
- `src/uav_tracker/__init__.py`
- `tests/`

## Implementation Steps
1. Убрать eager-import pipeline в package init или заменить на lazy pattern.
2. Проверить, что `from uav_tracker.config import Config` работает независимо от cv2.
3. Добавить короткий regression test на package import boundary.

## Status
Done — 2026-03-11. Report: orchestrator/reports/REPORT-20260311-003.md

## Acceptance Criteria
- [x] Import boundary исправлен: package import не тянет runtime-зависимости без необходимости.
- [x] Runtime entrypoints продолжают работать.
- [x] Проверки проходят: compile + unit tests (15/15).

## Validation
- `python3 -m compileall -q python_scripts src app tests`
- `PYTHONPATH=src ./tracker_env/bin/python -m unittest -q tests.test_target_manager_lock_policy`
- `PYTHONPATH=src ./tracker_env/bin/python -c "from uav_tracker.config import Config; print('OK')"`

## Risks
- Risk: сломать обратную совместимость импорта `from uav_tracker import TrackerPipeline`.
- Mitigation: сохранить API через lazy-export и добавить smoke import check.
