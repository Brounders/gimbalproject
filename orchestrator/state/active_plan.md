# Active Plan

## Plan ID
- AP-PHASE2-MODEL-DATASET-INTAKE

## Status
- Completed

## Source Direction
Phase 1 architecture завершена: BUG-004, ARC-001, ARC-002, TEST-001, TD-003.
AP-PHASE2 завершён: проект умеет принимать модель/датасет через формальный gate без ручной возни.
Следующий цикл открывается только после Human approval через Codex-control protocol.

**Strict non-scope for AP-PHASE2:** bird training, Hailo, UI, ByteTrack, thermal YOLO.

---

## Архив: AP-20260429-GOVERNANCE (CLOSED 2026-04-30)

Все exit criteria выполнены: governance restore, contracts, A1a-A1d pipeline contracts, pytest green.

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

---

## AP-20260430-CLEANUP — Текущий план

### Phase 0 Bugs (CLOSED 2026-04-30)

| Баг | Статус |
|-----|--------|
| BUG-001 Auto-scene race | ✅ DONE |
| BUG-002 Reacquire radius cap | ✅ DONE |
| BUG-003 Template lock drift | ✅ DONE |
| BUG-004 MainWindow thread safety | ⏳ **DEFERRED → Phase 1** (не блокирует pipeline) |
| BUG-005 Night grid collision | ✅ DONE |
| BUG-006 Confidence EMA cold-start | ✅ DONE |
| BUG-007 Inference timeout 8.0s | ✅ DONE |
| BUG-008 Typed exceptions | ✅ DONE |

### Cleanup Tasks

- [x] **C1**: antiuav_ir_v1 intake — REPORT-20260430, SHA записан, статус IR_CANDIDATE_HOLD
- [x] **C2**: resolve_model_path — explicit override не подменяется дефолтом
- [x] **C3**: pytest 338/338 green (без PYTHONPATH)
- [x] **C4**: BUG-004 формально DEFERRED → Phase 1
- [x] **C5**: OQ-002 → DEFERRED
- [x] **C6**: wiki/synthesis/current_state.md обновлён (фазы, модели, baseline)
- [x] **C7**: финальный коммит (5912e3b)

### Open Questions

| ID | Статус |
|----|--------|
| OQ-001 | ✅ CLOSED — `configs/dataset_contract.yaml` v1.1 + `python_scripts/dataset_audit.py` |
| OQ-002 | **DEFERRED** — IR bird rejection, не блокирует |
| OQ-003 | ✅ CLOSED — no-GT structural false_lock artifact, gate already protected |
| OQ-004 | ✅ CLOSED — `docs/OPERATOR_BASELINE.md` night_confirm=5 |
| OQ-005 | ✅ CLOSED — `python_scripts/verify_baseline.py` baseline integrity check |

---

## AP-20260430-PHASE1 — Phase 1 Architecture (текущий план)

Сессия 2026-04-30. Коммит: 10480ab.

| Задача | Статус | Примечание |
|--------|--------|------------|
| BUG-004: MainWindow thread safety | ✅ DONE | threading.RLock, one-shot shutdown guard |
| ARC-001: декомпозиция MainWindow | ✅ DONE | 1205 → 683 строк; все build-методы в layout_builders |
| ARC-002: декомпозиция TargetManager | ✅ DONE | FocusModeController; target_manager 434→401 строк |
| TEST-001: coverage → 35% | ✅ DONE | core 52→55% (--cov=src); full 27→29% (--cov=src/uav_tracker --cov=app) |
| TD-003: magic numbers → Config | ✅ DONE | 16 constants, commit 351f1c8, coverage 55% |

---

## AP-PHASE2 — Model & Dataset Intake (текущий план)

Цель: проект умеет принимать новую модель/датасет через формальный gate без ручной возни.

| Задача | Статус | Scope | Acceptance |
|--------|--------|-------|------------|
| **TASK-20260501-090 / MG-001: Единый intake-скрипт** | ✅ DONE | `python_scripts/run_intake.py` | коммит 19f3984; 11 тестов |
| **DG-001: Закрыть OQ-001 dataset spec** | ✅ DONE | `configs/dataset_contract.yaml` v1.1 + `dataset_audit.py` | коммит fde841b; OQ-001 resolved; 15 тестов |
| **OQ-004-fix: night_confirm docs** | ✅ DONE | `docs/OPERATOR_BASELINE.md` | коммит 0dc2319; OQ-004 закрыт |
| **OQ-003-diag: day false_lock=1.000** | ✅ DONE | диагностика | коммит dbd0b84; структурный артефакт, gate уже защищён; OQ-003 закрыт |
| **OQ-005: baseline verification** | ✅ DONE | `python_scripts/verify_baseline.py` | коммит cbb01c8; baseline integrity check |

### Execution Order

1. MG-001
2. DG-001
3. OQ-004-fix
4. OQ-003-diag

### Guardrails

- Не начинать training.
- Не менять model baseline.
- Не менять runtime thresholds без explicit Human approval.
- Не исправлять OQ-003 в диагностической задаче.
- Не выходить за текущую задачу из таблицы AP-PHASE2.

---

## Active Claude Tasks (execution allowed now)
(none)

## Active RTX Tasks (execution allowed now)
(none)

---

## Backlog Policy
Задачи вне списков выше — backlog. Не исполняются без явного Human запроса.
