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
- Reverted QML `VideoSurface.asynchronous` to `false` after Human reported
  visible blinking.  The async `image://frames/current?<id>` reload path caused
  presentation flicker.
- Added `SEARCH_SCAN_INTERVAL`: SEARCH mode no longer runs global YOLO every
  processed frame.
- Added `ROI_ASSIST_IN_SEARCH`: live/QML and `tracking_live_auto` can disable
  ROI crop inference before an active target exists.
- QML operator config now disables `ROI_ASSIST_IN_SEARCH`.
- Fixed QML latency display to use `timings_ms["total"]` instead of summing
  stage timings plus `total`.

## A/B performance evidence

After `SEARCH_SCAN_INTERVAL` but before disabling search ROI:
`runs/evaluations/tracking_gt_diagnostics/task126_search_interval_20260517_184301`

After disabling ROI in pure search:
`runs/evaluations/tracking_gt_diagnostics/task126_search_no_roi_20260517_184543`

| Clip | total p99 before -> after | ROI p99 before -> after | Recall |
|---|---:|---:|---:|
| `1_minie3_range_close` | `94.7 ms -> 80.0 ms` | `39.4 ms -> 35.0 ms` | unchanged `0.000` |
| `9_dji2_range_medium` | `128.8 ms -> 75.8 ms` | `89.1 ms -> 34.8 ms` | unchanged `0.276` |
| `antiuav_rgbt_20190925_200805` | `54.5 ms -> 51.8 ms` | `0.0 ms -> 0.0 ms` | unchanged `0.000` |
| `antiuav_rgbt_train_20190925_205804` | `48.7 ms -> 48.8 ms` | `0.0 ms -> 0.0 ms` | unchanged `0.413` |

This matches the Human observation: lag is worst while searching because search
was running heavy global/ROI inference, while focused lock mode avoids most of
that work.

## Decision

The playback stutter has two layers:

1. backend latency spikes from YOLO/global/local inference;
2. GUI-thread frame conversion / synchronous image loading.

The first fixes target both layers:

1. remove GUI-thread frame conversion;
2. stop global YOLO every frame during SEARCH;
3. stop ROI crop inference in pure SEARCH for live/QML.

## Next

Run operator smoke in QML and inspect:

- displayed FPS;
- latency panel;
- whether stutter remains while `timings_ms.global/local/night` spike;
- whether frame presentation is smoother after the QImage worker-thread move.

If stutter remains, the next bounded lever is backend scheduling:

- lower live `imgsz` for operator mode;
- raise `SEARCH_SCAN_INTERVAL`;
- throttle local validation;
- skip UI frame presentation when the GUI is behind instead of queueing every
  processed frame.
