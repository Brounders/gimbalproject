# Project Architecture

## Goal

Build the tracker as a reusable backend first, then place a desktop GUI on top of it.
This is the shortest path to a stable tool for:

- camera and file testing on macOS,
- later deployment on Raspberry Pi 5 + Hailo,
- future GUI control without rewriting the core logic.

## Recommended Stack

- Backend: Python 3.11
- GUI: PySide6
- Config: YAML
- Logging and runs: plain files under `runs/`
- Model runtime:
  - macOS: Ultralytics + Torch MPS
  - Raspberry Pi: Hailo runtime adapter

## Recommended Layout

```text
GimbalProject/
  app/
    main_cli.py
    main_gui.py
  src/uav_tracker/
    config/
      schema.py
      presets.py
    io/
      video_source.py
      video_writer.py
    detectors/
      yolo_detector.py
      night_detector.py
      roi_assist.py
    tracking/
      target.py
      target_manager.py
      lock_policy.py
    pipeline/
      tracker_pipeline.py
      frame_result.py
    ui/
      viewmodels.py
      qt/
        main_window.py
        video_widget.py
        settings_panel.py
    runtime/
      torch_backend.py
      hailo_backend.py
    services/
      session_service.py
      export_service.py
  configs/
    default.yaml
    small_target.yaml
    night.yaml
    rpi_hailo.yaml
  test_videos/
  datasets/
  runs/
  tests/
```

## Core Rule

`GUI must not own detection logic.`

The GUI should only:

- choose source,
- choose model,
- choose preset,
- start or stop pipeline,
- display frames and stats,
- save outputs and logs.

All tracking logic should live in `src/uav_tracker/pipeline` and `src/uav_tracker/detectors`.

## Processing Flow

One frame should pass through this order:

1. read frame
2. full-frame YOLO
3. ROI assist for small targets
4. night detector
5. target manager update
6. lock policy
7. draw overlay
8. emit stats and optionally save frame

## Lock Policy

Keep lock policy isolated from detectors.

It should decide:

- when target becomes confirmed,
- when to enter focus mode,
- when to suppress secondary targets,
- when to allow reacquire,
- when to fall back from track mode to scan mode.

## GUI Plan

Recommended first GUI window:

- Source selector: camera index or video file
- Model selector: `.pt` path
- Preset selector: `default`, `small_target`, `night`
- Buttons: `Start`, `Stop`, `Record`
- Live frame preview
- Status panel:
  - FPS
  - target count
  - active ID
  - mode: `SCAN` or `LOCK-FOCUS`
  - source of active target: `YOLO`, `ROI`, `NIGHT`
- Log console

## Threading

Use a worker thread for the pipeline.

The UI thread must only:

- receive rendered frames,
- receive metrics,
- update widgets.

The worker thread must:

- open source,
- run detection and tracking,
- push frame results to GUI via signals.

## Presets

Presets should move out of code and into YAML:

- `default.yaml`
- `small_target.yaml`
- `night.yaml`
- `rpi_hailo.yaml`

This makes it easy to switch between:

- webcam testing,
- night testing,
- Raspberry Pi deployment.

## Why This Is Better

- current tracker keeps moving forward without a rewrite,
- GUI can be added cleanly,
- Raspberry Pi backend can replace only the inference layer,
- testing becomes easier because pipeline and UI are separated.

## Next Practical Step

Refactor current `main_tracker.py` into:

1. `detectors/yolo_detector.py`
2. `detectors/night_detector.py`
3. `detectors/roi_assist.py`
4. `tracking/target_manager.py`
5. `pipeline/tracker_pipeline.py`
6. thin `main_cli.py`
7. thin `main_gui.py`
