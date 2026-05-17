# REPORT-TARGET-LAB-ACT3-GATE-20260516

## Verdict

ACCEPTED.

Act 3 source-aware IR preset routing is kept as the current tracker diagnostic
baseline for the next tracking evolution pass.

## Scope

Accepted changes:

- Target Lab scene-aware diagnostics now route most IR clips through
  `antiuav_thermal_peak`.
- Known OSD/airplane IR sources remain on `antiuav_thermal_field_osd` to avoid
  reverting the Act 2 OSD-safety fix.
- EO and night routing from Act 2 is preserved.

No training change, model promotion, production model replacement, or async
scheduler change is part of this decision.

## Evidence

Previous accepted baseline:

- `runs/evaluations/tracking_gt_diagnostics/target_lab_act2_20260516_142723/summary.json`

Accepted candidate:

- `runs/evaluations/tracking_gt_diagnostics/target_lab_act3b_20260516_150258/summary.json`

Preset battle reports used before selecting the bounded fix:

- `runs/evaluations/tracking_gt_diagnostics/act3_antiuav_thermal_field_osd_20260516_144311`
- `runs/evaluations/tracking_gt_diagnostics/act3_antiuav_thermal_hotspot_20260516_144635`
- `runs/evaluations/tracking_gt_diagnostics/act3_antiuav_thermal_peak_20260516_144928`
- `runs/evaluations/tracking_gt_diagnostics/act3_antiuav_thermal_motion_20260516_145144`

Risk count:

- Act 2: 25
- Act 3b: 21

Scene deltas:

| Scene | Recall | Missed | Off-target | FPS |
|---|---:|---:|---:|---:|
| EO | 0.533 -> 0.465 | 0.446 -> 0.514 | 0.023 -> 0.023 | 38.8 -> 30.5 |
| EO_NEGATIVE | 0.950 -> 0.950 | 0.040 -> 0.040 | 0.013 -> 0.013 | 88.2 -> 78.4 |
| IR | 0.103 -> 0.556 | 0.517 -> 0.113 | 0.380 -> 0.331 | 47.8 -> 50.8 |
| IR_NEGATIVE | 0.185 -> 0.185 | 0.752 -> 0.752 | 0.063 -> 0.063 | 23.3 -> 16.4 |
| NEGATIVE | 0.046 -> 0.046 | 0.954 -> 0.954 | 0.000 -> 0.000 | 21.0 -> 15.4 |
| UNKNOWN | 0.000 -> 0.000 | 0.000 -> 0.010 | 0.995 -> 0.984 | 47.3 -> 40.3 |

Key IR clip improvements:

| Clip | Preset | Recall | Missed | Off-target |
|---|---|---:|---:|---:|
| `5_minie3_range_far` | `antiuav_thermal_peak` | 0.040 -> 0.871 | 0.903 -> 0.054 | 0.057 -> 0.075 |
| `IR_DRONE_025` | `antiuav_thermal_peak` | 0.043 -> 0.987 | 0.732 -> 0.013 | 0.223 -> 0.007 |
| `f2_13_IR_dji_mavic_2` | `antiuav_thermal_peak` | 0.028 -> 0.707 | 0.733 -> 0.026 | 0.239 -> 0.267 |
| `9_dji2_range_medium` | `antiuav_thermal_peak` | 0.005 -> 0.276 | 0.968 -> 0.688 | 0.026 -> 0.036 |

## Decision Rationale

The fix is accepted because it attacks the specific Act 3 problem without
undoing Act 2:

- IR missed-visible rate drops sharply on the drone/minidrone clips.
- Overall diagnostic risk count drops from 25 to 21.
- OSD-sensitive AntiUAV RGBT and airplane clips stay on the safer OSD profile.

The tradeoff is explicit:

- This does not solve `antiuav_rgbt_20190925_200805_1_2_infrared`.
- This does not solve `IR_AIRPLANE_014`.
- EO recall and FPS move down in the latest full run, even though EO routing was
  not intentionally changed.  Treat this as a measurement warning for the next
  pass, not as permission to revert Act 2.
- Bbox size stability remains unsolved.
- Reacquire still grabs trees/background in several clips.

## Next Pass

Act 4 should not change model weights and should not introduce an async
scheduler.  The next bounded lever is bbox/reacquire stability:

1. reduce too-small/too-large tracking boxes;
2. hold a short predicted region after target loss;
3. avoid reacquiring trees, grass, OSD, or unrelated background;
4. A/B validate against the accepted Act 3b baseline.
