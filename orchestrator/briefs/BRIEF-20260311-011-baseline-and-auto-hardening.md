# BRIEF: BRIEF-20260311-011-baseline-and-auto-hardening

## Summary
- Human approved execution of the next 5 logical steps:
  1. close the current RTX -> Mac -> quality-gate loop;
  2. run a short operational smoke on real clips;
  3. harden `Auto` toward full `Day / Night / IR`;
  4. freeze the operator baseline;
  5. close the canonical runbook/entrypoint task.

## Facts Locked In
- Mac-side training intake for `TRAIN-20260311-001` is already evaluable from existing artifacts.
- Stable-cycle decision for the current RTX candidate is `hold_and_tune`:
  - quality gate did not pass;
  - next action: retune IR-noise thresholds / lock confirm.
- A fresh quick smoke was run on the current operator baseline (`default` preset):
  - aggregate: `fps=85.2`, `id_chg/min=14.68`, `false_lock=0.724`
  - weakest scenes: `night_ground_large_drones`, `IR_BIRD_001`, `Demo_IR_DRONE_146`

## Scope
- In scope:
  - close training intake state on Mac;
  - define the next code cycle around `Auto`, operator baseline, and canonical runbook;
  - keep changes minimal and verifiable.
- Out of scope:
  - new RTX training launch;
  - major GUI redesign;
  - runtime-wide rewrite.

## Success Criteria
- Training intake state is no longer dangling in `open_training.md`.
- `Auto` has an explicit path toward `Day / Night / IR` instead of day/night-only behavior.
- Operator baseline is documented from real smoke data.
- `RUNBOOK.md` becomes the single source of truth for launch commands.
