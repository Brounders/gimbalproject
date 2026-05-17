# TASK-20260517-126 — Playback performance root-cause intake

## Status

Initial UI data-path hardening implemented.  Operator smoke still required.

## Evidence

Weak4 diagnostics show frame p99 latency high enough to stutter live playback:

- `1_minie3_range_close`: baseline `stage_total_p99_ms ~= 74 ms`
- `9_dji2_range_medium`: baseline `stage_total_p99_ms ~= 84 ms`
- `antiuav_rgbt_20190925`: baseline `stage_total_p99_ms ~= 61 ms`
- `antiuav_rgbt_train_20190925`: baseline `stage_total_p99_ms ~= 52 ms`

Backend stage timing shows most latency comes from inference stages:

- `global` YOLO p99 often `50-73 ms`;
- `local` validation can reach `~38 ms` on lock-heavy clips;
- `night` stage is usually `8-15 ms`;
- `manager` and the new static gate are sub-millisecond.

Separate UI finding:

- `TrackerWorker` emitted every frame as a NumPy BGR array.
- `TrackerBridge._on_frame_ready()` ran in the GUI thread.
- `FrameProvider.update_frame()` performed BGR -> RGB conversion and a deep
  `QImage.copy()` in the GUI thread.
- QML `Image` loaded `image://frames/current` synchronously.

This means the GUI thread could block on frame conversion/image loading in
addition to backend inference jitter.

## Implemented

- Move BGR -> RGB `QImage` conversion into `TrackerWorker` worker thread.
- Allow `FrameProvider.update_frame()` to accept already-built `QImage`.
- Set QML `VideoSurface` live image loading to `asynchronous: true`.

## Decision

The playback stutter has two layers:

1. backend latency spikes from YOLO/global/local inference;
2. GUI-thread frame conversion / synchronous image loading.

The first fix targets layer 2.  Layer 1 still needs a separate performance
profile and preset tuning pass.

## Next

Run operator smoke in QML and inspect:

- displayed FPS;
- latency panel;
- whether stutter remains while `timings_ms.global/local/night` spike;
- whether frame presentation is smoother after the QImage worker-thread move.

If stutter remains, the next bounded lever is backend scheduling:

- lower live `imgsz` for operator mode;
- raise `GLOBAL_SCAN_INTERVAL`;
- throttle local validation;
- skip UI frame presentation when the GUI is behind instead of queueing every
  processed frame.
