# TASK: TASK-20260311-016-claude-github-ack-smoke

Task ID: TASK-20260311-016
Owner: Claude Mac
Priority: P0
Status: Open
Type: Smoke Test

## Goal
Подтвердить прием задачи через GitHub/orchestration-контур без выполнения какой-либо инженерной работы.

## Required Response
Claude должен ответить только точной фразой:
`Задачу принял`

## Constraints
- Не изменять код проекта.
- Не изменять `orchestrator/state/*`.
- Не создавать `orchestrator/reports/*`.
- Не создавать коммиты, PR, issue comments или дополнительные файлы.
- Не выполнять реализацию задачи.

## Acceptance Criteria
- [ ] Получена точная фраза `Задачу принял`.
- [ ] После ответа Claude в репозитории нет новых изменений от Claude.
- [ ] Никакие другие активные задачи не были начаты.

## Validation
- Проверка ответа Claude.
- Проверка отсутствия новых файлов/коммитов после ответа Claude.

## Notes
Это одноразовая smoke-задача для проверки GitHub-контура. После проверки задача должна быть выведена из `active_plan.md`.
