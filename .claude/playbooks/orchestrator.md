# Orchestrator Playbook

## Когда использовать
- Работа по `active_plan`.
- Анализ backlog и state.
- Выполнение задач из `orchestrator/tasks`.
- Подготовка отчетов в `orchestrator/reports`.

## Обязательный порядок
1. `git status --short --branch`
2. Прочитать только нужные state-файлы:
   - `orchestrator/state/active_plan.md`
   - `orchestrator/state/open_tasks.md`
   - `orchestrator/state/open_training.md`, если задача касается training/RTX
3. Читать `completed_tasks.md`, reports или task files только если они явно названы или нужны для конкретного active item.
4. Выполнять только задачи, перечисленные в `active_plan.md` или прямо заданные Codex/Human.
5. Не брать backlog-задачи вне active plan.
6. После выполнения обновить report/state только в пределах выполненной задачи.

## Ограничения
- Минимальный и обратимый diff.
- Не переписывать runtime-код без явного task.
- Не менять стратегию проекта самостоятельно.
- Не делать `git pull`, `git add`, `git commit`, `git push` без явной команды Codex/Human.

## Обязательная валидация
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `python3 orchestrator/scripts/check_orchestration_state.py`
