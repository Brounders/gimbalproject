# TASK: TASK-20260502-091 — FPID-004 weak-evidence suppressor

Task ID: TASK-20260502-091
Alias: FPID-004
Status: Ready
Owner: Claude Code
Plan: AP-FP-ID-SUPPRESSOR-V1

## Goal

Implement a bounded weak-evidence suppressor in `ActionPolicy` so the guarded ON path can drop clearly weak `night` / `roi` false locks earlier, without weakening accepted day/IR target retention.

## Decision Context

Codex completed FPID-001/002/003 in commit `f74e065`.

Read first:

- `orchestrator/reports/REPORT-FP-ID-SUPPRESSOR-V1-20260502.md`
- `docs/superpowers/plans/2026-05-02-fp-id-suppressor-v1.md`
- `orchestrator/state/active_plan.md`
- `orchestrator/state/open_tasks.md`

Auditor verdict after Codex checkpoint:

- `noise-airplane` false locks are weak `night` evidence, not YOLO:
  - `false_lock_source_counts={'night': 62}`
  - `avg_target_reliability=0.0434`
  - `avg_target_p_present=0.1330`
- visible-night diagnostic false locks are weak `night` / `roi` evidence, not YOLO.
- `POLICY_SUPPRESSOR_CANDIDATE` is valid.
- `target_modality` in offline gates currently remains `rgb`; do not rely on `modality` as the primary condition.

## Scope

Allowed files:

- `src/uav_tracker/tracking/action_policy.py`
- `src/uav_tracker/tracking/evidence.py` only if needed for source normalization helpers
- `src/uav_tracker/pipeline.py` only for `TargetBelief.source` normalization, not broad pipeline rewrites
- `tests/test_action_policy.py`
- `tests/test_action_policy_behavior.py`
- `tests/test_tracking_evidence.py`
- `python_scripts/run_action_policy_gate.py` only if compact telemetry formatting needs a test-safe change
- `orchestrator/reports/REPORT-FP-ID-SUPPRESSOR-IMPLEMENTATION-20260502.md`
- `orchestrator/state/completed_tasks.md` after validation
- `orchestrator/state/open_tasks.md` / `orchestrator/state/active_plan.md` only to mark this exact task completed after successful validation

## Non-Scope

Do not:

- change baseline model;
- run or modify training;
- add dependencies;
- change GUI;
- replace `TargetManager`;
- replace `TemplateLockTracker`;
- change gate thresholds to make failures pass;
- enable `ACTION_POLICY_BEHAVIOR_ENABLED=True` by default;
- suppress fresh `yolo` evidence;
- broadly suppress `lock` / `local` in IR clips;
- make decisions based primarily on `belief.modality`, because offline gates currently report `target_modality='rgb'`.

## Required Implementation Shape

Use TDD.

Add source normalization if needed so `TargetBelief.source` is stable:

- expected stable values: `yolo`, `local`, `roi`, `lock`, `night`, `-`.
- enum-like strings such as `DetectionSource.NIGHT` must not be required by policy rules.

Candidate rule shape:

```python
if (
    belief.source in {"night", "roi"}
    and belief.reliability <= 0.20
    and belief.p_present <= 0.40
    and belief.lost_age >= 1
):
    return TrackingAction.DROP_LOCK
```

If gate data proves this exact predicate is too aggressive, tune conservatively. Do not widen to `yolo`. Do not widen to all `lock/local` without separate proof and Codex review.

## Required Tests

Add focused tests in `tests/test_action_policy.py`:

- weak `night` source drops when reliability and `p_present` are low;
- weak `roi` source drops when reliability and `p_present` are low;
- fresh/high-confidence `yolo` is not suppressed by this rule;
- `lock` / `local` are not suppressed by the first implementation unless there is explicit telemetry proof;
- IR-like belief with `lock/local` continuity still avoids broad suppression;
- existing modality-aware tests continue to pass.

If source normalization is added, cover it in `tests/test_tracking_evidence.py` or `tests/test_action_policy.py`.

## Acceptance Criteria

- Blocking promotion gate remains PASS.
- `noise-airplane` `false_lock` decreases materially, or the report explains why the predicate did not affect it.
- Day and IR presence do not materially drop:
  - day `delta_presence >= -0.01`;
  - IR `delta_presence >= -0.01`;
  - `delta_hits_iou_01 >= -2`.
- Noise clips do not increase `presence` or `false_lock`.
- Diagnostic-night remains non-blocking and records any regressions in `diagnostic_reasons`.
- OFF sanity remains true: `off_behavior_drop_count=0`.

## Validation

Run serially, not in parallel:

```bash
PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_tracking_evidence.py tests/test_action_policy.py tests/test_action_policy_behavior.py tests/test_action_policy_gate.py tests/test_evaluation_telemetry.py -q
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_candidate_
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_candidate_
PYTHONPATH=src tracker_env/bin/python -m compileall -q python_scripts src app orchestrator tests
git diff --check
PYTHONPATH=src tracker_env/bin/python orchestrator/scripts/check_orchestration_state.py
```

Expected:

- tests pass;
- blocking gate PASS;
- diagnostic gate PASS/non-blocking;
- compileall OK;
- whitespace clean;
- orchestration state OK.

## Report

Write `orchestrator/reports/REPORT-FP-ID-SUPPRESSOR-IMPLEMENTATION-20260502.md` with:

- exact rule implemented;
- tests added;
- before/after metrics for:
  - `drone_detection_V_AIRPLANE_001`;
  - `night_ground_large_drones`;
  - both Anti-UAV visible-night clips;
  - day-mixkit;
  - both IR clips;
- whether `noise-airplane` improved;
- whether day/IR margins stayed safe;
- any diagnostic-night regressions;
- final decision: `PASS`, `RETUNE`, or `REJECT`.

## Stop Condition

Stop after this task. Do not choose the next task. Do not start model/dataset work.
