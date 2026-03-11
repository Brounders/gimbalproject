# BRIEF: BRIEF-20260311-007-evolution-cycle-v1

## Context
Human confirmed the next code evolution package:
1) quick KPI smoke,
2) operator mode Auto/Day/Night/IR,
3) point stabilization of target presentation and state transitions,
4) stage-0 GUI/pipeline decomposition preparation.

## Objective
Translate the confirmed direction into a minimal, testable implementation batch for Claude without changing training policy or performing a large refactor.

## Success Metrics
- A quick KPI smoke path exists and can be used before full benchmark.
- Operator-facing mode selection is reduced to Auto/Day/Night/IR with expert-only fine presets.
- Visual target presentation and state display are less noisy and more predictable without altering the decision loop wholesale.
- A stage-0 decomposition map exists for `app/main_gui.py` and `src/uav_tracker/pipeline.py`.

## Boundaries
- Must do:
  - minimal, reversible diffs;
  - keep runtime/UI boundaries explicit;
  - validate locally after each task.
- Must not do:
  - broad runtime rewrite;
  - hidden training-policy changes;
  - uncontrolled UI redesign beyond task scope.

## Deliverables
- 4 active Claude tasks for this cycle.
- Updated `active_plan`, `open_tasks`, `completed_tasks`, `project_state`.
