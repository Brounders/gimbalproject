# TASK: TASK-20260311-002-lock-policy-unit-tests

## Goal
Добавить минимальный тестовый контур для lock/ID-policy, чтобы следующие точечные правки трекинга были проверяемыми и не делались вслепую.

## Scope
- In scope:
  - создать `tests/`;
  - добавить unit-тесты для `TargetManager` (гистерезис подтверждения, блокировка агрессивной смены ID, LOST-переход);
  - использовать стандартную библиотеку (`unittest`) или существующий раннер без новых зависимостей.
- Out of scope:
  - изменение прод-логики трекера,
  - интеграционные видео-бенчмарки.

## Constraints
- Не менять алгоритм работы TargetManager в этом task.
- Не добавлять внешние зависимости.

## Inputs
- `src/uav_tracker/tracking/target_manager.py`
- `src/uav_tracker/config.py`

## Implementation Steps
1. Создать `tests/test_target_manager_lock_policy.py`.
2. Описать 3-5 детерминированных сценариев входных кадров.
3. Проверить ожидаемые переходы/счетчики (`TRACK/LOST`, смены active_id, confirm behavior).
4. Добавить короткий README в `tests/` (как запускать).

## Status
Done — 2026-03-11. Report: orchestrator/reports/REPORT-20260311-002.md

## Acceptance Criteria
- [x] Добавлены детерминированные unit-тесты для lock-policy.
- [x] Тесты запускаются одной командой (8/8 passed).
- [x] Без изменения runtime-кода трекинга.

## Validation
- `python3 -m compileall -q python_scripts src app tests`
- `python3 -m unittest -q tests.test_target_manager_lock_policy`

## Risks
- Risk: тесты завязаны на нестабильные внутренние детали.
- Mitigation: проверять только контрактное поведение (состояния/счетчики), а не внутренние переменные реализации.
