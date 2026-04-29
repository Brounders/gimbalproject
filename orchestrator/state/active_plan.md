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
- [ ] G2b: Promotion + dataset contracts
- [ ] G2c: Worktree classification document

### A-фаза — Architecture fixes
- [ ] **A1a**: DetectionSource enum + pytest PYTHONPATH fix
- [ ] **A1b**: FrameContext dataclass
- [ ] **A1c**: RuntimeConfigView (BUG-001 архитектурное закрытие)
- [ ] **A1d**: Config.validate() — raise ValueError, не assert

### Exit Criteria
- [ ] wiki/synthesis/current_state.md содержит Canonical Phase Status
- [ ] configs/promotion_contract.yaml существует
- [ ] configs/dataset_contract.yaml существует
- [ ] orchestrator/state/worktree_review.md существует
- [ ] pytest запускается без PYTHONPATH вручную
- [ ] DetectionSource enum используется вместо строк
- [ ] Config.validate() выбрасывает ValueError при плохих значениях
- [ ] RuntimeConfigView заменяет мутацию cfg в auto-scene
- [ ] Все изменения в одной ветке, закоммичены
- [ ] active_plan.md указывает на следующий implementation цикл

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.
