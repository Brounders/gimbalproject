# TASK: TASK-20260311-004-select-active-policy-tests

## Status
Accepted — 2026-03-11 (Codex Mac review). Report: orchestrator/reports/REPORT-20260311-004.md

## Goal
Расширить unit-тесты lock-policy сценариями выбора active target (`select_active`) между конкурирующими целями, чтобы снизить риск регрессий `active_id_changes_per_min` в night/IR.

## Scope
- In scope:
  - добавить тесты конкуренции primary/aux целей в `tests/test_target_manager_lock_policy.py`;
  - покрыть минимум 2 сценария: устойчивое удержание active и допустимое переключение по условиям;
  - обновить `tests/README.md` при необходимости.
- Out of scope:
  - изменение runtime-логики `TargetManager`;
  - tuning порогов в production config.

## Constraints
- Только тестовые изменения.
- Без новых зависимостей.

## Inputs
- `src/uav_tracker/tracking/target_manager.py`
- `tests/test_target_manager_lock_policy.py`

## Implementation Steps
1. Добавить deterministic fixtures для multi-target состояния.
2. Проверить поведение `select_active()` при активной цели и конкуренте.
3. Зафиксировать ожидания по switch/no-switch и счетчикам.

## Acceptance Criteria
- [x] Добавлены новые тесты по `select_active()` (минимум 2).
- [x] Полный тестовый набор проходит.
- [x] Изменений runtime-кода нет.

## Validation
- `PYTHONPATH=src ./tracker_env/bin/python -m unittest -q tests.test_target_manager_lock_policy`
- `python3 -m compileall -q tests src`

## Risks
- Risk: тесты станут хрупкими при изменении внутренних деталей.
- Mitigation: проверять контракт поведения (active_id/switch decision), не приватные поля.
