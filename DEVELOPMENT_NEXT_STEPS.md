# Drone Tracker: Next Steps (Mac M1 -> RPi5 + Hailo)

## 1) Fine-tuning YOLO11n (Drone vs Bird)

### 1.1 Activate env
```bash
cd /Users/bround/Documents/Projects/GimbalProject
source tracker_env/bin/activate
python -V
```

### 1.2 Put dataset on disk
Expected paths:
- `datasets/drone_bird_raw/images/...`
- `datasets/drone_bird_raw/labels/...`

Supported formats by script:
- Flat: `images/* + labels/*`
- Pre-split YOLO: `images/train,val + labels/train,val`
- Also supported (your current dataset): `train/images`, `valid/images`, `test/images`

If dataset is in Downloads (your case), copy once:
```bash
cd /Users/bround/Documents/Projects/GimbalProject
rsync -a --delete ~/Downloads/'Segmented Dataset Based on YOLOv7 for Drone vs. Bird Identification for Deep and Machine Learning Algorithms'/Dataset/ datasets/drone_bird_raw/
```

### 1.3 Run training
```bash
python python_scripts/train_drone_bird.py \
  --dataset-root datasets/drone_bird_raw \
  --workdir datasets/drone_bird_yolo \
  --model models/yolo11n.pt \
  --project runs \
  --name drone_bird_v2 \
  --device mps \
  --imgsz 640 \
  --batch 8 \
  --epochs 120
```

Quick preparation check (no training):
```bash
python python_scripts/train_drone_bird.py \
  --dataset-root datasets/drone_bird_raw \
  --workdir datasets/drone_bird_yolo \
  --model models/yolo11n.pt \
  --prepare-only
```

The script now auto-fixes this dataset's broken class split:
- Original `train/valid` contains only class `Drone`.
- Class `Bird` exists only in original `test`.
- `train_drone_bird.py` auto-resplits all data with stratification when class is missing in train/val.

Outputs:
- Best weights: `runs/detect/runs/drone_bird_v2/weights/best.pt`
- Plots/metrics: `runs/detect/runs/drone_bird_v2/`

If OOM on MPS:
- lower `--batch` to `8` or `6`
- keep `--imgsz 640` first, then test `768`

### 1.4 Quick quality check
Already included at end of script (`model.val`).
Target metric for first stable baseline: `mAP50 >= 0.75` (dataset dependent).

## 2) Hybrid tracker run (YOLO + Night detector)

Updated file: `main_tracker.py`

### 2.1 Camera mode
```bash
python main_tracker.py --source 0 --model runs/detect/runs/drone_bird_v2/weights/best.pt --device mps
```

### 2.2 Video file mode
```bash
python main_tracker.py --source test_videos/night_test.mp4 --model runs/detect/runs/drone_bird_v2/weights/best.pt --device mps
```

Keys:
- `q` quit
- `n` switch active target
- `r` reset target manager

## 3) What was improved in hybrid logic

- Night detections now require confirmation across frames.
- Combined motion mask: `MOG2` + frame-difference to suppress static noise.
- Border/aspect/area filters to reduce false positives.
- Separate night IDs (`9000+`) with nearest-neighbor association.
- Correct aging/removal of YOLO and night tracks (different TTL).
- Proper source switch via `--source` (`0` camera or file path).

## 4) Migration plan: Raspberry Pi 5 + AI HAT+ (Hailo)

### 4.1 On Raspberry Pi install
1. Raspberry Pi OS 64-bit (Bookworm recommended).
2. Python 3.11 venv.
3. OpenCV (`python3-opencv`) and numpy.
4. Hailo runtime/toolchain according to your AI HAT+ package:
   - HailoRT
   - model compiler / conversion tools
   - Python bindings for inference pipeline

### 4.2 Model export path
1. Train on Mac, keep `best.pt`.
2. Export to ONNX on Mac or RPi:
```bash
yolo export model=runs/detect/runs/drone_bird_v2/weights/best.pt format=onnx imgsz=640
```
3. Convert ONNX -> Hailo HEF using Hailo toolchain on supported environment.
4. Run HEF with Hailo runtime pipeline on RPi.

### 4.3 Code parts likely unchanged
- Target manager logic (ID, lock, switching, smoothing).
- Night detector logic (OpenCV).
- Draw/HUD and key controls.

