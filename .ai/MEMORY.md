# Engineering Memory — GimbalProject

## Project Identity

**GimbalProject**: Real-time UAV (drone/bird) tracking system.
Purpose: Detect, lock, and follow aerial targets using YOLO + template matching + motion detection.
Runtimes: Mac M1 (Ultralytics/MPS for dev) and RPi5+Hailo (abstracted, stub only).

---

## Architecture Principles

- **SRP extraction pattern**: A08 decomposition extracted 9 components from TrackerPipeline monolith in stages. Each stage is an independent commit. Precedent for future extractions.
- **Coordinator pattern**: `TrackerPipeline` orchestrates components via `self.*` — it does not implement logic itself, it delegates.
- **Config as single source of truth**: All tuneable values live in `Config` dataclass. No magic numbers in pipeline or detector logic.
- **No circular imports**: `overlay.py` must be imported at the top of `pipeline.py`, not deferred to end-of-file. A03 fixed the late-import workaround.
- **threading.Event for QThread control**: `TrackerWorker` and `EvaluationWorker` use `threading.Event` (not QMutex) for stop/switch signals. A01 established this pattern.

---

## Naming Conventions

| Entity | Convention | Example |
|---|---|---|
| Classes | PascalCase | `TargetManager`, `BudgetController` |
| Modules | snake_case | `target_manager.py`, `lock_tracker.py` |
| Config fields | UPPER_SNAKE_CASE | `LOCK_CONFIRM_FRAMES` |
| Pipeline state | `self.*` (public for extracted), `self._*` (internal) | `self.manager`, `self._frame_count` |
| Events | SCREAMING_SNAKE | `LOCK_ACQUIRED`, `LOCK_LOST`, `LOCK_SWITCH` |

---

## Critical Files

| File | Lines | Risk | Notes |
|---|---|---|---|
| `src/uav_tracker/pipeline.py` | ~820 | HIGH | Coordinator + inline AutoSceneAdapter; A08 ongoing |
| `app/main_gui.py` | ~1600 | HIGH | Monolith: TrackerWorker + UI + APP_STYLESHEET inline |
| `src/uav_tracker/config.py` | ~145 fields | MEDIUM | Flat dataclass; restructure = breaking API change |
| `src/uav_tracker/tracking/target_manager.py` | ~459 | MEDIUM | Multi-target logic; central to all detection paths |

---

## Component Interfaces

Extracted components communicate with `TrackerPipeline` via:
- **Constructor injection**: Pipeline instantiates each component with `cfg` reference.
- **Return values**: Components return typed results (e.g., `FrameOutput`, detection lists).
- **Direct attribute access**: Pipeline reads `self.manager.active_id`, `self.tracking_sm.state`, etc.
- **No back-references**: Components must NOT import or reference `TrackerPipeline` — one-way dependency only.

---

## Quality Gate Rules

Runner: `python_scripts/run_quality_gate.py`

| Metric | Description | Gate |
|---|---|---|
| `continuity_score` | ID stability across frames | Must not regress vs baseline |
| `presence_rate` | Fraction of frames with detection | Must not regress |
| `false_lock_rate` | False positives on non-target clips | Must not regress |
| `id_changes_per_min` | ID churn rate | Must not regress |

- Baseline: `night` preset, `drone_bird_probe_fast` model.
- `false_lock_rate` check is **skipped** when `gt_frames=0` (no ground truth available).
- Regression packs: `configs/regression_pack.csv`, `configs/regression_pack_ir_gt.csv`.

---

## Training Status

- **drone_bird_yolo**: 100% daytime frames, 540:1 drone:bird ratio — curriculum failure root cause.
- **antiuav_rgbt_ir_yolo**: only source of night visible-light data; insufficient alone.
- **No accepted production model**: all RTX candidates (including `rtx_drone_stability_12h_v1`) rejected due to false-lock regression.
- **BRIEF-033**: new training strategy required — target ≥20% night frames, drone:bird ratio ≤10:1.

---

## Engineering Decisions Log

| Decision | Rationale |
|---|---|
| Keep EMA smoothing, not Kalman filter (A07) | Kalman adds state complexity; EMA sufficient for current target motion profiles |
| `false_lock_rate` gated on `gt_frames > 0` | Clips without ground truth cannot produce valid false-lock measurements |
| `threading.Event` over `QMutex` for worker control | Pythonic, testable without Qt runtime; QMutex requires event loop context |
| Defer Config nested groups (BRIEF-030) | Restructuring is a breaking API change; no downstream consumers ready for migration |
| `overlay.py` import at file top, not deferred (A03) | PEP 8 compliance; late import was a workaround for a now-resolved circular dependency |
| AutoSceneAdapter stays inline until BRIEF-031 | Extraction requires its own BRIEF due to cfg-mutation side effects |
