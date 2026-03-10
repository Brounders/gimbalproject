# Project State

## Mission
- Система стабильного обнаружения и сопровождения БПЛА (день/ночь/IR) с подготовкой к переносу на RPi5 + Hailo.

## Current Phase
- Phase: stabilization-first → tooling-integration
- Priority: test coverage completeness + observability integration into stable cycle

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

## Control Loop Snapshot (2026-03-11, loop 5)

### Reviews completed this loop
- REPORT-20260311-003 (package import decoupling) → ACCEPT
- REPORT-20260311-004 (select_active policy tests) → ACCEPT
- REPORT-20260311-005 (lock-events analyzer) → ACCEPT
- REPORT-20260311-006 (profile preset validator) → ACCEPT
- REPORT-20260311-007..012 (filesystem/tooling tasks) → ACCEPTED/DONE

### Briefs closed this loop
- BRIEF-20260311-003 (observability + config hygiene) — FULLY DELIVERED
  - TASK-003: lazy import boundary DONE
  - TASK-004: select_active policy tests DONE
  - TASK-005: analyze_lock_events.py DONE
  - TASK-006: validate_profile_presets.py DONE
- BRIEF-20260311-004 (filesystem architecture audit) — CLOSED

### New brief created this loop
- (none)

### New Claude tasks created this loop
- (none; active plan currently does not require Claude execution)

### Carry-over open tasks (filesystem audit brief)
- (none)

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
- TRAIN-20260311-001 on RTX: no status update received.
- Smoke run on real video not done (no test clip available).
- Potential state drift if `active_plan.md` is updated without `open_tasks.md`/`completed_tasks.md` sync.
