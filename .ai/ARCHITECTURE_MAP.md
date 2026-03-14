# Architecture Map — GimbalProject

## System Overview

Real-time UAV tracking system using YOLOv8 inference + template lock + motion detection.
Runs on Mac M1 (MPS, Ultralytics) and RPi5+Hailo (stub backend).
Pipeline processes video frames through detection, tracking, and display layers.
GUI layer (PySide6) runs pipeline in a background QThread with stop/switch signals.

---

## Architectural Zones

| Zone | Directory | Responsibility |
|---|---|---|
| core | `src/uav_tracker/` | Pipeline, config, detectors, tracking logic |
| app | `app/` | Entry points, GUI main, worker threads |
| ui | `app/ui/` | PySide6 panels, state machine, video stage |
| integrations | `src/uav_tracker/runtime/` | DetectorBackend: Ultralytics, Hailo (stub) |
| shared | `src/uav_tracker/` | overlay.py, frame_result.py, geometry.py |
| tests | `tests/` | unittest suite (~48 tests, ~15% coverage) |
| ai-memory | `.ai/` | Architectural snapshots, agent memory |
| orchestrator | `orchestrator/` | Task plans, reports, agent team state |

---

## Data Flow

```
VideoSource
  └─► VideoSession.read()
        └─► TrackerPipeline.process_frame()
              ├─► [GlobalScan]    backend.predict_frame()
              │                   └─► TargetManager.update_from_yolo()
              ├─► [LockTrack]     lock_tracker.track()
              │                   └─► TargetManager update
              ├─► [LocalValidate] backend.predict_crops()
              │                   └─► TargetManager update
              ├─► [ROIAssist]     roi.propose() → backend.predict_crops()
              │                   └─► TargetManager update
              ├─► [NightDetect]   night.detect()
              │                   └─► TargetManager.update_from_night()
              ├─► TargetManager.age_targets() → select_active() → update_focus_mode()
              ├─► LockEventTracker.update()
              ├─► TrackingStateMachine.update()
              ├─► DisplayStateTracker.update_*()
              ├─► BudgetController.update()
              └─► draw_frame() → FrameOutput
```

---

## TrackerPipeline Components

| Component | Class | Responsibility |
|---|---|---|
| `self.manager` | `TargetManager` | Multi-target lifecycle, ID assignment, age-out |
| `self.backend` | `DetectorBackend` | YOLO inference abstraction (Ultralytics / Hailo) |
| `self.lock_tracker` | `TemplateLockTracker` | Template matching for locked target |
| `self.night` | `NightSmallTargetDetector` | MOG2 motion-based night detection |
| `self.roi` | `MotionROIProposer` | Motion-based crop region proposals |
| `self.budget` | `BudgetController` | CPU load EMA, adaptive scan intervals |
| `self.continuity` | `ContinuityTracker` | Target ID continuity metrics |
| `self.tracking_sm` | `TrackingStateMachine` | SCAN / TRACK / LOST FSM |
| `self.display_state` | `DisplayStateTracker` | Visual smoothing (confidence, reticle, bbox) |
| `self.lock_telemetry` | `LockEventTracker` | ACQUIRE / LOST / SWITCH / REACQUIRED events |

Note: `AutoSceneAdapter` logic is still inline in `pipeline.py` — pending extraction (BRIEF-031).

---

## Config System

- `Config` dataclass: **145 flat fields**, 10 logical sections.
- Sections: Source/Runtime, Model, AdaptiveScan, LockTracker, ROI, Budget, Tracking/Lock, NightDetector, Display/Overlay, AutoScene, BboxSmoothing.
- Fields: `UPPER_SNAKE_CASE`. No magic numbers in logic — all referenced via `cfg.*`.
- Breaking API change required for nested groups (BRIEF-030, deferred).

---

## Architectural Risks

1. `AutoSceneAdapter` inline in `pipeline.py` — mutates `cfg` directly, no isolation boundary.
2. `app/main_gui.py` monolith (~1600 lines) — UI logic and business logic mixed in one file.
3. `hailo_backend.py` is a stub — no real RPi5/Hailo integration implemented.
4. `Config` has 145 flat fields — restructuring to nested groups is a breaking API change.
5. Test coverage ~15% — insufficient for safe refactoring of core pipeline.