### 4.4 Code parts likely to change
- YOLO inference call (`ultralytics`) -> Hailo inference wrapper.
- Pre/post-processing around model I/O (tensor shape, normalization, decode).
- Possibly camera pipeline (GStreamer/libcamera for stable FPS).

### 4.5 Expected FPS on RPi5 + Hailo (practical estimate)
- YOLO-only tiny model, optimized HEF: ~20-40 FPS (depends on resolution and pipeline overhead).
- Hybrid mode (YOLO + night detector + drawing): ~15-30 FPS.
- Biggest FPS killers: Python postprocess and UI drawing, not only inference.

## 5) Suggested next validation sequence

1. Train `drone_bird_v2` on Mac with auto-resplit and lock baseline metrics.
2. Run `main_tracker.py` on 3-5 night videos, log false positives.
3. Tune night params in `Config`:
   - `NIGHT_MOT_THRESH`
   - `NIGHT_DIFF_THRESH`
   - `NIGHT_MIN_AREA`, `NIGHT_MAX_AREA`
   - `NIGHT_CONFIRM`
4. Freeze best config, then start Hailo export/conversion.

Quick multi-scenario benchmark (new):
```bash
cd /Users/bround/Documents/Projects/GimbalProject
source tracker_env/bin/activate
python python_scripts/run_scenario_sweep.py \
  --source test_videos/drone_closeup_mixkit_44644_360.mp4 \
  --presets default,small_target,night,antiuav_thermal \
  --max-frames 300 \
  --report-dir runs/evaluations/sweeps \
  --tag night_probe_
```
Outputs:
- per-preset JSON reports in `runs/evaluations/sweeps/`
- ranking summary JSON/CSV (`summary_*.json`, `summary_*.csv`)
- score uses lock-rate, FPS, lock-switches/min, false-alarm-rate, and budget level

## 6) Tracking Evolution Plan (focused)

Status (March 4, 2026):
- 6.1 is now implemented in codebase: lock-event telemetry (`acquired/lost/reacquired/switch`) and `switches/min` metric are emitted in tracker HUD/GUI/evaluation report.
- 6.1 advanced is implemented: motion-predictive reacquire (`vx/vy` + predicted center gating) reduces lock jumps when target is briefly lost.
- 6.2 baseline is implemented: dynamic compute-budget (adaptive ROI candidate cap, night-detector frame skipping under load, dynamic scan/local intervals) with budget metrics in evaluation.
- 6.2 advanced is implemented: local YOLO validation now auto-boosts for tiny targets or weak lock (dynamic local imgsz/conf), with budget-aware fallback.
- 6.3 baseline is implemented: lightweight lock event export to JSONL (`--lock-log`) for offline timeline analysis.
- 6.3 advanced (partial): GUI now auto-writes lock-event logs per run, and scenario sweep runner compares presets with unified KPI score.

### 6.1 Lock quality and anti-jump stability
Goal:
- Keep lock on one UAV and avoid switching to random micro-targets.

Implementation:
- Temporal class confidence (`drone_score`) on each track.
- Reacquire only for candidates near the locked trajectory and with sufficient drone score.
- Stronger active-target scoring (speed + confidence + hit streak + drone score).

Acceptance criteria:
- In test night clips, lock switches only after true loss, not on each noisy candidate.
- Number of active-ID changes per minute drops by at least 30% vs current baseline logs.

### 6.2 Small-target recall at night with compute budget
Goal:
- Improve detection of tiny UAV while preserving FPS.

Implementation:
- Run night detector only after short primary-detector cooldown.
- Keep ROI assist active for small-target presets, but clamp candidate count by motion quality.
- Add optional frame-skipping policy for heavy pipelines (e.g., full scan every N frames, local validate each frame).

Acceptance criteria:
- FPS in operator mode stays >= 20 on Mac M1 at 640 input.
- No growth in false positive bursts after 5-minute night run.

### 6.3 Track lifecycle and noise suppression
Goal:
- Reduce visual/logic noise from short-lived night blobs.

Implementation:
- Show only mature tracks (`hit_streak` threshold by source).
- Hide stale tracks quickly (`display_max_lost_frames`).
- Add lightweight event logger: lock acquired/lost/reacquired with frame index.
- CLI export is available now: `--lock-log runs/lock_events.jsonl`.

Acceptance criteria:
- HUD remains readable during dense background motion.
- Operators can reconstruct lock timeline from log without video replay.

