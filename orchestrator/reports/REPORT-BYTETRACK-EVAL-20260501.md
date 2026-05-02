# REPORT-BYTETRACK-EVAL-20260501

Status: ACCEPTED
Date: 2026-05-01
Owner: Codex
Type: Measurement tooling / tracking evaluation

## Purpose

Open Human-approved option B as a safe evaluation cycle:
compare current project pipeline metrics against native Ultralytics tracking output without changing runtime behavior.

## Scope

- Add standalone tracking evaluation tooling.
- Support native Ultralytics `bytetrack.yaml` and `botsort.yaml`.
- Keep outputs as measurement artifacts, not promotion artifacts.

## Non-Scope

- No baseline promotion.
- No runtime threshold changes.
- No GUI changes.
- No detector replacement.
- No training.
- No Hailo/RPi work.

## What Changed

1. Added `python_scripts/run_ultralytics_tracking_eval.py`.
   - Reads the same pack-file format as quality-gate tooling.
   - Builds project `Config` through existing presets and `apply_runtime_preset()`.
   - Runs current project pipeline via `evaluate_source()` unless `--skip-project` is set.
   - Runs native Ultralytics `model.track(..., persist=True, tracker="<tracker>.yaml")`.
   - Writes per-clip project/native reports plus aggregate JSON/CSV.
   - Marks summary decision as `measurement_only`.

2. Added `tests/test_ultralytics_tracking_eval.py`.
   - Covers native track selection helper.
   - Covers project/native comparison row deltas.
   - Does not run YOLO inference in unit tests.

3. Updated orchestration state.
   - `active_plan.md` records AP-20260501-BYTETRACK-EVAL as completed.
   - `completed_tasks.md` records this report.

## Findings

- Current `UltralyticsBackend.track_frame()` already uses `tracker='bytetrack.yaml'`.
- The real comparison is not "current tracker vs ByteTrack absent"; it is:
  project pipeline (`ByteTrack IDs + TargetManager + lock tracker + ROI + night detector`) vs native Ultralytics tracker-only output.
- Context7 confirmed current Ultralytics tracking supports `bytetrack` and `botsort`, with track IDs available through `Results.boxes.id`.

## Smoke Measurement

Command:

```bash
./tracker_env/bin/python python_scripts/run_ultralytics_tracking_eval.py \
  --pack-file configs/regression_pack_night.csv \
  --preset night \
  --tracker bytetrack \
  --max-frames 5 \
  --tag smoke_
```

Output:

- `runs/evaluations/ultralytics_tracking/smoke_tracking_eval_night_bytetrack.json`
- `runs/evaluations/ultralytics_tracking/smoke_tracking_eval_night_bytetrack.csv`

Smoke result:

| Clip | Native presence | Native id_chg/min | Native false_lock |
|------|-----------------|-------------------|-------------------|
| night_ground_large_drones | 0.000 | 0.00 | 0.000 |
| night_ground_indicator_lights | 0.000 | 0.00 | 0.000 |

Interpretation: 5-frame smoke validates execution and artifact generation only. It is not enough to judge tracker quality.

## Full Measurement

Command:

```bash
./tracker_env/bin/python python_scripts/run_ultralytics_tracking_eval.py \
  --pack-file configs/regression_pack.csv \
  --preset night \
  --tracker bytetrack \
  --tag full_
```

Output:

- `runs/evaluations/ultralytics_tracking/full_tracking_eval_night_bytetrack.json`
- `runs/evaluations/ultralytics_tracking/full_tracking_eval_night_bytetrack.csv`

Aggregate:

| Metric | Project pipeline | Native ByteTrack |
|--------|------------------|------------------|
| active_presence | 0.4448 | 0.1838 |
| id_chg/min | 7.0140 | 0.0000 |
| false_lock | 0.4448 | 0.1838 |
| avg_fps | 42.6017 | 33.3468 |

Per-clip highlights:

| Clip | Scene | Project presence | Native presence | Project id_chg/min | Native id_chg/min |
|------|-------|------------------|-----------------|--------------------|-------------------|
| drone_closeup_mixkit_44644_360 | day | 1.0000 | 1.0000 | 0.00 | 0.00 |
| night_ground_large_drones | night | 0.5208 | 0.0000 | 30.58 | 0.00 |
| Demo_IR_DRONE_146 | ir | 0.5399 | 0.0383 | 11.50 | 0.00 |
| IR_DRONE_001 | ir | 0.4684 | 0.0000 | 0.00 | 0.00 |
| IR_BIRD_001 | noise | 0.0581 | 0.0645 | 0.00 | 0.00 |
| night_ground_indicator_lights | noise | 0.0815 | 0.0000 | 0.00 | 0.00 |

Interpretation:

- Native ByteTrack has zero ID churn mostly because it produces no active track on the hard night/IR clips.
- Project pipeline has worse raw false-lock/presence rates in this measurement, but it is actually attempting continuity through TargetManager, lock tracker, ROI assist, and night detector.
- Day false_lock remains a no-GT structural artifact, consistent with OQ-003; it is not an operator-quality signal by itself.

Decision:

**FAIL for runtime integration.** Native ByteTrack-only behavior should not replace the current project pipeline.

**PASS as measurement baseline.** The tooling is valid for future controlled experiments, especially BoT-SORT comparison or native tracker tuning.

## Validation

- `./tracker_env/bin/python python_scripts/run_ultralytics_tracking_eval.py --help`
- `./tracker_env/bin/python -m pytest tests/test_ultralytics_tracking_eval.py -q`
- `./tracker_env/bin/python -m compileall -q python_scripts/run_ultralytics_tracking_eval.py tests/test_ultralytics_tracking_eval.py`
- `./tracker_env/bin/python python_scripts/run_ultralytics_tracking_eval.py --pack-file configs/regression_pack_night.csv --preset night --tracker bytetrack --max-frames 5 --tag smoke_`
- `./tracker_env/bin/python python_scripts/run_ultralytics_tracking_eval.py --pack-file configs/regression_pack.csv --preset night --tracker bytetrack --tag full_`

## Recommended Next Step

Run a full measurement pass before any architecture decision:

```bash
./tracker_env/bin/python python_scripts/run_ultralytics_tracking_eval.py \
  --pack-file configs/regression_pack.csv \
  --preset night \
  --tracker bytetrack \
  --tag full_
```

Optional second pass:

```bash
./tracker_env/bin/python python_scripts/run_ultralytics_tracking_eval.py \
  --pack-file configs/regression_pack.csv \
  --preset night \
  --tracker botsort \
  --tag full_
```

Do not promote native tracking behavior into runtime until project gate metrics show a clear win and Human approves the integration scope.
