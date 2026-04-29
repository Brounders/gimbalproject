# Active Plan

## Plan ID
- AP-20260429-GOVERNANCE

## Source Direction
- Human approved governance restoration + architecture fixes on 2026-04-29.
- Scope: синхронизация источников правды, contracts, pytest fix, pipeline contracts (A1a-A1d).
- RTX/Hailo/новые алгоритмы — вне этого плана (следующий цикл).

## Status
- In Progress

---

## Архив: AP-20260314-027 (CLOSED)

Закрыт на основании REPORT-20260314-087 (committed, ACCEPTED).

| Задача | Статус | Источник |
|--------|--------|----------|
| A01: threading.Event race condition | ✅ DONE | REPORT-087 |
| A02: print() → logging | ✅ DONE | REPORT-087 |
| A03: circular import fix | ✅ DONE | REPORT-087 |
| A05: _iou() → utils/geometry.py | ✅ DONE | REPORT-087 |
| A06: TrackerPipeline docstrings | ✅ DONE | REPORT-087 |
| A07: Kalman vs EMA → ОСТАВИТЬ EMA | ✅ DECIDED | BRIEF-032 |
| A09: Config sections (non-breaking) | ✅ DONE | REPORT-087 |
| A11: try/except UltralyticsBackend | ✅ DONE | REPORT-087 |
| A12: magic numbers → Config | ✅ DONE | REPORT-087 |
| Day gate fix (gt_frames=0 skip) | ✅ DONE | REPORT-087 |
| A08: TrackerPipeline decomposition | ⏳ WORKTREE | REPORT-089 (needs review) |
| A10: тесты >30% | ⏳ WORKTREE | Session 7 (не смержена) |
| Training strategy / dataset audit | ⏳ NEXT CYCLE | OQ-001 |

---

## AP-20260429-GOVERNANCE — Текущий план

### G-фаза — Governance (выполняется сейчас)
- [x] G1: Read-only divergence report (2026-04-29)
- [x] G2a: Canonical state sync — wiki/synthesis/current_state.md обновлён
- [x] G2b: Promotion + dataset contracts (configs/promotion_contract.yaml, dataset_contract.yaml)
- [x] G2c: Worktree classification document + Session Closing Protocol в CLAUDE.md

### A-фаза — Architecture fixes
- [x] **A1a**: DetectionSource enum + pytest conftest (282→304 тесты работают)
- [x] **A1b**: FrameContext dataclass
- [x] **A1c**: RuntimeConfigView — BUG-001 fix (auto-scene не мутирует base Config)
- [x] **A1d**: Config.validate() — raise ValueError, не assert

### Exit Criteria
- [x] wiki/synthesis/current_state.md содержит Canonical Phase Status
- [x] configs/promotion_contract.yaml существует
- [x] configs/dataset_contract.yaml существует
- [x] orchestrator/state/worktree_review.md существует
- [x] pytest запускается без PYTHONPATH вручную (304 тестов)
- [x] DetectionSource enum используется вместо строк
- [x] Config.validate() выбрасывает ValueError при плохих значениях
- [x] RuntimeConfigView заменяет мутацию cfg в auto-scene
- [x] Все изменения закоммичены в main (7 коммитов)
- [x] active_plan.md указывает на следующий implementation цикл

## Следующий цикл — implementation (открыть отдельной сессией)

Governance восстановлен. Следующие задачи в порядке приоритета:

1. **Worktree review** (Human decision needed):
   - `orchestrator/state/worktree_review.md` — решить судьбу UI diff и Session 7 worktree
2. **REPORT-088 commit** — закоммитить untracked dataset audit report
3. **Tracker association A/B** — сравнить ByteTrack vs template lock по id_chg/min
4. **YOLOv11 benchmark** — model intake с SHA + gate против baseline

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.
