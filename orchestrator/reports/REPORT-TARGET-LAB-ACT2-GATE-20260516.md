# REPORT-TARGET-LAB-ACT2-GATE-20260516

## Verdict

ACCEPTED.

Act 2 source-conflict fix is kept as the current baseline for the next tracking
evolution pass.

## Scope

Accepted changes:

- EO/day `small_target` preset no longer runs the night/MOG2 detector.
- Target Lab scene-aware GT diagnostics route IR clips through
  `antiuav_thermal_field_osd`.
- Target Lab scene-aware GT diagnostics route night clips through
  `night_field_osd`.

No model promotion, training change, or production model replacement is part of
this decision.

## Evidence

Baseline report:

- `runs/evaluations/tracking_gt_diagnostics/target_lab_act1_20260516_112807/summary.json`

Candidate report:

- `runs/evaluations/tracking_gt_diagnostics/target_lab_act2_20260516_142723/summary.json`

Risk count:

- Act 1: 37
- Act 2: 25

Scene deltas:

| Scene | Recall | Missed | Off-target | FPS |
|---|---:|---:|---:|---:|
| EO | 0.554 -> 0.533 | 0.185 -> 0.446 | 0.280 -> 0.023 | 42.2 -> 50.5 |
| EO_NEGATIVE | 0.952 -> 0.950 | 0.026 -> 0.040 | 0.024 -> 0.013 | 72.6 -> 88.2 |
| IR | 0.083 -> 0.103 | 0.516 -> 0.517 | 0.401 -> 0.380 | 57.5 -> 52.2 |
| IR_NEGATIVE | 0.185 -> 0.185 | 0.752 -> 0.752 | 0.063 -> 0.063 | 15.7 -> 23.3 |
| NEGATIVE | 0.046 -> 0.046 | 0.954 -> 0.954 | 0.000 -> 0.000 | 14.8 -> 21.0 |
| UNKNOWN | 0.008 -> 0.000 | 0.000 -> 0.000 | 0.987 -> 0.995 | 71.8 -> 47.3 |

## Decision Rationale

The fix is accepted because it sharply reduces EO off-target behavior:

- EO off-target drops from 0.280 to 0.023.
- EO FPS improves from 42.2 to 50.5.
- Overall diagnostic risk count drops from 37 to 25.

The tradeoff is explicit:

- EO missed-visible increases from 0.185 to 0.446.
- This means the tracker now more often says "I do not see it" instead of
  grabbing grass/tree/background via night/MOG2.

For operator safety, missed detection is a better failure mode than a confident
wrong lock.  Missed detection can be addressed in the next pass through
candidate sensitivity, reacquire, and model/data work.  False active background
locks are more dangerous and should be suppressed first.

## Next Pass

Act 3 should not revert this fix.  It should address:

1. IR missed detection: visible target does not become a candidate.
2. Bbox-size stability: target is inside the bbox but the bbox is too small or
   too large.
3. Reacquire behavior: temporary target loss should hold a predicted region
   without grabbing trees, grass, OSD, or background.

Act 3 must remain bounded and A/B validated.
