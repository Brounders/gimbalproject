# Project State

## Mission
- Система стабильного обнаружения и сопровождения БПЛА (день/ночь/IR) с подготовкой к переносу на RPi5 + Hailo.

## Current Phase
- Phase: stabilization-first → tooling-integration
- Priority: test coverage completeness + observability integration into stable cycle

## Runtime Policy
- Runtime code changes only via explicit task.
- UI/business/runtime boundaries must remain isolated.

## Agent Topology
- Human: orchestrator
- Codex Mac: architect/planner/reviewer
- Claude Mac: implementation lead
- Codex RTX: training/evaluation worker

## Control Loop Snapshot (2026-03-11, loop 4)

### Reviews completed this loop
- REPORT-20260311-003 (package import decoupling) → ACCEPT
- REPORT-20260311-004 (select_active policy tests) → ACCEPT
- REPORT-20260311-005 (lock-events analyzer) → ACCEPT
- REPORT-20260311-006 (profile preset validator) → ACCEPT

### Briefs closed this loop
- BRIEF-20260311-003 (observability + config hygiene) — FULLY DELIVERED
  - TASK-003: lazy import boundary DONE
  - TASK-004: select_active policy tests DONE
  - TASK-005: analyze_lock_events.py DONE
  - TASK-006: validate_profile_presets.py DONE

### New brief created this loop
- BRIEF-20260311-004-tooling-integration-and-test-hardening

### New Claude tasks created this loop
- TASK-20260311-010 (P2): primary vs primary score test (follow-up REPORT-004)
- TASK-20260311-011 (P2): validator auto-types from Config (follow-up REPORT-006)
- TASK-20260311-012 (P2): stable-cycle preset preflight integration

### Carry-over open tasks (filesystem audit brief)
- TASK-20260311-007 (P1): filesystem-inventory
- TASK-20260311-008 (P1): filesystem-classification
- TASK-20260311-009 (P2): safe-reorg-plan

### Open training jobs
- TRAIN-20260311-001 (still open — waiting for RTX)

## Active Baseline Policy
- Candidate policy: promote only after quality-gate PASS.
- RTX artifacts ingested and evaluated on Mac before release.

## Cumulative Test Coverage
- test_package_import: 3 tests, Green
- test_target_manager_lock_policy: 12 tests, Green
- test_analyze_lock_events: 11 tests, Green
- test_validate_profile_presets: 14 tests, Green
- Total: 40 tests, OK

## Current Risks
- TASK-007/008 (filesystem audit, P1) still open — highest priority for Claude.
- TRAIN-20260311-001 on RTX: no status update received.
- _TYPE_RULES in validate_profile_presets.py duplicates Config types — addressed by TASK-011.
- Smoke run on real video not done (no test clip available).
