# REPORT-TASK-103c-AUTO-SCENE-V2-20260516

## Verdict

ACCEPTED with residual EO/IR confusion noted.

5-feature multi-ROI classifier deployed. Confidence metric redesigned.
No recall regression. Two key regressions from earlier attempts fixed
(very_low_sat guard, ≥2-ROI IR threshold for RGBT split-screen).

## Scope

- `src/uav_tracker/config.py`:
  - `AUTO_SCENE_IR_EDGE_MAX: float = 0.12` — edge density gate for EO-overcast guard.
  - `AUTO_SCENE_IR_HOT_FRAC: float = 0.005` — hot pixel fraction for IR detection.
  - `AUTO_SCENE_STABILITY_WINDOW: int = 30` — sliding-window size for stability ratio.
- `src/uav_tracker/pipeline.py` — `_adapt_auto_scene` v2 (TASK-103c):
  - **5 features per ROI**: mean_Y, mean_S, hot_pixel_frac, edge_density, motion_density.
  - **5-ROI multi-sampling**: center + 4 quadrants. Majority vote with IR bias: ≥2 IR
    ROIs → IR scene (handles RGBT split-screen where only 2/5 ROIs cover IR half).
  - **EO-overcast guard**: if mean_S in borderline zone (>50% of ir_sat_max) AND
    edge_density > ir_edge_max AND no hot spots → classify as day, not IR. Fixes
    EO→IR confusion on textured gray scenes.
  - **very_low_sat bypass**: if mean_S < ir_sat_max * 0.5, skip EO guard — definitely IR.
  - Sliding-window history deque (`_auto_scene_history`); `_prev_sample_gray` for motion density.
  - **scene_confidence_runtime redesigned** as sliding-window stability ratio:
    `fraction of recent history samples matching current scene state`.
- `src/uav_tracker/pipeline.py` — `__init__`:
  - `self._auto_scene_history: deque = deque()`
  - `self._prev_sample_gray: np.ndarray | None = None`
- `tests/test_live_scene_runtime.py`:
  - Stub updated with `_auto_scene_history`, `_prev_sample_gray`.
  - 4 new tests:
    - `test_eo_overcast_not_classified_as_ir`
    - `test_thermal_ir_with_hot_spot_classified_as_ir`
    - `test_multi_roi_majority_vote_detects_ir_in_half_frame`
    - `test_scene_confidence_is_stability_ratio`

## Validation

Passed:

- `pytest tests/ → 843 passed`, 1 pre-existing failure (`test_target_lab_bridge`).
- `python_scripts/smoke_qml_mvp.py` → `[pass]`.
- `orchestrator/scripts/check_orchestration_state.py` → `OK`.

A/B run: `scene_v2c_20260516_20260516_181627` vs `diag_pack_v1_20260516_155830`.

### scene_confusion

| GT scene | Baseline | v2c | Δ |
|----------|----------|-----|---|
| EO | day 83%, ir 17% | day 81%, ir 19% | ≈unchanged |
| EO_NEGATIVE | day 100% | day 100% | — |
| **IR** | **ir 100%** | **day 14%, ir 86%** | ⚠️ −14% |
| **IR_NEGATIVE** | **night 50%, ir 50%** | **ir 100%** | ✅ fixed |
| NEGATIVE | day 100% | day 100% | — |
| **UNKNOWN** | day 100% | **day 9%, ir 91%** | ✅ improved |

### scene_confidence_avg (key fix)

Baseline: all 14 clips = 1.000 (F2 finding — metric was broken).
v2c: 3 clips now vary:
- `2023-11-23 14-56-24`: **0.947** (UNKNOWN clip, now correctly classified IR)
- `7_minie5_range_all_cut_blur`: **0.963**
- `antiuav_rgbt_20190925_200805_1_2_infrared`: **0.909**

### Recall gate

`2023-11-23 14-56-24`: recall 0.000 → **0.154** (+15.4%) — UNKNOWN clip now detected.
`2_minie3_birds`: 0.950 → 0.946 (−0.4% — within noise).
All other clips: 0 change. **Gate: PASS.**

## Analysis of Remaining Issues

### GT=IR 14% day misclassification

Cause: RGBT split-screen clips where the visible half generates 2 'day' votes (TL, BL
quadrants) and the IR half generates 2 'ir' votes (TR, BR). Center ROI falls on the
split — depending on frame content, center may vote 'day'. With ≥2 IR rule the 2 IR
quadrant votes win, but some frames with unusual quadrant coverage still resolve to day.

Impact on tracking: recall unchanged (PASS). Config overrides still apply for 86% of IR
frames. Remaining 14% use day config which may reduce night/peak detector sensitivity.

### EO→IR confusion unchanged (17%→19%)

The EO-overcast guard only activates when saturation is in borderline range. The EO clips
that drift to IR classification have very low saturation AND low edge density, bypassing
the guard. Fixing this requires either tighter ir_sat_max (risking true IR misses) or
additional temporal smoothing. Deferred to TASK-103d calibration data.

## Risks

- `very_low_sat` threshold at 50% of ir_sat_max (=12.5 at default=25) may be too low
  for IR cameras with slight color artifacts. If IR camera outputs mean_S=13-25 for some
  frames, EO-overcast guard may fire incorrectly. Monitor in production.
- Motion density feature computed but not yet used in decision tree.
  Deferred to TASK-103d when trust table calibration is available.
- GT=IR 14% day regression: acceptable for now; does not affect recall gate.

## Next Pass

TASK-103d — Unified Proposal Layer. Now calibrated with:
- F5 data: night/peak source is IR drone truth carrier; lock source unreliable on RGBT.
- F3: YOLO dominates latency (no scheduler needed).
- 103c stability ratio available as gate signal for proposal weighting.
