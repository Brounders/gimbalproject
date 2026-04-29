# TASKS.md — Engineering Backlog

## P0 — Immediate (Blockers)

| ID | Description | Risk | Files Affected |
|----|-------------|------|----------------|
| BRIEF-033 | **Phase A DONE ✅. Phase B — BLOCKED (2026-03-17, Agent-2 audit).** Critical blocker: все доступные датасеты содержат только дроны — antiuav (nc=1, drone-only), drone-bird-yolo (185.8:1), mendeley_ir пути указывают на Desktop (broken). Training reset без bird-примеров не решит регрессию. build_mixed_dataset.py не поддерживает >2 источника и не умеет class weighting. **REQUIRED BEFORE PHASE B (Bround action):** переместить `drone_bird_mendeley_ir_mix_v1` из Desktop → в проект ИЛИ найти альтернативный bird YOLO датасет (nc=2). После восстановления bird-данных: (1) конвертировать antiuav YAML nc=1→2, (2) пересчитать --night-multiplier. drone_closeup_mixkit GT — NON-BLOCKER (day false_lock пропускается). | Phase B: BLOCKED / Phase E: HIGH | `datasets/drone_bird_mendeley_ir_mix_v1/` (broken paths → Desktop), `datasets/antiuav_rgbt_ir_yolo/` (nc=1 несовместим), `python_scripts/build_mixed_dataset.py` |

## P1 — Next Sprint

| ID | Description | Risk | Files Affected |
|----|-------------|------|----------------|
| BRIEF-031 | AutoSceneAdapter extraction — BLOCKER: (1) file doesn't exist, requires NEW class creation not file move; (2) method mutates 5 cfg fields in-place (`CONF_THRESH`, `NIGHT_MOT_THRESH`, `NIGHT_DIFF_THRESH`, `LOCK_CONFIRM_FRAMES`, `DRONE_LOCK_SCORE_MIN`) affecting NightDetector/TargetManager/LockTracker downstream; (3) 0% test coverage — no regression safety net; (4) interface design unresolved (pass cfg ref vs return override dict) | High: cfg mutation pattern must be resolved before extraction | `src/uav_tracker/pipeline.py:190-283`, new `src/uav_tracker/pipeline_control/auto_scene_adapter.py` |
| A10 | Test coverage → **SUBSTANTIALLY COMPLETE** ✅. 282 tests total (was 48). Cycles: C1 DisplayStateTracker +21, C2 config.py +67, C3 TargetManager lifecycle +37, C4 profile_io blocked→deferred, C5 modes.py +58, C6 profile_io +51. Remaining: detectors (cv2 — permanently deferred), overlay.py (cv2 — deferred) | Medium | All new test files committed. Suite: 282/282 OK |
| SCRIPTS-001 | Phase 1 DONE ✅ (commit 27b1616). **Phase 2 — DEFERRED (HIGH risk, re-classified 2026-03-15).** Agent-2 audit found: 21 files to move, 3 shell scripts × 22 hardcoded refs, RUNBOOK.md × 46 refs (not 13 as estimated). Any partial update breaks launch scenarios. Checklist required: (1) `run_dataset_batch.py:12` path, (2) .sh scripts 22 refs, (3) RUNBOOK.md 46 refs. Do not attempt without dedicated checklist task. | High (Phase 2) | Phase 2: `python_scripts/*.sh` (22 refs), `run_dataset_batch.py:12`, `RUNBOOK.md` (46 refs), orchestrator docs |

## P2 — Future

| ID | Description | Risk | Files Affected |
|----|-------------|------|----------------|
| BRIEF-030 | Config nested groups — restructure 145-field flat dataclass into grouped sections; breaking API change | High: all callers use `cfg.<field>` flat access | `src/uav_tracker/config.py`, `pipeline.py`, `main_gui.py`, all callers |
| Hailo impl | HailoBackend real implementation for RPi5 — replace stub with actual Hailo SDK calls | High: hardware dependency, platform-specific | `src/uav_tracker/runtime/hailo_backend.py` |
| ROOT-DOC-001 | **ROOT-DOC-001a DONE ✅** (commit f9d7080): `PROJECT_COMPASS.md`, `ENGINEERING_CODEX.md`, `ENGINEERING_DECISIONS.md` → `docs/philosophy/`. Ссылки в AGENTS.md + CODEX_ROLE.md обновлены. **`DEVELOPMENT_NEXT_STEPS.md` удалён ✅** (commit 81127b7, ephemeral, 0 functional refs). **ROOT-DOC-001b DEFERRED** — RUNBOOK.md (51 refs), OPERATOR_BASELINE.md (135 refs), PROJECT_ARCHITECTURE.md (294 refs) остаются в root. | Medium (ROOT-DOC-001b) | root: 9 files remain; `docs/philosophy/`: 3 files moved |
| MAIN-GUI-001 | Split `app/main_gui.py` (1600 lines) — extract TrackerWorker business logic from UI layer | High | `app/main_gui.py`, new `app/workers/tracker_worker.py` |
| DISP-001..003 | ~~Display cluster moves~~ — COMPLETED | — | — |

