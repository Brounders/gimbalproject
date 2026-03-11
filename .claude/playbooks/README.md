# Claude Playbooks

Этот каталог задает для Claude проектные навыки в виде playbooks.

Принцип работы:
- Claude не ждет явного имени playbook от Human.
- Claude сначала читает `CLAUDE.md` и использует авто-маршрутизацию по смыслу задачи.
- Если формулировка Human совпадает с одним из типов задач ниже, Claude обязан открыть соответствующий playbook перед началом работы.

Доступные playbooks:
- `router.md` — карта соответствия естественного языка Human и рабочего playbook.
- `orchestrator.md` — работа по `active_plan`, task/report review, orchestration state.
- `rtx_intake.md` — разбор статусов RTX, epoch accounting, resume/exit diagnostics.
- `quality_gate.md` — benchmark, KPI, baseline vs candidate, PASS/FAIL/RETUNE.
- `training_ops.md` — подготовка/контроль training cycle, термобезопасность, resume continuity.
- `pyside6_ui.md` — безопасная работа с desktop UI на PySide6.
