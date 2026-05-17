# REPORT-TARGET-LAB-ACT4-LIVE-AUTO-20260516

## Verdict

ACCEPTED WITH RISKS.

Act 4 removes the wrong foundation: Target Lab no longer selects tracker
profiles from clip names, folder names, or dataset identity.  Diagnostics now
run a single live-oriented preset and let the pipeline choose detector behavior
from frame content.

This is accepted as an architectural correction, not as a final tracking
quality victory.

## Scope

Accepted changes:

- Added `configs/tracking_live_auto.yaml` as the single live-oriented Target Lab
  preset.
- Target Lab diagnostics now launch with `--preset tracking_live_auto`.
- `run_tracking_gt_diagnostics.py` no longer contains `_preset_for_scene()` and
  no longer switches presets by `source` / folder / file name.
- Scene labels remain in reports for grouping metrics, but they no longer drive
  tracker behavior.
- `TrackerPipeline._adapt_auto_scene()` now applies runtime detector overrides
  for day/night/IR from frame brightness/saturation.
- The stateful night/peak detector now reads `RuntimeConfigView`, so live
  auto-scene affects actual night/peak detection instead of only YOLO threshold
  telemetry.

No model weights, production promotion, DTS training, or async scheduler change
is part of this decision.

## Evidence

Previous accepted baseline:

- `runs/evaluations/tracking_gt_diagnostics/target_lab_act3b_20260516_150258/summary.json`

Live-auto candidate:

- `runs/evaluations/tracking_gt_diagnostics/target_lab_live_auto_20260516_152826/summary.json`

Risk count:

- Act 3b: 21
- Act 4 live-auto: 20

Scene deltas:

| Scene | Recall | Missed | Off-target | FPS |
|---|---:|---:|---:|---:|
| EO | 0.465 -> 0.465 | 0.514 -> 0.498 | 0.023 -> 0.036 | 30.5 -> 38.5 |
| EO_NEGATIVE | 0.950 -> 0.946 | 0.040 -> 0.050 | 0.013 -> 0.006 | 78.4 -> 84.8 |
| IR | 0.556 -> 0.474 | 0.113 -> 0.113 | 0.331 -> 0.413 | 50.8 -> 64.9 |
| IR_NEGATIVE | 0.185 -> 0.000 | 0.752 -> 1.000 | 0.063 -> 0.000 | 16.4 -> 22.2 |
| NEGATIVE | 0.046 -> 0.000 | 0.954 -> 1.000 | 0.000 -> 0.000 | 15.4 -> 25.9 |
| UNKNOWN | 0.000 -> 0.000 | 0.010 -> 0.967 | 0.984 -> 0.032 | 40.3 -> 27.4 |

Important clip observations:

- `5_minie3_range_far` remains strong: recall `0.875`.
- `IR_DRONE_025` remains strong: recall `0.987`.
- `f2_13_IR_dji_mavic_2` remains usable: recall `0.677`.
- `antiuav_rgbt_20190925_200805_1_2_infrared` remains a hard failure:
  off-target `1.000`.
- `antiuav_rgbt_train_20190925_205804_1_2_infrared` regresses:
  recall `0.412`, off-target `0.589`.
- `IR_AIRPLANE_*` now fails closed instead of tracking off-target: recall `0`,
  off-target `0`.

## Decision Rationale

The Human correctly rejected folder/source-name routing as production logic.
Live video has no dataset folder and no filename truth.  Therefore the
architecture must not say "if this path contains antiuav_rgbt then use profile
X".  That was useful for diagnosis, but wrong for the product.

The accepted Act 4 behavior is:

- one live preset;
- frame-content auto-scene;
- day disables night detector by default;
- IR enables peak-style small-target detection through runtime config;
- reports still group by GT scene, but only for analysis.

The quality result is mixed.  This is acceptable for this specific task because
the task was to remove the wrong foundation.  The new baseline is more honest:
it exposes the remaining universal selector problem instead of hiding it behind
dataset-specific routing.

## Next Pass

Act 5 must close the next real tracker layer:

1. build a universal proposal/selector policy over YOLO, local, ROI, night,
   peak, lock, and operator sources;
2. demote low-evidence night/peak proposals near static OSD/background;
3. protect reacquire from switching to unrelated background;
4. stabilize bbox size without hiding true target scale changes;
5. validate against `target_lab_live_auto_20260516_152826`, not against
   source-name routing.

Do not reintroduce source-name/folder-name routing.
