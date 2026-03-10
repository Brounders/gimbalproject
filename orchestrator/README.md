# Orchestrator Layer

Этот слой управляет взаимодействием между агентами без изменения runtime-кода.
Репозиторий GitHub — единственный источник состояния.

## Active Plan Protocol

1. Human задает направление через `План: ...`.
2. Codex Mac интерпретирует направление и обновляет `orchestrator/state/active_plan.md`.
3. `active_plan.md` — единственный источник активного контекста исполнения.
4. Claude Mac выполняет только задачи, перечисленные в `active_plan.md`.
5. Если в `active_plan.md` нет задач для Claude, Claude ничего не делает.
6. `orchestrator/state/open_tasks.md` — backlog, не эквивалент active plan.
7. При каждом обновлении `active_plan.md` Codex обязан синхронно обновить:
   - `orchestrator/state/open_tasks.md`
   - `orchestrator/state/completed_tasks.md`
   - `orchestrator/state/open_training.md` (если изменился training-контекст)
8. Любая рассинхронизация `active_plan` и state-индексов считается orchestration bug.

## Workflow

1. **Codex Mac → анализ → задачи Claude**
   - анализ архитектуры и состояния;
   - создание brief/task в `orchestrator/briefs` и `orchestrator/tasks`;
   - постановка проверяемых критериев приемки.

2. **Claude Mac → реализация → отчет**
   - выполнение задачи минимальным диффом;
   - публикация отчета в `orchestrator/reports`.

3. **Codex Mac → ревью**
   - проверка task/report/diff/валидации;
   - решение: accepted или rework.

4. **Codex Mac → training задачи RTX**
   - формирование задач в `orchestrator/training`;
   - фиксация ожиданий по артефактам и валидации.

5. **Codex RTX → обучение и evaluation**
   - запуск training/eval;
   - выгрузка артефактов и статусов в репозиторный workflow.

## Backlog vs Active Plan

- `open_tasks.md`: полный пул доступных задач (backlog).
- `active_plan.md`: подмножество задач из backlog, разрешенное к исполнению сейчас.
- При конфликте источников приоритет всегда у `active_plan.md`.
- Проверка согласованности выполняется скриптом `orchestrator/scripts/check_orchestration_state.py`.

## Структура

- `briefs/` — постановки фаз и эпиков.
- `tasks/` — конкретные инженерные задачи для реализации.
- `reports/` — отчеты выполнения задач.
- `training/` — задачи обучения/оценки для RTX.
- `state/` — состояние проекта и индексы очередей.
- `templates/` — шаблоны документов.
- `scripts/` — проверки консистентности orchestration-слоя.
