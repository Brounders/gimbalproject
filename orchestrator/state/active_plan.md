# Active Plan

## Plan ID
- AP-MODERNITY-GAP

## Status
- Completed

## Source Direction
Human approved the modernity-gap plan and started execution on 2026-05-01.
Cycle completed as measurement/decision audit only: runtime code, baseline, thresholds, training, and UI were not changed.
Цикл должен определить, насколько современно построены основные механизмы трекинга, модели, ночного обнаружения, оценки качества и отображения.

**Строго вне рамок AP-MODERNITY-GAP:** Hailo, Raspberry Pi, внедрение новых зависимостей, продвижение новой модели в baseline, изменение runtime thresholds, обучение, крупный рефакторинг без отдельного подтверждения.

**Правила отчётов для этого и следующих циклов:**
- Заголовки разделов писать по-русски.
- Объяснения писать по-русски; имена файлов, API и кода оставлять на английском.
- Сводить к минимуму непонятные английские термины; если термин нужен, сразу пояснять его по-русски.
- Hailo/Raspberry не включать в отчёты и планы до отдельной команды Human.

## AP-MODERNITY-GAP — аудит современности трекинга и модели

### Цель

Сравнить текущий GimbalProject с актуальным путём Ultralytics и определить, какие механизмы:

- оставить как есть;
- измерить глубже;
- заменить современным способом;
- не трогать без новых контрольных доказательств.

### Задачи

| ID | Задача | Статус | Результат |
|----|--------|--------|-----------|
| MGAP-001 | Сравнить штатные трекеры Ultralytics | ✅ DONE | Full `ByteTrack`, `BoT-SORT`, `BoT-SORT + ReID` measured; none can replace self-hold |
| MGAP-002 | Разобрать самописные механизмы трекинга | ✅ DONE | `TargetManager`/`TemplateLockTracker` оставить; `NightSmallTargetDetector` признан главным modernity gap |
| MGAP-003 | Обновить модельный путь | ✅ DONE | `YOLO26n` — следующий candidate-only benchmark; baseline не менять |
| MGAP-004 | Оценить визуальное отставание | ✅ DONE | UI gap отделён от algorithm gap; не смешивать с tracking decisions |
| MGAP-005 | Сформировать матрицу решений | ✅ DONE | См. `orchestrator/reports/REPORT-MODERNITY-GAP-20260501.md` |

### Порядок работы

1. Сначала восстановить актуальное состояние: git, `active_plan.md`, отчёты, wiki.
2. Прочитать локальный Ultralytics route:
   - `../wiki/sources/ultralytics_site_map.md`
   - `../wiki/sources/ultralytics_yolo.md`
3. Проверить свежую документацию Ultralytics только по нужным разделам.
4. Не начинать переписывание кода.
5. Сначала собрать измерения и таблицу решений.
6. После таблицы решений запросить Human approval на конкретный следующий эксперимент.

### Ожидаемый итог

Документ-решение по современности проекта:

- где мы уже используем актуальный путь;
- где у нас полезная самописная логика;
- где у нас технический долг;
- какие 1-2 эксперимента дадут максимальный прирост без риска сломать ночной gate.

### Итог

Отчёт: `orchestrator/reports/REPORT-MODERNITY-GAP-20260501.md`.

Решение:
- не заменять текущий project pipeline на native ByteTrack-only, `BoT-SORT`, or `BoT-SORT + ReID`;
- не удалять `TemplateLockTracker`, пока replacement не докажет night gate PASS;
- считать `YOLO26` актуальным направлением для candidate experiments;
- считать `NightSmallTargetDetector` главным modernity gap, но не менять его без dataset/model cycle;
- ближайший безопасный эксперимент: `YOLO26n` candidate-only benchmark.

---

## Архив: AP-20260501-BYTETRACK-EVAL (CLOSED 2026-05-01)

Human approved option B: ByteTrack / Ultralytics tracking evaluation.
Цикл выполнен как measurement-only: runtime thresholds, baseline, GUI и lock policy не менялись.

**Strict non-scope for AP-20260501-BYTETRACK-EVAL:** baseline promotion, runtime threshold changes, GUI changes, training, detector replacement.

## AP-20260501-BYTETRACK-EVAL — ByteTrack / Ultralytics Tracking Evaluation

Цель: дать безопасный способ сравнивать текущий project pipeline с native Ultralytics tracking (`bytetrack.yaml` / `botsort.yaml`) на тех же клипах и preset-ах.

| Задача | Статус | Scope | Acceptance |
|--------|--------|-------|------------|
| **TE-001: Standalone tracking-eval script** | ✅ DONE | `python_scripts/run_ultralytics_tracking_eval.py` | measurement-only JSON/CSV, no runtime changes |
| **TE-002: Helper unit tests** | ✅ DONE | `tests/test_ultralytics_tracking_eval.py` | pure helper coverage, no YOLO inference in unit tests |
| **TE-003: Smoke measurement** | ✅ DONE | `configs/regression_pack_night.csv`, `max_frames=5` | script runs native `bytetrack.yaml` and writes artifacts |

### Key Findings

- `src/uav_tracker/runtime/ultralytics_backend.py` already uses `tracker='bytetrack.yaml'` for `track_frame()`.
- Current project pipeline is not pure native ByteTrack: it combines Ultralytics track IDs with `TargetManager`, template lock, ROI assist, night detector, and lock policy.
- Evaluation should therefore compare project pipeline metrics against native Ultralytics tracker metrics, not treat ByteTrack as absent.

### Generated Smoke Artifacts

- `runs/evaluations/ultralytics_tracking/smoke_tracking_eval_night_bytetrack.json`
- `runs/evaluations/ultralytics_tracking/smoke_tracking_eval_night_bytetrack.csv`

### Exit Criteria

- [x] Official/current Ultralytics tracking API checked through Context7.
- [x] Local Ultralytics wiki route read before implementation.
- [x] Runtime code untouched.
- [x] Standalone script supports `--tracker bytetrack|botsort`.
- [x] Validation commands pass.

---

## Архив: AP-PHASE2-MODEL-DATASET-INTAKE (CLOSED 2026-05-01)

Phase 1 architecture завершена: BUG-004, ARC-001, ARC-002, TEST-001, TD-003.
AP-PHASE2 завершён: проект умеет принимать модель/датасет через формальный gate без ручной возни.
Следующий цикл был открыт после Human approval через Codex-control protocol.

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
