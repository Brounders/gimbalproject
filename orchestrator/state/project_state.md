# Project State

## Mission
- Система стабильного обнаружения и сопровождения БПЛА (день/ночь/IR) с подготовкой к переносу на RPi5 + Hailo.

## Current Phase
- Phase: stabilization-first
- Priority: lock stability + deterministic quality-gate

## Runtime Policy
- Runtime code changes only via explicit task.
- UI/business/runtime boundaries must remain isolated.

## Agent Topology
- Human: orchestrator
- Codex Mac: architect/planner/reviewer
- Claude Mac: implementation lead
- Codex RTX: training/evaluation worker

## Control Loop Snapshot (2026-03-11)
- Reviewed Claude reports: none (no files in `orchestrator/reports`).
- Accepted tasks this loop: none.
- Rejected tasks this loop: none.
- New brief created: `BRIEF-20260311-001-stability-loop`.
- New Claude tasks opened: 2.
- New RTX training tasks opened: 1.

## Active Baseline Policy
- Candidate policy: promote only after quality-gate PASS.
- RTX artifacts are ingested and evaluated on Mac before release.

## Current Risks
- `pipeline.py` remains large; extraction must stay behavior-safe.
- Test coverage for lock policy is still minimal until TASK-20260311-002 is done.
- Training throughput depends on curriculum/state discipline on RTX side.
