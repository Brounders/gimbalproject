# Active Plan

## Plan ID
- AP-20260312-011

## Source Direction
- Human direction: apply the next rational steps after the first successful RTX -> GitHub -> Mac conveyor smoke-run.
- Scope: fix conveyor metadata defects and restore reliable aggregate quality-gate before enabling scheduled automation.

## Status
- Completed

## Brief In Focus
- BRIEF-20260312-014-conveyor-hardening-after-smoke

## Active Claude Tasks (execution allowed now)
- (none)

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- Dataset registry no longer misclassifies `drone-bird-yolo` as `ir`.
- Broken datasets are blocked instead of being queued for training.
- Full regression pack quality-gate produces reliable aggregate artifacts for candidate intake.
