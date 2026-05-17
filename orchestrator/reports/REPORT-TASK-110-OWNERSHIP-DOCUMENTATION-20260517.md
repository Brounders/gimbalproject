# REPORT-TASK-110-OWNERSHIP-DOCUMENTATION-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted locally

## Scope

TASK-20260517-110 требовала ownership documentation после full-project audit:

- создать script registry для `python_scripts/`;
- зафиксировать primary operator UI authority;
- добавить decision note для `ui_web/`;
- добавить status note для `automation/state/`;
- не делать file moves, deletes, runtime edits и training runs.

## Changes

- Добавлен `python_scripts/README.md` как первичный реестр скриптов.
- Добавлен `ui_web/README.md`, где web UI помечен как `UNKNOWN_NEEDS_TRACE`.
- Добавлен `automation/state/README.md`, где мартовские automation JSON помечены
  как `HISTORICAL_NEEDS_REVIEW`.
- Обновлен `RUNBOOK.md`: добавлено решение по operator UI authority на
  2026-05-17.
- Обновлен orchestrator state: TASK-20260517-110 закрыта, TASK-20260517-111
  активирована.

## Decisions

- QML desktop остается primary operator UI для текущих Target Lab/operator
  workflows.
- PySide6 widgets остаются active fallback/research surface; на этом шаге они не
  удаляются и не заменяются.
- `ui_web/` не имеет runtime authority до отдельного owner decision и proof
  integration path.
- `automation/state/` — historical evidence, а не текущий источник training
  truth.
- Archive candidates из аудита остаются на месте до proof-table в
  TASK-20260517-111.

## Non-Changes

- Runtime tracker code не менялся.
- Training code не менялся.
- UI implementation code не менялся.
- Файлы не перемещались и не удалялись.
- Detector training не запускался.

## Next Step

Переход к TASK-20260517-111:

1. собрать archive-candidate proof table;
2. определить generated/local artifact ignore policy;
3. держать deletes и physical moves заблокированными до явных owner/risk
   decisions.
