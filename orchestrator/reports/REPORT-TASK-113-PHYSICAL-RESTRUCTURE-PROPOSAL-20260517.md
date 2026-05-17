# REPORT-TASK-113-PHYSICAL-RESTRUCTURE-PROPOSAL-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted locally

## Scope

TASK-20260517-113 требовала physical restructure proposal после stages 1-4:

- решить, как подходить к `python_scripts/`, configs, docs/archive и tests;
- не перемещать файлы на этом шаге;
- определить migration order, validation gates и rollback.

## Changes

- Добавлен `docs/PROJECT_PHYSICAL_RESTRUCTURE_PROPOSAL.md`.
- Orchestrator state обновлен: TASK-20260517-113 закрыта.
- Следующим активным шагом выбран TASK-20260514-093 commit boundary review.

## Decision

Физические moves сейчас заблокированы. Правильный порядок:

1. scripts refactor через compatibility wrappers;
2. configs split только после reference map и compatibility loading;
3. archive только после proof + owner decision;
4. automation/state только после refresh/deprecation decision;
5. каждый move отдельным commit с rollback gate.

## Non-Changes

- Файлы не перемещались.
- Файлы не удалялись.
- Runtime/training/UI implementation code не менялся.
- CI не менялся.
- Training не запускался.

## Next Step

TASK-20260514-093 commit boundary review:

- отделить готовые orchestrator/docs commits от локальных/агентских артефактов;
- понять, что можно синхронизировать с RTX и remote;
- не возвращаться к detector/training, пока commit boundary не ясен.