### 6.4 Preparation for embedded runtime (RPi + Hailo)
Goal:
- Keep tracking logic identical while replacing inference backend.

Implementation:
- Freeze tracker I/O contract (`Detection` schema + timing hooks).
- Build benchmark harness for backends (`ultralytics`, `hailo`) with same video inputs.
- Add preset parity checks: same YAML profile should run on both modes with device-specific overrides.

Acceptance criteria:
- Same clip runs on Mac and RPi backend with comparable lock behavior.
- Backend swap does not require edits in target manager/pipeline logic.

## 7) Evolution Roadmap (v2, March 5, 2026)

Current implementation status:
- [x] Anti-jitter lock mode hysteresis (`LOCK_MODE_ACQUIRE_FRAMES` / `LOCK_MODE_RELEASE_FRAMES`).
- [x] Active-ID switch cooldown (prevents rapid target jumping).
- [x] Reticle-centric overlay (operator-focused HUD, reduced clutter).
- [x] Smoothed confidence with 5s display cadence.
- [x] Predictive reticle hold on short target-loss windows (vx/vy based).
- [x] Continuity telemetry integrated (continuity score, active presence, ID changes, median reacquire).

### Phase A (now): Tracking stability first
Goal:
- Keep one target continuously with minimal visual jitter in daytime and night test clips.

Tasks:
1. Tune cooldown and loss thresholds per preset (`default`, `small_target`, `night`, `antiuav_thermal`).
2. Add telemetry for target continuity:
   - active-ID change rate
   - continuity score (frames on same target / total)
   - median reacquire time
3. Add deterministic regression clip pack (short fixed videos) and compare metrics after every change.

Exit criteria:
- Active-ID switches/min reduced by >= 50% vs pre-cooldown baseline.
- No rapid oscillation between target states on clean single-UAV clip.

### Phase B: Night robustness and false-positive control
Goal:
- Preserve lock in low contrast while suppressing random micro-targets.

Tasks:
1. Hard-negative tuning for night detector and ROI assist (moving lights, sensor noise, clouds).
2. Preset-specific night thresholds auto-selected by scene profile.
3. Add confidence floor for retaining target during short detector gaps.

Exit criteria:
- Fewer false lock captures on night sky backgrounds.
- Stable tracking on at least 3 distinct night clips.

### Phase C: Data and model evolution
Goal:
- Improve bird-vs-drone discrimination and small-object recall.

Tasks:
1. Expand labeled night/IR dataset and curate hard cases.
2. Retrain with scenario-balanced sampling (day/night/thermal/small target).
3. Maintain benchmark table per model version (mAP + runtime + continuity KPI).

Exit criteria:
- Model update improves continuity KPI and false alarm rate without FPS regression.

### Phase D: Embedded parity (RPi5 + Hailo)
Goal:
- Reproduce Mac behavior on target hardware with predictable latency.

Tasks:
1. ONNX -> HEF conversion path with fixed preprocess/postprocess contract.
2. Backend parity tests (same clip, same preset, comparable events).
3. Embedded operator profile with strict latency budget.

Exit criteria:
- Same operational behavior on RPi/Hailo within acceptable metric deltas.

## Implemented vNext Stability Gate (2026-03-07)
Status:
- Canonical pipeline states are fixed as `SCAN/TRACK/LOST` and used by UI as source of truth.
- Strict active-ID switching guard is enabled in focus lock path.
- Evaluation report now includes `false_lock_rate`, `active_id_changes_per_min`, and `mode_counts`.
- Deterministic regression pack added: `configs/regression_pack.csv`.

New scripts:
1. Offline benchmark summary (JSON + CSV + score)
   - `./tracker_env/bin/python python_scripts/run_offline_benchmark.py --preset night --source-list configs/regression_pack.csv --max-frames 0`
2. Strict quality gate with PASS/FAIL exit code
   - `./tracker_env/bin/python python_scripts/run_quality_gate.py --preset night --pack-file configs/regression_pack.csv --baseline runs/evaluations/quality_gate/<prev>.json`
3. Backend parity check (Mac profile vs Embedded profile)
   - `./tracker_env/bin/python python_scripts/run_backend_parity.py --pack-file configs/regression_pack.csv --left-preset night --right-preset rpi_hailo --left-label mac --right-label rpi`
