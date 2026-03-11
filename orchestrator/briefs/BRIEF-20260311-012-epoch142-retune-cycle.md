# BRIEF: BRIEF-20260311-012-epoch142-retune-cycle

## Summary
- Human approved the next rational step after RTX candidate intake:
  1. do not launch new training yet;
  2. apply a short code cycle around the completed `epoch142` model;
  3. suppress false locks and ID churn on the weakest night/noise scenes;
  4. retune the runtime around `epoch142`;
  5. rerun benchmark + quality gate before any promotion decision.

## Facts Locked In
- RTX run `rtx_drone_stability_12h_v1` completed successfully:
  - `epochs_done_total=142`
  - `exit_reason=completed`
  - export artifact was fixed and ingested on Mac.
- Candidate artifact is available locally:
  - `imports/rtx_drone_stability_12h_v1_20260311_204026/best.pt`
- Current intake decision remains `hold_and_tune`, not `promote`.
- Baseline versus candidate comparison on the current code shows regressions on operator-critical scenes:
  - `night_ground_large_drones`
  - `Demo_IR_DRONE_146`
  - `night_ground_indicator_lights`
- Main regressions:
  - `false_lock_rate`
  - `active_id_changes_per_min`

## Scope
- In scope:
  - harden runtime false-lock suppression for night/IR/noise conditions;
  - provide a clean candidate-model evaluation path without editing canonical operator presets by hand;
  - rerun candidate evaluation and record an explicit decision.
- Out of scope:
  - new RTX training launch;
  - major GUI redesign;
  - runtime-wide rewrite.

## Success Criteria
- A focused runtime/task cycle exists for reducing false locks around `epoch142`.
- Candidate evaluation no longer depends on ad hoc temporary preset hacking.
- `epoch142` receives an explicit post-retune decision based on fresh benchmark/gate data.
