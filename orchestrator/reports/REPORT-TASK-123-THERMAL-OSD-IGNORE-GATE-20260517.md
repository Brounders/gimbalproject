# REPORT-TASK-123-THERMAL-OSD-IGNORE-GATE-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted

## Scope

TASK-20260517-123 проверяла no-training candidate: расширить top-left OSD ignore
zone для thermal peak preset после visual audit.

## Change

Promoted in:

- `configs/antiuav_thermal_peak.yaml`

Changed ignore zone:

- old: `x2=0.22`, `y2=0.07`;
- new: `x2=0.42`, `y2=0.18`;
- applies to: `yolo`, `local`, `roi`, `night`, `lock`.

Candidate file `configs/antiuav_thermal_peak_osd_wide.yaml` was used only for
A/B and not retained.

## Weak4 A/B Result

Baseline:

- `runs/evaluations/tracking_gt_diagnostics/task120_baseline__20260517_171712`

Promoted verification:

- `runs/evaluations/tracking_gt_diagnostics/task123_promoted_verify__20260517_173103`

| Clip | Recall@0.1 before | Recall@0.1 after | False-lock before | False-lock after | Decision |
|------|------------------:|-----------------:|------------------:|-----------------:|----------|
| `1_minie3_range_close` | 0.000 | 0.000 | 0.983 | 0.983 | unchanged; label/GT mismatch remains |
| `9_dji2_range_medium` | 0.275 | 0.275 | 0.036 | 0.036 | unchanged |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | 0.000 | 0.309 | 1.000 | 0.660 | major improvement |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | 0.387 | 0.892 | 0.614 | 0.109 | major improvement |

## Protection Gate

Compared candidate vs baseline on `configs/regression_pack_ir.csv` with the same
thresholds:

- baseline `antiuav_thermal_peak`: FAIL on known `Demo_IR_DRONE_146` id changes;
- candidate `antiuav_thermal_peak_osd_wide`: same FAIL reason, no new failure;
- `IR_BIRD_001` noise false-lock improved from `0.952` to `0.661`.

Because the failure is already present in baseline and candidate did not add a
new failure, the weak4 improvement is accepted for the thermal peak preset.

## Validation

Passed:

- `PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_night_source_authority.py tests/test_night_small_target_detector.py tests/test_profile_io.py -q`

## Decision

Accept OSD-wide ignore zone for `antiuav_thermal_peak`.

Do not yet propagate blindly to `tracking_live_auto` or every thermal preset.
That needs its own A/B because `tracking_live_auto` is the operator-facing
primary flow.

## Open TASK-20260517-124

Task: Tracking-live-auto OSD propagation gate.

Goal:

- test whether the same OSD-wide ignore zone should be applied to
  `tracking_live_auto.yaml`;
- no RTX;
- no training;
- no propagation without A/B.
