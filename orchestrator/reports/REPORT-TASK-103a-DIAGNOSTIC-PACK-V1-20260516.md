# REPORT-TASK-103a-DIAGNOSTIC-PACK-V1-20260516

## Verdict

ACCEPTED.

Read-only telemetry layer. No runtime algorithm changed. Provides per-frame
diagnostic signals (latency by stage, scene confusion, bbox area stability,
proposal source counts) needed to calibrate TASK-103b..103e.

## Scope

- `FrameOutput` += `scene_label_runtime`, `scene_confidence_runtime`,
  `proposal_count_by_source`, `bbox_area`.
- `TrackerPipeline.process_frame`:
  - `timings_ms` += `manager` (target manager block) and `total` (whole frame).
  - Computes 4 new diagnostic fields from existing pipeline state.
- `frame_result_from_output` adapter propagates fields into
  `FrameResult.metrics`.
- `run_tracking_gt_diagnostics.py`:
  - Per-clip: `bbox_area_cv`, `scene_runtime_counts`, `scene_confidence_avg`,
    `proposal_mean_by_source`, `proposal_seen_rate_by_source`,
    `stage_ms_p50`/`p95`/`p99` for every stage.
  - Per-report: `scene_confusion` (gt_scene → runtime_scene distribution).
- `summary.csv` += `bbox_area_cv`, `scene_confidence_avg`, and 8 stage p99
  columns.
- Tests (4 new in `tests/test_tracking_gt_tools.py`):
  - `test_run_clip_emits_diagnostic_pack_fields`
  - `test_build_report_includes_scene_confusion`
  - `test_write_outputs_csv_includes_stage_p99_columns`
  - `test_frame_result_metrics_carries_diagnostic_pack_fields`

No detector parameter, no preset, no acceptance gate logic changed.

## Validation

Passed:

- `pytest tests/ -q` → 868 passed.
- `python_scripts/smoke_qml_mvp.py` → `[pass] qml bridge smoke ok`.
- `orchestrator/scripts/check_orchestration_state.py` → `OK`.
- Full GT diagnostic run on `configs/gt_minipack/generated/` (14 clips):
  `runs/evaluations/tracking_gt_diagnostics/diag_pack_v1_20260516_155830/`.

A/B baseline: `target_lab_live_auto_20260516_152826`. No quality regression
expected (read-only). risk count 20 unchanged.

## Findings (these drive TASK-103b..103e calibration)

### F1. Auto-scene-detect drift on EO and IR_NEGATIVE

`scene_confusion`:

| GT scene | Runtime scene distribution |
|----------|----------------------------|
| IR | ir 100% |
| UNKNOWN | day 100% |
| EO_NEGATIVE | day 100% |
| **EO** | **day 83%, ir 17%** |
| **IR_NEGATIVE** | **night 50%, ir 50%** |
| NEGATIVE | day 100% |

EO clips spend 17% of frames misclassified as IR. IR airplane negatives split
50/50 between night and ir. This confirms the W1 weakness from the prior audit:
2-feature (brightness + saturation) classifier is too coarse. TASK-103c must
use multi-ROI sampling and more features.

### F2. `scene_confidence_runtime` as currently defined is a poor signal

All 14 clips show `scene_confidence_avg = 1.000`. The metric only drops while
the streak counter is climbing toward `confirm`; once a flip happens the streak
resets and confidence returns to 1.0. So it does not measure how often scene
flips. TASK-103c should replace it with a sliding-window scene-stability ratio.

### F3. Latency budget — YOLO dominates, scheduler not justified

Stage p99 per clip (worst values):

| Stage | Range across clips (p99 ms) |
|-------|------------------------------|
| yolo (global) | 46.5 – 109.8 |
| lock | 0 – 24.8 |
| local | (covered by global yolo path) |
| roi | ~0 |
| night | 0 – 25.3 |
| manager | < 1 |
| draw | (render=False here) |
| **total** | **60.7 – 190.8** |

YOLO is the only stage ever above 25ms. Lock/night/manager combined are an
order of magnitude smaller. **Phase D7 (async scheduler) is not warranted** —
the next bottleneck is either model inference itself or per-clip detection
strategy, not stage parallelism.

### F4. `bbox_area_cv` confirms bbox stability gap is real

| Clip | bbox_area_cv | Comment |
|------|--------------|---------|
| `2023-11-23 14-56-24` | **1.141** | bbox area varies by ±114% on the same target |
| `2_minie3_..._birds` | 0.568 | |
| `7_minie5_..._cut_blur` | 0.446 | |
| `antiuav_rgbt_train_...` | 0.166 | |
| `antiuav_rgbt_...200805_...` | 0.061 | |
| `f1_3_EO_..._occlusion_far` | 0.018 | |
| IR clips | 0.000 | tracker silent → no bbox samples to vary |

TASK-103b (bbox stability layer) has now an explicit before-number to beat on
`2023-11-23`, `2_minie3_*_birds`, `7_minie5_*_blur`.

### F5. Proposal sources tell who is actually working

Per-clip fraction of sampled frames with ≥1 proposal:

| Clip class | Dominant source |
|------------|-----------------|
| IR drones (minie3, IR_DRONE_025, f2_13, 9_dji2, 5_minie3_far) | `night` 22–93% — YOLO almost never fires (0–2%) |
| RGBT `_infrared` | `lock` 80% but recall poor → lock holds on wrong region |
| EO clips (`f1_3_..._occlusion_far`, `7_minie5_..._blur`) | all sources ≤1–47% — pipeline often blind in EO |
| Negatives (`V_BIRD_030`, `IR_AIRPLANE_*`) | all 0% — fail closed |

Three actionable signals for TASK-103d (Unified Proposal Layer):

1. On IR drones the `night/peak` source is the truth carrier. Trust table must
   weight `peak × ir` very high.
2. On RGBT clips `lock` source is alive but unreliable. Trust table must
   demote `lock` when no detector confirms and scene confidence is degraded.
3. EO clips are detector-starved, not policy-starved. The next EO-focused
   work is either YOLO conf tuning or ROI-assist for day clutter — not
   proposal selection.

## Risks

- Diagnostic adds ~1µs per frame (one `perf_counter` + 4 dict ops). Negligible.
- `bbox_area` defaults to 0 when no active bbox — could be confused with
  "active bbox of zero area". Mitigated by `_bbox_positive` filter in CV
  computation.
- `scene_confidence_runtime` semantics are weak (see F2). Kept as-is for this
  task; redesign in TASK-103c.

## Next Pass

TASK-103b — Bbox stability layer. Acceptance numbers now grounded in F4.

Do not reintroduce source-name routing.
Do not start async scheduler (F3 closes that question).
Do not start training cycle (no policy fix yet).
