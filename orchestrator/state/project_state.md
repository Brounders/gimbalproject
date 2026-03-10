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
- Claude reports reviewed this loop: 2
  - REPORT-20260311-001 -> Accepted
  - REPORT-20260311-002 -> Accepted
- Accepted tasks this loop:
  - TASK-20260311-001
  - TASK-20260311-002
- Rejected tasks this loop: none
- New architecture brief:
  - BRIEF-20260311-003-observability-and-config-hygiene
- New Claude tasks created this loop:
  - TASK-20260311-005
  - TASK-20260311-006
- Open training jobs:
  - TRAIN-20260311-001 (still open)

## Active Baseline Policy
- Candidate policy: promote only after quality-gate PASS.
- RTX artifacts are ingested and evaluated on Mac before release.

## Current Risks
- Import boundary hardening не завершен (TASK-20260311-003).
- Coverage по `select_active` еще неполная (TASK-20260311-004).
- Training cycle зависит от корректного обновления curriculum state на RTX.