---

## Module Dependencies

```
pipeline.py         → target_manager, lock_tracker, night_detector, roi_assist,
                      runtime/backends, overlay, frame_result, config, modes
target_manager.py   → config, geometry
overlay.py          → frame_result, config          (no pipeline import — A03 fixed)
app/main_gui.py     → pipeline, config, evaluation, profile_io, ui/*
runtime/ultralytics → config, torch/ultralytics
runtime/hailo       → config (stub only)
tests/*             → src/uav_tracker/* (PYTHONPATH=src required)
```

---

## Target Feature Architecture

### Current vs Target Mapping

| Cluster | Current Location | Target Subpackage | Status |
|---------|-----------------|-------------------|--------|
| Detection | `detectors/` | `detectors/` | ✅ Already grouped |
| Tracking | `tracking/` | `tracking/` | ✅ Complete (5 files) |
| Pipeline Control | `pipeline_control/` | `pipeline_control/` | 🔄 Partial (budget_controller done; auto_scene_adapter pending BRIEF-031) |
| Display | root (flat) | `display/` | Planned |
| Config | root (flat) | keep flat or `config/` | Risk: breaking imports |
| Integrations | `runtime/` | `runtime/` | Already grouped |

### Files per Cluster

| Cluster | Files |
|---------|-------|
| Detection | `detectors/night_detector.py`, `detectors/roi_assist.py` |
| Tracking | `tracking/target_manager.py`, `tracking/lock_tracker.py`, `tracking/lock_event_tracker.py`, `tracking/tracking_state_machine.py`*, `tracking/continuity_tracker.py`* |
| Pipeline Control | `budget_controller.py`* → `pipeline_control/budget_controller.py` |
| Display | `display_state_tracker.py`*, `overlay.py`*, `frame_result.py`* → `display/` |
| Config | `config.py`, `profile_io.py`, `modes.py` (keep flat — imported broadly) |
| Coordinator | `pipeline.py` (stays at root, imports all clusters) |

*items with asterisk = planned moves, not yet executed

### Risk Assessment

| Change | Risk | Blocker |
|--------|------|---------|
| Move files into tracking/ | Low | 2-3 import lines per file |
| Move files into pipeline_control/ | Low | ~3-5 import lines |
| Move files into display/ | Medium | overlay.py imported by many callers |
| Move config.py | High | 145+ callers, breaking change |
| Split main_gui.py | High | UI+worker coupling, QThread lifecycle |

---

## Full Repository Layout (key directories)

| Directory | Purpose | AI-Zone |
|-----------|---------|---------|
| `src/uav_tracker/` | Core tracker pipeline and components | core |
| `src/utils/` | Shared math utilities (iou, geometry) | shared |
| `app/` | GUI entry point, CLI entry point | app |
| `app/ui/` | PySide6 panels, theme, state machine | ui |
| `tests/` | Unit test suite (48 tests, ~15% coverage) | tests |
| `configs/` | Preset YAMLs, regression packs | shared/config |
| `python_scripts/` | Training, evaluation, benchmarking scripts | tooling |
| `datasets/` | Training datasets (should be in .gitignore) | data |
| `automation/` | AI workflow prompts + state JSONs | orchestrator |
| `orchestrator/` | Active plan, reports, briefs for agent team | orchestrator |
| `arduino_sketches/` | Hardware gimbal control firmware (C++) | hardware |
| `agents/` | Agent team role definitions | ai-memory |
| `.ai/` | AI-native memory and architectural snapshots | ai-memory |

---

## Root MD Proliferation (known issue)

12+ MD files at repo root: AGENTS, CLAUDE, CODEX_ROLE, CURRENT_PHASE, DEVELOPMENT_NEXT_STEPS,
ENGINEERING_CODEX, ENGINEERING_DECISIONS, OPERATOR_BASELINE, PROJECT_ARCHITECTURE,
PROJECT_COMPASS, QUICKSTART, RUNBOOK.

Status: tracked as ROOT-DOC-001. Do not add more root MDs — use `.ai/` or `docs/` instead.
