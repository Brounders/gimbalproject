# Project State

## Mission
- Система стабильного обнаружения и сопровождения БПЛА (день/ночь/IR) с подготовкой к переносу на RPi5 + Hailo.

## Current Phase
- Phase: stabilization-first
- Priority: quick smoke + operator simplification + target/state stabilization

## Runtime Policy
- Runtime code changes only via explicit task.
- UI/business/runtime boundaries must remain isolated.

## Active Context Pointer
- Active execution context: `orchestrator/state/active_plan.md`
- Backlog index: `orchestrator/state/open_tasks.md`
- Rule: execution priority is always defined by `active_plan.md`.

## Agent Topology
- Human: orchestrator
- Codex Mac: architect/planner/reviewer
- Claude Mac: implementation lead
- Codex RTX: training/evaluation worker

## Control Loop Snapshot (2026-03-11, audit loop)
- Reviewed Claude reports this loop: 2
  - REPORT-20260311-003 -> Accepted
  - REPORT-20260311-004 -> Accepted
- Accepted tasks this loop:
  - TASK-20260311-003
  - TASK-20260311-004
- New brief created:
  - BRIEF-20260311-005-audit-and-next-goals
- New Claude tasks opened:
  - TASK-20260311-013
  - TASK-20260311-014
  - TASK-20260311-015
- Open RTX training context:
  - TRAIN-20260311-001 (awaiting status sync on Mac)

## Active Baseline Policy
- Candidate policy: promote only after quality-gate PASS.
- RTX artifacts are ingested and evaluated on Mac before release.

## Current Risks
- Monolith risk: `app/main_gui.py` and `src/uav_tracker/pipeline.py` remain large and tightly coupled.
- Entry-point ambiguity at repository root may cause operator mistakes.
- CI does not yet enforce full unit-test stage by default.
- Training throughput depends on discipline of curriculum state updates on RTX side.
- Potential state drift if `active_plan.md` is updated without `open_tasks.md`/`completed_tasks.md` sync.

## Latest Control Loop
- Date: 2026-03-11
- Directly closed `TASK-20260311-028` by reconciling `OPERATOR_BASELINE.md` with current preset YAML.
- `TASK-20260311-027` is now fully accepted.
- Corrected fields:
  - `night.imgsz = 960`
  - `antiuav_thermal.imgsz = 960`
  - `antiuav_thermal.conf_thresh = 0.12`
  - `small_target.conf_thresh = 0.15`
- No open RTX training task in the current execution context.

## Latest Approved Direction
- Date: 2026-03-11
- Human approved a short retune cycle around imported RTX candidate `epoch142`.
- Locked facts:
  - training run `rtx_drone_stability_12h_v1` completed and artifact was ingested on Mac;
  - direct candidate gate failed and remained `hold_and_tune`;
  - targeted local sweep showed that simple stricter thresholds do not reliably recover operator-critical stability;
  - next cycle focuses on runtime false-lock suppression, clean candidate-eval override, and fresh post-retune gate.
