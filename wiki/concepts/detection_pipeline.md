# Detection Pipeline

> Frame processing flow: YOLO → ROI assist → Night detector → Target manager → Lock policy → Overlay

## Processing Order (per frame)

1. **Read frame** — from video file or camera
2. **Full-frame YOLO** — main detector, `yolo_detector.py`
3. **ROI assist** — small-target path, `roi_assist.py`
4. **Night detector** — blob-based MOG2 detector, `night_detector.py`
5. **Target manager update** — `target_manager.py`
6. **Lock policy** — `lock_policy.py`
7. **Draw overlay** — `overlay.py`
8. **Emit stats / save frame** — `frame_result.py`

## Source Files

| Module | Path | Role |
|--------|------|------|
| `yolo_detector` | `src/uav_tracker/detectors/yolo_detector.py` | Main YOLO inference |
| `night_detector` | `src/uav_tracker/detectors/night_detector.py` | MOG2 blob detection |
| `roi_assist` | `src/uav_tracker/detectors/roi_assist.py` | Small-target ROI |
| `pipeline` | `src/uav_tracker/pipeline.py` | Orchestration (1067 lines after AP-016 split) |
| `overlay` | `src/uav_tracker/overlay.py` | Draw helpers, extracted AP-016 |
| `frame_result` | `src/uav_tracker/frame_result.py` | `FrameOutput` dataclass, extracted AP-016 |
| `target_manager` | `src/uav_tracker/tracking/target_manager.py` | Multi-target state |
| `lock_policy` | `src/uav_tracker/tracking/lock_policy.py` | Lock/unlock decisions |

## Night Detector

The night detector is a separate detection path active when `night_enabled=True` in the preset.
It uses MOG2 background subtraction and blob analysis to find targets invisible to YOLO in low-light.

Key parameters (all exposed via YAML / `profile_io.py::apply_overrides` as of AP-024/AP-025):

| YAML key | Config field | Default | Meaning |
|----------|-------------|---------|---------|
| `night_max_area` | `NIGHT_MAX_AREA` | 200 | Max blob area (px²) |
| `night_track_dist` | `NIGHT_TRACK_DIST` | 42 | Spatial gate (px) |
| `night_lost_max` | `NIGHT_LOST_MAX` | 8 | Grace frames before track lost |
| `night_confirm` | `NIGHT_CONFIRM` | 3 | Consecutive detections required to enter candidates |
| `night_max_ar` | `NIGHT_MAX_AR` | 3.0 | Max blob aspect ratio |
| `night_mot_thresh` | — | 18 | Motion threshold |
| `night_diff_thresh` | — | 12 | Diff threshold |

> `night_confirm=5` was the dominant fix for false-lock on large-target night clips (AP-025).
> Root cause: transient false positives at detector level, not lock policy.

## Runtimes

| Platform | Runtime | Notes |
|----------|---------|-------|
| macOS | Ultralytics + Torch MPS | Current development target |
| Raspberry Pi 5 | Hailo runtime adapter | Future deployment target |

## Architecture Rule

`GUI must not own detection logic.` The GUI only: chooses source/model/preset, starts/stops pipeline,
displays frames and stats. All tracking logic lives in `src/uav_tracker/`.

## Related

- [lock_policy.md](lock_policy.md) — what happens after target manager decides
- [presets.md](../entities/presets.md) — how YAML configs drive detection parameters
- [runtime_hardening.md](runtime_hardening.md) — history of parameter tuning
