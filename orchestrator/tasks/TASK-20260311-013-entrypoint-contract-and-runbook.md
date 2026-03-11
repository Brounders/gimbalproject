# TASK: TASK-20260311-013-entrypoint-contract-and-runbook

Task ID: TASK-20260311-013
Owner: Claude Mac
Priority: P1
Status: Accepted — 2026-03-11 (Codex Mac review). Report: orchestrator/reports/REPORT-20260311-013.md

## Goal
Устранить неоднозначность запусков проекта: зафиксировать канонические entrypoints и команды в одном runbook без изменения runtime-логики.

## Scope
- In scope:
  - создать `RUNBOOK.md` (operator / training / evaluation / orchestration commands);
  - описать допустимые точки входа (`main_tracker.py`, `tracker_gui.py`, `python_scripts/*`);
  - пометить legacy-скрипты в документации как non-canonical.
- Out of scope:
  - удаление или перемещение legacy-файлов;
  - изменение runtime-кода.

## Files
- `RUNBOOK.md` (new)
- `PROJECT_ARCHITECTURE.md` (update: короткая ссылка на runbook)

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator`
- Ручная проверка: команды из runbook существуют и запускаются с `--help` там, где применимо.

## Acceptance Criteria
- [ ] Один источник истины по запуску и ролям команд.
- [ ] Явно разделены operator/training/evaluation/orchestrator контуры.
- [ ] Без изменений runtime-поведения.
