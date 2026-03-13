# Brief: Model Decision Cycle v1

## Brief ID
- BRIEF-20260313-029

## Why Now
- `AP-20260313-025` delivered the first accepted PASS on the night problem-pack mini-gate.
- Published RTX curriculum artifacts for `drone-bird-yolo` already exist and can now be re-evaluated under the accepted runtime.
- Before any new training or strategy reset, the project needs one explicit decision on the current model branch.

## Scope
- Local Mac-side model decision cycle only.
- Verify the current baseline contract operationally.
- Re-intake already published curriculum candidates under the current accepted runtime.
- Produce one explicit branch decision for the current curriculum branch.

## Objectives
1. Verify whether the current Mac baseline contract is operational and complete.
2. Re-evaluate published `drone-bird-yolo` curriculum candidates using the accepted local `day/night/ir` quality flow.
3. Produce one explicit decision for the current model branch:
   - `promote`
   - `hold_and_tune`
   - `reject_and_reset_training_strategy`

## Deliverables
- One baseline operational check report.
- One published-candidate re-intake comparison report.
- One explicit branch decision artifact and summary.

## Out Of Scope
- New RTX training.
- Runtime code changes.
- GUI refactor or redesign.
- Hailo / embedded work.
