# BRIEF: BRIEF-20260311-002-testability-and-stability-hardening

## Context
Первый цикл стабилизации выполнен: overlay extraction stage-1 и базовые lock-policy unit-tests приняты. Следующий шаг должен повысить тестопригодность и предсказуемость мелкими безопасными изменениями без расширения архитектурного риска.

## Objective
Укрепить контур разработки через low-risk задачи:
1) устранить жесткую связку package-import с runtime-зависимостями,
2) расширить unit-тесты для ключевого выбора active target,
3) подготовить основу для следующей итерации стабилизации KPI.

## Success Metrics
- Пакетные импорты `uav_tracker` не ломают unit-тесты без запуска runtime-контура.
- Покрыты тестами сценарии выбора active цели между конкурентами.
- State и task-индексы отражают проверенный статус задач.

## Boundaries
- Must do:
  - минимальные изменения;
  - нулевая деградация runtime-поведения;
  - обязательная проверка compile + tests.
- Must not do:
  - крупный рефактор pipeline;
  - изменения quality-gate логики;
  - внедрение новых зависимостей.

## Deliverables
- 1–2 точечные задачи Claude на testability и lock policy quality.
- Обновленный orchestration state.
