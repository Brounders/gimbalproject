# TASK: TASK-20260311-010-primary-vs-primary-score-test

Task ID: TASK-20260311-010
Owner: Claude Mac
Priority: P2
Status: Done — 2026-03-11. Report: orchestrator/reports/REPORT-20260311-010.md

## Goal
Добавить тест конкуренции двух primary-целей с различным `drone_score` в `TestSelectActivePolicy`,
чтобы закрыть пробел, выявленный в REPORT-20260311-004.

Текущее покрытие проверяет Phase-1 early return (активная primary удерживается) и Phase-3/4 ветки.
**Непокрытая ветка**: при отсутствии активной цели (`active_id=None`) и наличии двух primary-кандидатов
выбирается тот, у кого выше `drone_score`. Этот сценарий — свободный switch по качеству сигнала.

## Scope
- In scope:
  - добавить 1-2 детерминированных теста в `TestSelectActivePolicy` в
    `tests/test_target_manager_lock_policy.py`;
  - покрыть: два primary-кандидата с разным `drone_score`, `active_id=None` → победитель = лучший score.
- Out of scope:
  - изменение runtime-кода `select_active()`;
  - изменение других тестовых классов.

## Constraints
- Без изменения runtime-алгоритмов.
- Тесты детерминированы: фиксированные score-значения, чёткий ожидаемый результат.
- Использовать существующий `_inject()` helper; speed устанавливать через `mgr.targets[tid].speed`.

## Inputs
- `tests/test_target_manager_lock_policy.py` (существующий)
- `src/uav_tracker/tracking/target_manager.py` — логика `select_active()`

## Implementation Hint
Два target с `source='yolo'`, `active_id=None`:
- target A: `drone_score=0.50`, speed=0 → слабее
- target B: `drone_score=0.75`, speed=0 → сильнее
Ожидаем: `active_id == B.id` после вызова `mgr.select_active()`.

Дополнительно (опционально): тест с равными score — проверить детерминизм.

## Validation
- `PYTHONPATH=src ./tracker_env/bin/python -m unittest -v tests.test_target_manager_lock_policy`
- `python3 -m compileall -q tests src`

## Acceptance Criteria
- [ ] 1-2 новых теста в `TestSelectActivePolicy`.
- [ ] Все зелёные, не ломают существующие 12 тестов.
- [ ] Ветка конкуренции primary vs primary покрыта.
