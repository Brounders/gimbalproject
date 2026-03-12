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
- Reviewed Claude reports:
  - `REPORT-20260311-029` -> Accepted
  - `REPORT-20260311-030` -> Accepted
  - `REPORT-20260311-031` -> Accepted
- Accepted tasks this loop:
  - `TASK-20260311-029`
  - `TASK-20260311-030`
  - `TASK-20260311-031`
- Runtime hardening around `epoch142` is complete:
  - auto-scene night/IR lock confirmation is stricter;
  - benchmark and quality-gate scripts now support `--model` override;
  - fresh candidate evaluation was completed without temporary committed presets.
- Final model decision:
  - imported RTX candidate `epoch142` remains `reject` / `hold_and_tune`
  - reason: persistent false-lock and ID-churn regressions on night/noise clips even after the short retune cycle
- No open Claude or RTX tasks remain in the current execution context.

## Latest Approved Direction
- Date: 2026-03-11
- Human approved a short retune cycle around imported RTX candidate `epoch142`.
- Locked facts:
  - training run `rtx_drone_stability_12h_v1` completed and artifact was ingested on Mac;
  - direct candidate gate failed and remained `hold_and_tune`;
  - targeted local sweep showed that simple stricter thresholds do not reliably recover operator-critical stability;
  - next cycle focuses on runtime false-lock suppression, clean candidate-eval override, and fresh post-retune gate.

## Latest Approved Direction
- Date: 2026-03-12
- Human approved a full 4-hour audit cycle across architecture, execution, and filesystem structure.
- Locked constraints:
  - analysis-only; no runtime or UI implementation in this cycle;
  - Claude may use commands and tools without asking Human between steps;
  - full access applies to analysis commands, but git remains non-destructive;
  - deliverable is one evidence-based audit report plus a prioritized roadmap.
- Active audit context:
  - `BRIEF-20260312-013-project-audit-4h`
  - `TASK-20260312-032`

## Latest Control Loop
- Date: 2026-03-12
- Reviewed Claude reports:
  - `REPORT-20260312-032` -> Accepted with caveat
- Accepted tasks this loop:
  - `TASK-20260312-032`
- Reviewer caveat:
  - audit report is accepted as the primary analysis artifact, but the claimed `MEMORY.md` inconsistency is not currently verifiable because `MEMORY.md` is absent from the repository.
- Outcome:
  - audit cycle is closed;
  - no active Claude or RTX tasks remain;
  - next implementation cycle must be opened explicitly from the audit roadmap.

## Latest Approved Direction
- Date: 2026-03-12
- Human approved the next rational steps after the first successful RTX conveyor smoke-run.
- Locked facts:
  - RTX -> GitHub Release -> Mac intake flow works end-to-end;
  - first candidate chunk for `drone-bird-yolo` remains `hold_and_tune`, not promoted;
  - current blockers are conveyor metadata correctness and quality-gate aggregate completeness, not artifact delivery.
- Active hardening context:
  - `BRIEF-20260312-014-conveyor-hardening-after-smoke`
  - `TASK-20260312-033`
  - `TASK-20260312-034`
  - `TASK-20260312-035`

## Latest Control Loop
- Date: 2026-03-12
- Reviewed Claude reports:
  - `REPORT-20260312-033` -> Accepted
  - `REPORT-20260312-034` -> Accepted
  - `REPORT-20260312-035` -> Accepted
- Accepted tasks this loop:
  - `TASK-20260312-033`
  - `TASK-20260312-034`
  - `TASK-20260312-035`
- Reviewer validation summary:
  - synthetic conveyor scan confirms `drone-bird-yolo -> scene_profile=mixed`
  - incomplete dataset is blocked with `status=blocked_no_images`
  - `next-chunk` skips blocked dataset and selects only valid datasets
  - `run_quality_gate.py` now writes aggregate JSON/CSV even when one clip raises `evaluate_error`
- Outcome:
  - conveyor metadata hardening cycle is closed;
  - aggregate quality-gate output is deterministic under clip-level failure;
  - no active Claude or RTX tasks remain.

## Latest Approved Direction
- Date: 2026-03-12
- Human approved the next implementation cycle derived from audit `032`, with one critical priority rule:
  - the final product is a local desktop program;
  - RTX/GitHub/web infrastructure is temporary and must not become the architectural center.
- Active local-product-integrity context:
  - `BRIEF-20260312-015-local-product-integrity-v1`
  - `TASK-20260312-043`
  - `TASK-20260312-044`
  - `TASK-20260312-045`

## Latest Control Loop
- Date: 2026-03-12
- Reviewed Claude reports:
  - `REPORT-20260312-043` -> Accepted
  - `REPORT-20260312-044` -> Accepted
  - `REPORT-20260312-045` -> Accepted
- Accepted tasks this loop:
  - `TASK-20260312-043`
  - `TASK-20260312-044`
  - `TASK-20260312-045`
- Reviewer validation summary:
  - `APP_STYLESHEET` now has an explicit maintained source in `app/ui/theme.py`
  - canonical operator presets now point to the stable local contract `models/baseline.pt`
  - legacy root scripts moved under `legacy/`, while `main_tracker.py` and `tracker_gui.py` remain canonical entrypoints
- Reviewer caveat:
  - `models/baseline.pt` is a local contract, not a tracked repository artifact; first-run setup still requires manually placing an accepted model there
- Outcome:
  - local product integrity cycle is closed;
  - no active Claude or RTX tasks remain;
  - next cycle can move to either dependency/reproducibility work or deeper architecture refactor.

## Latest Approved Direction
- Date: 2026-03-12
- Human approved the next implementation cycle from audit findings with local desktop product priority preserved.
- Locked scope:
  - phase 1 only: local reproducibility and quality discipline;
  - no deep refactor of `pipeline.py` / `main_gui.py` in this cycle;
  - no expansion of temporary RTX/GitHub/web infrastructure as product architecture.
- Active context:
  - `BRIEF-20260312-016-local-reproducibility-and-quality-v1`
  - `TASK-20260312-046`
  - `TASK-20260312-047`
  - `TASK-20260312-048`