---

## Completed

| ID | Description |
|----|-------------|
| A01 | Race condition fix in TrackerWorker — QMutex for control flags (`app/main_gui.py:74-75`) |
| A02 | `print()` → `logging` in `pipeline.py` run_tracker (lines 1003, 1032, 1045, 1052-1066) |
| A03 | Fix overlay import at end of `pipeline.py:973` — resolve circular import, move to top |
| A04 | HailoBackend documented as placeholder with clear TODOs |
| A05 | `_iou()` extracted to `src/utils/geometry.py`, duplicates removed from pipeline/target_manager/roi_assist |
| A06 | Docstrings added to TrackerPipeline and public methods |
| A07 | (reserved) |
| A08 (stage 1) | TrackerPipeline decomposition — BudgetController extracted |
| A08 (stage 2) | TrackerPipeline decomposition — ContinuityTracker extracted |
| A08 (stage 3) | TrackerPipeline decomposition — TrackingStateMachine extracted |
| A08 (stage 4) | TrackerPipeline decomposition — DisplayStateTracker extracted |
| A08 (stage 5) | TrackerPipeline decomposition — LockEventTracker extracted |
| A09 | Config structuring — 145 parameters annotated into logical sections (comments) |
| A10 | (partial) Initial test expansion |
| A11 | try/except added to UltralyticsBackend track_frame and predict_frame |
| A12 | Magic numbers in night_detector.py and roi_assist.py → Config fields |
| Phase 2 gate fix | Quality gate regression pack — IR GT clips integration and PASS/FAIL exit code fix |
| .ai init | Created `.ai/` folder with CLAUDE.md, MEMORY.md, ARCHITECTURE_MAP.md, TASKS.md, CONTEXT7_GUIDE.md |
| TRACK-000 | `lock_event_tracker.py` → `tracking/` subpackage |
| TRACK-001 | `continuity_tracker.py` → `tracking/` subpackage |
| TRACK-002 | `tracking_state_machine.py` → `tracking/` subpackage |
| PCTL-001 | Создан `pipeline_control/` + `budget_controller.py` перемещён туда |
| DISP-001 | `display_state_tracker.py` → `display/` subpackage |
| DISP-002 | `frame_result.py` → `display/` subpackage |
| DISP-003 | `overlay.py` → `display/` subpackage |
| TASK-033 | theme.py audit — COMPLETE: `theme.py` is sole source of truth, 0 inline styles in `main_gui.py` |

---

## Architectural Safety Classification

### Completed cluster moves (as of 2026-03-14)
- TRACK-000/001/002: `tracking/` subpackage — DONE (lock_event_tracker, continuity_tracker, tracking_state_machine)
- PCTL-001: `pipeline_control/` subpackage — DONE (budget_controller)
- DISP-001/002/003: `display/` subpackage — DONE (display_state_tracker, frame_result, overlay)

### Ready NOW (recommended next)
- SCRIPTS-001 Phase 1: `python_scripts/training/`, `evaluation/`, `tools/` dirs — LOW risk, mkdir only

### Deferred (requires caller audit or design decision)
- SCRIPTS-001 Phase 2: file moves + path fixes — MEDIUM risk, separate task
- ROOT-DOC-001: root MD consolidation (risk: external references)
- BRIEF-031: AutoSceneAdapter extraction — HIGH risk, cfg-mutation interface unresolved

### Blocked (breaking API or deep coupling)
- BRIEF-030: Config nested groups (145 callers)
- MAIN-GUI-001: main_gui.py split (QThread lifecycle coupling)
- Hailo: platform-specific, hardware dependency
