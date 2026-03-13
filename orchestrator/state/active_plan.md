# Active Plan

## Plan ID
- AP-20260313-024

## Source Direction
- Human approved the next implementation cycle after the corrected adversarial review.
- Scope: a narrow large-target night detector/runtime contract cycle derived from the accepted unified conclusion.
- Priority: do not open training, refactor, UI, or embedded work; focus only on exposing and tuning detector-level night knobs and proving the effect on the night problem pack.

## Status
- Completed

## Brief In Focus
- BRIEF-20260313-027-large-target-night-detector-contract-v1

## Active Claude Tasks (execution allowed now)
- (none)

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [x] Detector-level night knobs `NIGHT_MAX_AREA`, `NIGHT_TRACK_DIST`, `NIGHT_LOST_MAX` are exposed through the profile/YAML contract.
- [~] `night_ground_large_drones` improves beyond the current stage-4b reference point without regression on `night_ground_indicator_lights`. (id_chg/min improved −44%, false_lock marginal regression +0.021; indicator_lights no regression)
- [x] A reproducible before/after evidence loop exists on the night problem pack with an explicit verdict.
