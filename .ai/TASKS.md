# TASKS.md — Engineering Backlog

## P0 — Immediate (Blockers)

| ID | Description | Risk | Files Affected |
|----|-------------|------|----------------|
| BRIEF-033 | Training strategy reset — dataset composition fix, re-run training cycle | High: model regression if dataset split wrong | `configs/`, `python_scripts/training_helpers.py`, orchestrator brief |

## P1 — Next Sprint

| ID | Description | Risk | Files Affected |
|----|-------------|------|----------------|
| BRIEF-031 | AutoSceneAdapter extraction — BLOCKER: (1) file doesn't exist, requires NEW class creation not file move; (2) method mutates 5 cfg fields in-place (`CONF_THRESH`, `NIGHT_MOT_THRESH`, `NIGHT_DIFF_THRESH`, `LOCK_CONFIRM_FRAMES`, `DRONE_LOCK_SCORE_MIN`) affecting NightDetector/TargetManager/LockTracker downstream; (3) 0% test coverage — no regression safety net; (4) interface design unresolved (pass cfg ref vs return override dict) | High: cfg mutation pattern must be resolved before extraction | `src/uav_tracker/pipeline.py:190-283`, new `src/uav_tracker/pipeline_control/auto_scene_adapter.py` |
| A10 | Test coverage from ~15% → >30% — add tests for pipeline, config, detectors, target_manager | Medium: test isolation for stateful classes | `tests/`, `src/uav_tracker/pipeline.py`, `src/uav_tracker/config.py`, detectors |
| TASK-033 | Verify APP_STYLESHEET extraction — `app/ui/theme.py` exists; audit whether it's fully used by `main_gui.py` or still has inline remnants | Low | `app/main_gui.py`, `app/ui/theme.py` |
| SCRIPTS-001 | Organize `python_scripts/` into subdirs: `training/`, `evaluation/`, `tools/` — no code changes, just directory structure | Low | `python_scripts/` |
| TRACK-001 | Move `continuity_tracker.py` → `tracking/` — zero internal imports, 2 callers | Low | 2 import lines, 1 file move |
| TRACK-002 | Move `tracking_state_machine.py` → `tracking/` — zero internal imports, 2 callers | Low | 2 import lines, 1 file move |
| PCTL-001 | Create `pipeline_control/` subpackage, move `budget_controller.py` | Low | 2 import lines, 1 file move |

## P2 — Future

| ID | Description | Risk | Files Affected |
|----|-------------|------|----------------|
| BRIEF-030 | Config nested groups — restructure 145-field flat dataclass into grouped sections; breaking API change | High: all callers use `cfg.<field>` flat access | `src/uav_tracker/config.py`, `pipeline.py`, `main_gui.py`, all callers |
| Hailo impl | HailoBackend real implementation for RPi5 — replace stub with actual Hailo SDK calls | High: hardware dependency, platform-specific | `src/uav_tracker/runtime/hailo_backend.py` |
| ROOT-DOC-001 | Root MD proliferation — 12+ MD files at root; consolidate/move to `docs/` without breaking existing references | Low | root `*.md` files |
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

---

## Architectural Safety Classification

### Safe NOW (low risk, < 3 import changes each)
- TRACK-001, TRACK-002: move tracking components into tracking/
- PCTL-001: move budget_controller into pipeline_control/

### Deferred (requires caller audit first)
- DISP-001..003: display cluster (overlay.py has GUI callers)
- ROOT-DOC-001: root MD consolidation (risk: external references)

### Blocked (breaking API or deep coupling)
- BRIEF-030: Config nested groups (145 callers)
- MAIN-GUI-001: main_gui.py split (QThread lifecycle coupling)
- Hailo: platform-specific, hardware dependency
