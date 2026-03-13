# Active Plan

## Plan ID
- AP-20260313-025

## Source Direction
- Human approved the next implementation cycle after acceptance of the large-target night detector/runtime contract cycle.
- Scope: a narrow large-target night runtime fix focused on continuity gating, reacquire/release guard behavior, and a hard evidence gate.
- Priority: do not open training, refactor, UI, or embedded work; focus only on the unresolved large-target night runtime defect.

## Status
- Done

## Brief In Focus
- BRIEF-20260313-028-large-target-night-runtime-fix-v1

## Active Claude Tasks (execution allowed now)
- TASK-20260313-081 | large-target continuity gating | Open
- TASK-20260313-082 | large-target reacquire/release guard | Open
- TASK-20260313-083 | large-target hard gate evidence | Open

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [x] `night_ground_large_drones` improves beyond the current accepted point (false_lock=0.510, id_chg=12.23 — both PASS gate)
- [x] `night_ground_indicator_lights` does not regress (false_lock=0.096, id_chg=0.00 — PASS gate)
- [x] The cycle yields one hard-gate before/after verdict — verdict: `improvement`, night gate PASS
