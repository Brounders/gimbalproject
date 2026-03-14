# TASKS.md — Engineering Backlog

## P0 — Immediate (Blockers)

| ID | Description | Risk | Files Affected |
|----|-------------|------|----------------|
| BRIEF-033 | Training strategy reset — dataset composition fix, re-run training cycle | High: model regression if dataset split wrong | `configs/`, `python_scripts/training_helpers.py`, orchestrator brief |

## P1 — Next Sprint

| ID | Description | Risk | Files Affected |
|----|-------------|------|----------------|
| BRIEF-031 | AutoSceneAdapter extraction — currently mutates `cfg` in-place, risky decoupling | High: cfg mutation side-effects must be isolated | `src/uav_tracker/pipeline.py`, new `src/uav_tracker/auto_scene_adapter.py` |
| A10 | Test coverage from ~15% → >30% — add tests for pipeline, config, detectors, target_manager | Medium: test isolation for stateful classes | `tests/`, `src/uav_tracker/pipeline.py`, `src/uav_tracker/config.py`, detectors |
| TASK-033 | Verify APP_STYLESHEET extraction — `app/ui/theme.py` exists; audit whether it's fully used by `main_gui.py` or still has inline remnants | Low | `app/main_gui.py`, `app/ui/theme.py` |
| SCRIPTS-001 | Organize `python_scripts/` into subdirs: `training/`, `evaluation/`, `tools/` — no code changes, just directory structure | Low | `python_scripts/` |

## P2 — Future

| ID | Description | Risk | Files Affected |
|----|-------------|------|----------------|
| BRIEF-030 | Config nested groups — restructure 145-field flat dataclass into grouped sections; breaking API change | High: all callers use `cfg.<field>` flat access | `src/uav_tracker/config.py`, `pipeline.py`, `main_gui.py`, all callers |
| Hailo impl | HailoBackend real implementation for RPi5 — replace stub with actual Hailo SDK calls | High: hardware dependency, platform-specific | `src/uav_tracker/runtime/hailo_backend.py` |
| ROOT-DOC-001 | Root MD proliferation — 12+ MD files at root; consolidate/move to `docs/` without breaking existing references | Low | root `*.md` files |
| MAIN-GUI-001 | Split `app/main_gui.py` (1600 lines) — extract TrackerWorker business logic from UI layer | High | `app/main_gui.py`, new `app/workers/tracker_worker.py` |

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
