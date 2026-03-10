# TASK: TASK-20260311-009-safe-reorg-plan

Task ID: TASK-20260311-009
Owner: Claude
Priority: P2
Goal: Подготовить безопасный план реорганизации файловой системы (phased), без выполнения destructive-действий.
Files:
- `orchestrator/reports/REPORT-20260311-009.md` (new)
- `orchestrator/state/filesystem_reorg_plan.md` (new)
Expected result:
- План из фаз P1/P2/P3: что можно перенести/заархивировать/оставить как есть.
- Для каждого шага: команда, rollback, критерий успеха, риск.
- Явный раздел "Запрещено трогать" (`datasets/`, `runs/`, `tracker_env/`, production entrypoints).
Validation:
- План содержит dry-run команды и чек-лист проверок (`git status`, compile smoke, entrypoint smoke).
- Нет команд удаления в первой фазе.
Constraints:
- Никаких перемещений/удалений в рамках этой задачи.
- Никаких изменений runtime и training логики.
- Никаких новых зависимостей.
Status: Done — 2026-03-11. Report: orchestrator/reports/REPORT-20260311-009.md
