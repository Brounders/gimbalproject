# REPORT-TASK-111-PROOF-CLEANUP-PLAN-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted locally

## Scope

TASK-20260517-111 требовала proof-based cleanup plan:

- собрать proof-table по archive candidates;
- определить generated/local artifact ignore policy;
- не удалять и не перемещать файлы без owner decision.

## Proof Summary

- `build_mixed_dataset.py` не мертвый: он используется RUNBOOK и long-run
  training shell wrappers.
- `diagnose_ir_hotspot_oracle.py` и `diagnose_ir_sensitivity.py` не имеют
  активных ссылок вне audit/docs; это low-risk archive candidates, но без move на
  этом шаге.
- `monitor_six_hour_session.py` и `summarize_batch_reports.py` пока упомянуты в
  RUNBOOK, поэтому требуют runbook/training-flow cleanup перед архивом.
- `automation/state/*.json` нельзя архивировать вслепую: tooling still depends
  on those paths (`training_conveyor.py`, artifact publish/fetch scripts,
  automation prompts/docs).
- `ui_web/**` остается `UNKNOWN_NEEDS_TRACE`, не archive-now.

## Changes

- Добавлен `docs/PROJECT_STRUCTURE_CLEANUP_POLICY.md`.
- Добавлено `.gitignore` правило `._*` для macOS AppleDouble sidecars.
- Orchestrator state обновлен: TASK-20260517-111 закрыта, TASK-20260517-112
  стала активной.

## Non-Changes

- Файлы не удалялись.
- Файлы не перемещались.
- Runtime/training/UI implementation code не менялся.
- Detector training не запускался.

## Next Step

Переход к TASK-20260517-112:

1. определить unit-test scope для `NightSmallTargetDetector`;
2. определить offscreen PySide6/QML sanity в CI;
3. определить pipeline smoke-test proposal;
4. не менять runtime behavior без отдельного approval.
