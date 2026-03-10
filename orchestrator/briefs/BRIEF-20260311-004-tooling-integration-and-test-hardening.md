# BRIEF: BRIEF-20260311-004-tooling-integration-and-test-hardening

## Context
BRIEF-003 полностью закрыт: TASK-003..006 приняты. В системе появились два рабочих инструмента —
`analyze_lock_events.py` и `validate_profile_presets.py`. Однако инструменты существуют изолированно
и не встроены в эксплуатационный цикл. Параллельно выявлены два точечных пробела из ревью:

1. **Тестовый пробел** (REPORT-004): конкуренция двух primary-целей по `drone_score` не покрыта.
   Это единственная непроверенная ветка свободного switch между primary-целями.

2. **Дублирование типов** (REPORT-006): `_TYPE_RULES` в `validate_profile_presets.py` дублирует знания
   о типах полей из `Config` датакласса. При добавлении нового поля в Config валидатор не обновляется
   автоматически.

3. **Интеграционный пробел**: pre-flight валидация пресетов и post-run анализ lock-событий
   должны быть частью stable cycle, а не только ручными CLI-командами.

## Objective
Закрыть выявленные пробелы без изменения runtime-алгоритмов:
- Добавить тест для конкуренции primary vs primary в `select_active()`.
- Автоматизировать вывод типов валидатора из Config (убрать дублирование).
- Встроить `validate_profile_presets.py` в `run_stable_cycle.py` как pre-flight шаг.

## Success Metrics
- Тест конкуренции primary vs primary добавлен и зелёный.
- `_TYPE_RULES` заменены на авто-вывод из `dataclasses.fields(Config)`.
- `run_stable_cycle.py` вызывает валидатор пресетов перед запуском бенчмарка.
- Все 3 задачи проходят compileall + unit tests.

## Boundaries
- Must do: минимальный diff, локальные изменения, проверяемые результаты.
- Must not do: изменение decision-loop трекера; изменения quality-gate порогов; крупные рефакторы.

## Deliverables
- 3 задачи для Claude Mac (P2, локальные, конкретные).
- Обновлённый project_state.md.
