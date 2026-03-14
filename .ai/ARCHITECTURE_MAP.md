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
