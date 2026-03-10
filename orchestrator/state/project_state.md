# Project State

## Mission
- Система стабильного обнаружения и сопровождения БПЛА (день/ночь/IR) с подготовкой к переносу на RPi5 + Hailo.

## Current Phase
- Phase: stabilization-first
- Priority: lock stability + deterministic quality-gate

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

## Control Loop Snapshot (2026-03-11)
- Reviewed Claude reports: 2
  - REPORT-20260311-001 -> Accepted
  - REPORT-20260311-002 -> Accepted
- Accepted tasks this loop: 2
  - TASK-20260311-001
  - TASK-20260311-002
- Rejected tasks this loop: none
- New brief created: `BRIEF-20260311-002-testability-and-stability-hardening`.
- New Claude tasks opened: 2
  - TASK-20260311-003
  - TASK-20260311-004
- New RTX training tasks opened this loop: 0 (TRAIN-20260311-001 remains active)

## Active Baseline Policy
- Candidate policy: promote only after quality-gate PASS.
- RTX artifacts are ingested and evaluated on Mac before release.

## Current Risks
- Package-level import coupling still needs hardening (TASK-20260311-003).
- select_active regression coverage is still partial until TASK-20260311-004.
- Training throughput depends on discipline of curriculum state updates on RTX side.
