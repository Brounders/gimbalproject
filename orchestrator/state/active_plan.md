# Active Plan

## Plan ID
- AP-20260312-020

## Source Direction
- Human direction: move to the next stage after runtime hardening stage-2.
- Scope: runtime hardening stage-3 only — narrow the remaining night/noise problem, fix `night_ground_large_drones` stability, and turn the problem pack into a threshold-based mini-gate.

## Status
- Done

## Brief In Focus
- BRIEF-20260312-023-runtime-hardening-stage3-v1

## Active Claude Tasks (execution allowed now)
- TASK-20260312-067 | night-noise scene classification gating | Done
- TASK-20260312-068 | large-drones night stability fix | Done
- TASK-20260312-069 | problem-pack threshold contract | Done

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [x] noise-like night scenes are handled more narrowly than generic night behavior
- [x] `night_ground_large_drones` no longer shows runaway instability in the short smoke loop
- [x] the problem pack has one explicit threshold-based mini-gate for future runtime cycles
