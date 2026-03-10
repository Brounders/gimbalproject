# Python Scripts Index

## Training
- `train_drone_bird.py` - Prepare/train/validate Drone-vs-Bird model from raw dataset layouts.
- `train_yolo_from_yaml.py` - Generic YOLO training runner from `dataset.yaml`.
- `run_training_curriculum.py` - Sequential dataset queue trainer (continues from previous `best.pt` and tracks progress in state JSON).
- `run_six_hour_training_fast_trainonly.sh` - Fast 6h train loop on prepared datasets.
- `run_six_hour_training_fast_full.sh` - Full 6h session with conversion/sanitize/mix/train.
- `run_six_hour_training_session.sh` - Legacy 6h session launcher (kept for compatibility).

## Dataset Prep / Conversion
- `build_mixed_dataset.py` - Build mixed train/val/test path lists without copying images.
- `convert_antiuav_rgbt_to_yolo.py` - Convert Anti-UAV RGBT sequences to YOLO format.
- `sanitize_yolo_pairs.py` - Remove orphan image/label pairs.
- `normalize_yolo_labels_to_boxes.py` - Normalize mixed segment/box labels to detect-only boxes.

## Evaluation / Quality Gate
- `run_offline_benchmark.py` - Offline KPI benchmark over fixed clips.
- `run_quality_gate.py` - Compare run KPIs against baseline thresholds.
- `run_profile_ab.py` - A/B of operator profiles (`operator_standard` vs `fast`) on fixed night/IR clips.
- `run_stable_cycle.py` - Single orchestrator: RTX artifact -> benchmark -> quality-gate -> release decision.
- `ingest_rtx_cycle.py` - End-to-end Mac intake: download RTX zip -> install `rtx_latest_best.pt` -> run stable cycle.
- `run_backend_parity.py` - Compare KPI parity across backend/preset pairs.
- `run_scenario_sweep.py` - Batch sweep of presets over one source.
- `run_dataset_batch.py` - Batch dataset-level evaluation helper.
- `summarize_batch_reports.py` - Aggregate dataset batch reports.

## Lock Event Analysis
- `analyze_lock_events.py` - Parse one or more `.jsonl` lock-event logs; print tabular summary (event counts, switches/min mean/max, frame span); optionally save JSON/CSV report.

## Monitoring
- `check_training_status.py` - Quick status from latest autosession log.

## Deprecated (kept for compatibility)
- `watch_training_progress.py` - Deprecated monitor for old run naming conventions.
- `monitor_six_hour_session.py` - Deprecated monitor tied to old `*_session.log` flow.

## Canonical runtime entrypoints
- CLI runtime: `python main_tracker.py`
- Desktop runtime: `python tracker_gui.py`
