# Worktree Review — 2026-04-29

Создан в G1 read-only audit. Только классификация.
Никаких git-операций не выполнялось. Все решения требуют явного Human approval.

---

## Модифицированные файлы (tracked, uncommitted)

| Файл | Изменение | Источник | Классификация | Решение | Статус |
|------|-----------|----------|---------------|---------|--------|
| `app/main_gui.py` | +467 строк | Session 10, UI редизайн | UI diff | Review required | ⏳ pending |
| `app/ui/theme.py` | +748 строк | Session 10, glass design | UI diff | Review required | ⏳ pending |
| `python_scripts/run_quality_gate.py` | +6 строк | Session 8, `--context` flag | Feature addition | Likely ACCEPT | ⏳ pending |
| `.ai/TASKS.md` | +6 строк | Неизвестно | Minor update | Likely ACCEPT | ⏳ pending |

---

## Untracked файлы

| Файл/Директория | Источник | Классификация | Решение | Статус |
|------|---------|---------------|---------|--------|
| `orchestrator/reports/REPORT-20260314-088-dataset-audit.md` | Session 8 | Report not committed | **COMMIT** | ⏳ pending |
| `orchestrator/reports/REPORT-agent-team-audit-20260314.md` | agent-team | Agent-team audit report | Review required | ⏳ pending |
| `models/anti_uav_night_v5.onnx` | Session 9, Path A (провален) | Abandoned experiment artifact | Likely DELETE | ⏳ pending |
| `models/anti_uav_night_v5.onnx.data` | Session 9, Path A (провален) | Abandoned experiment artifact | Likely DELETE | ⏳ pending |
| `configs/night_yolov5.yaml` | Session 9, Path A | Config заброшенного пути | Likely DELETE | ⏳ pending |
| `"Gimbal design/"` | Session 10 | UI reference materials | Keep/ignore | ⏳ pending |
| `memory/claude-memory-compiler/` | Tool infrastructure | Memory system | Keep/ignore | ⏳ pending |
| `.claire/` | Unknown | Unknown tool | Review required | ⏳ pending |
| `.obsidian/` | Obsidian vault | Wiki tool | Keep/ignore | ⏳ pending |
| `.claude/worktrees/` | Claude worktree dirs | Tool infrastructure | Keep/ignore | ⏳ pending |

---

## UI Diff — Отдельный Review Item

**Ветка:** `claude/inspiring-agnesi-c7897f` (Session 10 work)
**Файлы:** `app/main_gui.py` (+467), `app/ui/theme.py` (+748)
**Описание:** 3-колоночный layout, TopBar pill, Dock pill, glass design токены
**Статус сессии:** структурно правильно, визуально не совпадает с референсом
**Решение не принято:** Path A (точно повторить референс) vs Path B (только стиль)

> Эти файлы НЕ входят в governance-коммиты G2a/G2b/G2c.
> Human решает судьбу UI diff отдельно.

---

## Worktrees с незамерженной работой

| Ветка | Сессия | Содержимое | Статус |
|-------|--------|------------|--------|
| `elastic-hawking-25f3dd` | Session 7 | Рефакторинг: MainWindow decomposition, 338 тестов, coverage 51% | ⚠️ NOT MERGED |
| `claude/inspiring-agnesi-c7897f` | Session 10 | UI редизайн | ⚠️ NOT MERGED |

> Работа в этих ветках была задекларирована как выполненная в project_state.md,
> но в main ветке отсутствует. Это основная причина расхождений (G1 audit).

---

## Actions Required (Human approval needed)

- [ ] **REPORT-088**: закоммитить untracked report (`git add orchestrator/reports/REPORT-20260314-088-dataset-audit.md`)
- [ ] **UI diff**: принять решение Path A / Path B / abandon
- [ ] **Session 7 worktree**: смержить в main или закрыть как abandoned
- [ ] **Onnx артефакты**: удалить `models/anti_uav_night_v5.onnx*` и `configs/night_yolov5.yaml` если Path A окончательно заброшен
- [ ] **run_quality_gate.py +6**: проверить и принять изменение
- [ ] **REPORT-agent-team-audit**: прочитать и дать статус
