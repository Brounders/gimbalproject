# Project Structure Cleanup Policy

Дата статуса: 2026-05-17

Этот документ фиксирует правила TASK-20260517-111: что можно чистить сразу, что
можно только игнорировать, а что требует отдельного owner/risk decision. Это не
план физического перемещения файлов.

## Правила

- Не удалять и не перемещать source/runtime/training scripts без proof-table.
- Если файл используется shell wrapper, RUNBOOK, automation prompt или state
  script, он не является мертвым.
- Generated/local artifacts должны попадать в `.gitignore`, а не в историю git.
- Historical evidence можно архивировать только после решения владельца и
  проверки, что активные скрипты его не читают.

## Archive-Candidate Proof Table

| Path | Evidence | Решение TASK-111 |
|------|----------|------------------|
| `python_scripts/build_mixed_dataset.py` | Есть ссылки в `RUNBOOK.md` и трех `run_six_hour_training_*.sh` wrappers. | Не архивировать сейчас. Это legacy-active dependency; сначала нужен replacement/RTX workflow decision. |
| `python_scripts/diagnose_ir_hotspot_oracle.py` | Активных ссылок вне audit/docs не найдено. | Candidate archive, low risk, но move только после owner approval. |
| `python_scripts/diagnose_ir_sensitivity.py` | Активных ссылок вне audit/docs не найдено. | Candidate archive, low risk, но move только после owner approval. |
| `python_scripts/monitor_six_hour_session.py` | Есть ссылка в `RUNBOOK.md` как monitoring utility. | Не архивировать до обновления training runbook. |
| `python_scripts/summarize_batch_reports.py` | Есть ссылка в `RUNBOOK.md` как batch-report summary. | Candidate archive после proof, что batch reports больше не используются. |
| `automation/state/*.json` | Активные ссылки есть в `training_conveyor.py`, `publish_training_artifact.py`, `fetch_training_artifact.py`, `automation/README.md`, prompts и architecture docs. | Не архивировать сейчас. Статус: historical data with active tooling dependency. Нужен refresh или explicit deprecation. |
| `ui_web/**` | Buildable React/Vite project, но runtime/operator integration не доказан. | Не архивировать сейчас. Статус: `UNKNOWN_NEEDS_TRACE`; решение переносится в TASK-113. |

## Generated/Local Artifact Policy

Уже закрыто в `.gitignore`:

- `.DS_Store`;
- `__pycache__/` и `*.pyc`;
- `tracker_env/`;
- `datasets/`;
- `runs/`;
- `logs/`;
- `ui_web/node_modules/` и `ui_web/dist/`;
- model binaries и local import/export/safety artifacts;
- local agent/worktree/memory/design directories.

Добавлено в TASK-111:

- `._*` — macOS AppleDouble sidecars. Это напрямую снижает шум от RTX/Mac sync,
  где такие файлы давали сотни untracked entries.

Не менять сейчас:

- `automation/state/*.json`, кроме уже игнорируемого
  `automation/state/next_training_chunk.json`;
- `models/baseline_manifest.json`;
- orchestrator reports/state;
- source scripts, tests, configs and docs.

## Next Decisions

1. Обновить RUNBOOK training section: отделить legacy six-hour flow от текущего
   bounded RTX smoke/training contract.
2. После обновления runbook вернуться к `monitor_six_hour_session.py` и
   `summarize_batch_reports.py`.
3. Для двух IR diagnose scripts принять owner decision: оставить как research
   tools или перенести в future archive.
4. Для `automation/state` выбрать: refresh current RTX schema или deprecate as
   historical evidence.
