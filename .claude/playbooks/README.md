# Claude Playbooks

Этот каталог задает для Claude проектные навыки в виде playbooks.

Принцип работы:
- Claude сначала следует `CLAUDE.md` и текущему Codex/Human prompt.
- Playbooks не читаются при старте по умолчанию.
- Playbook открывается только если prompt явно просит это сделать, либо если задача является active-plan/orchestrator задачей без достаточного scope.
- Если prompt уже содержит точный bounded scope, playbook не нужен.

Доступные playbooks:
- `router.md` — карта соответствия естественного языка Human и рабочего playbook.
- `orchestrator.md` — работа по `active_plan`, task/report review, orchestration state.
- `rtx_intake.md` — разбор статусов RTX, epoch accounting, resume/exit diagnostics.
- `quality_gate.md` — benchmark, KPI, baseline vs candidate, PASS/FAIL/RETUNE.
- `training_ops.md` — подготовка/контроль training cycle, термобезопасность, resume continuity.
- `pyside6_ui.md` — безопасная работа с desktop UI на PySide6.
