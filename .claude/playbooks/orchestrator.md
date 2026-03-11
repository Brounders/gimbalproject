# Orchestrator Playbook

## Когда использовать
- Работа по `active_plan`.
- Анализ backlog и state.
- Выполнение задач из `orchestrator/tasks`.
- Подготовка отчетов в `orchestrator/reports`.

## Обязательный порядок
1. `git pull --ff-only`
2. Прочитать:
   - `orchestrator/state/active_plan.md`
   - `orchestrator/state/open_tasks.md`
   - `orchestrator/state/completed_tasks.md`
   - `orchestrator/state/open_training.md`
3. Выполнять только задачи, перечисленные в `active_plan.md`.
4. Не брать backlog-задачи вне active plan.
5. После выполнения обновить report/state только в пределах выполненной задачи.

## Ограничения
- Минимальный и обратимый diff.
- Не переписывать runtime-код без явного task.
- Не менять стратегию проекта самостоятельно.

## Обязательная валидация
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `python3 orchestrator/scripts/check_orchestration_state.py`
