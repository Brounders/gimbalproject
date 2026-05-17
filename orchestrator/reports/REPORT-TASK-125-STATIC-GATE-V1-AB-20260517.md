# TASK-20260517-125 — Static-target rejection v1 A/B

## Status

Runtime infrastructure added, candidate not promoted.

## Implemented

- Added default-off config fields:
  - `STATIC_TARGET_REJECTION_ENABLED`
  - `STATIC_TARGET_SOURCES`
  - `STATIC_TARGET_MOTION_THRESH`
  - `STATIC_TARGET_MIN_MOTION_RATIO`
  - `STATIC_TARGET_STREAK_MIN`
  - `STATIC_TARGET_PENALTY`
- Added bbox-local motion/static evidence on `TrackedTarget`:
  - `motion_score`
  - `static_streak`
- Added selector penalty in `build_proposals()` only when the gate is enabled.
- Added candidate preset `configs/antiuav_thermal_peak_static_gate.yaml`.
- Added unit coverage in `tests/test_static_target_rejection.py`.

Production/default behavior remains unchanged because the gate is off by
default.

## A/B result

Baseline:
`runs/evaluations/tracking_gt_diagnostics/task125_baseline_20260517_182537`

Candidate:
`runs/evaluations/tracking_gt_diagnostics/task125_static_gate_20260517_182752`

| Clip | Recall baseline -> candidate | False-lock baseline -> candidate | Decision |
|---|---:|---:|---|
| `1_minie3_range_close` | `0.000 -> 0.000` | `0.983 -> 0.983` | no movement |
| `9_dji2_range_medium` | `0.275 -> 0.275` | `0.036 -> 0.036` | no movement |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | `0.309 -> 0.313` | `0.660 -> 0.656` | tiny improvement only |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | `0.890 -> 0.890` | `0.111 -> 0.111` | no movement |

## Decision

Do not promote static-target rejection v1 as a tracker improvement.  It is a
safe default-off infrastructure layer, but it does not break the current weak4
ceiling.

The likely reason is that the current false-locks are not only "static text";
they are a mix of:

- primary YOLO/local confirmation on wrong high-contrast geometry;
- template lock holding wrong texture after acquisition;
- weak/absent true-target proposals;
- clip-specific OSD contamination.

## Next

The next tracker logic candidate should use richer evidence:

1. candidate motion relative to local background;
2. trajectory plausibility from center history;
3. size/shape plausibility against scene and previous bbox;
4. primary detector support versus lock/local self-confirmation.

This should be designed as evidence telemetry first, then an A/B gate.
