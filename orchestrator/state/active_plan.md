# Active Plan

## Plan ID
- AP-20260312-021

## Source Direction
- Human direction: implement the next stage after runtime hardening stage-3.
- Scope: runtime hardening stage-4 only — tighten night/noise runtime behavior for the two worst problem scenes, and turn the problem-pack mini-gate into a real short acceptance barrier.

## Status
- Active

## Brief In Focus
- BRIEF-20260312-024-runtime-hardening-stage4-v1

## Active Claude Tasks (execution allowed now)
- TASK-20260312-070 | indicator lights noise gating | Open
- TASK-20260312-071 | large drones night stability fix | Open
- TASK-20260312-072 | problem-pack mini-gate enforcement | Open

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [ ] `night_ground_indicator_lights` is more tightly bounded in the short problem-pack loop
- [ ] `night_ground_large_drones` no longer shows runaway `id_changes/min` behavior in the short loop
- [ ] the problem-pack mini-gate acts as a real short acceptance barrier for future runtime cycles
