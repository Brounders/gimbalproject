# BRIEF: BRIEF-20260311-008-tracking-hardening-no-redesign

## Context
Human confirmed the next implementation package:
1) restore target box overlay with target ID instead of reticle,
2) investigate and correct Auto mode scene recognition for night scenes,
3) reduce target jitter and improve smooth/stable target following in night conditions,
4) explicitly exclude major UI redesign from this cycle.

## Objective
Translate the confirmed direction into a small, testable Claude batch that hardens the operator-visible tracking behavior without broad architectural rewrite.

## Success Metrics
- Base operator overlay shows a target-aligned box with target ID; reticle is not shown by default.
- Auto mode reliably selects night behavior on obvious night scenes and does not oscillate between scene modes.
- Night target presentation and tracking feel noticeably less jittery through local smoothing/hold logic.
- No large-scale GUI redesign is attempted in this cycle.

## Boundaries
- Must do:
  - minimal, reversible diffs;
  - preserve runtime/UI separation;
  - validate with local compile/smoke where possible.
- Must not do:
  - broad UI redesign;
  - full lock-policy rewrite;
  - hidden training/model changes.

## Deliverables
- 3 active Claude tasks.
- Updated `active_plan`, `open_tasks`, `project_state`.
