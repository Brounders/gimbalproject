# Active Plan

## Plan ID
- AP-20260311-007

## Source Direction
- Human direction: `План: Исправить Причина по TASK-022: inspector_module скрыт по умолчанию, но все еще восстанавливается из ui/inspector_visible и может снова появиться в operator-layer на старте.`
- Human confirmation for delivery: `Принимаю`

## Status
- Active

## Brief In Focus
- BRIEF-20260311-010-inspector-operator-isolation

## Active Claude Tasks (execution allowed now)
- TASK-20260311-025 | inspector expert isolation | Open

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.
- TASK-20260311-013 остается backlog-task и не относится к текущему fix cycle.

## Exit Criteria
- `inspector_module` не восстанавливается в operator-layer из persisted settings.
- Обычный старт окна держит `inspector_module.isVisible() == False`.
- Expert-контур не ломается.
