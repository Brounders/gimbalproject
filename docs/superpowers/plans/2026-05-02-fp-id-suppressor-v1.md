# FP/ID Suppressor V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce false active locks and visible-night ID churn without weakening accepted day/IR target retention.

**Architecture:** Keep the current detector, model, `TargetManager`, and `TemplateLockTracker`. Add measurement first, then only add guarded `ActionPolicy` suppression rules where runtime evidence proves the active target is weak or unstable. If a false lock is a high-confidence YOLO/model false positive with no runtime-discriminating signal, do not hide it with policy thresholds; record that as a detector/model task.

**Tech Stack:** Python, pytest, existing `TrackerPipeline`, `TargetBelief`, `ActionPolicy`, `FrameOutput`, `EvaluationReport`, `python_scripts/run_action_policy_gate.py`.

---

## Scope

In scope:

- Add telemetry needed to understand false locks: action counts, decision path counts, target source/modality counts, reliability buckets, and false-lock action/source counts.
- Add focused policy rules only after telemetry proves the false lock is weak/noisy evidence.
- Keep `Config.ACTION_POLICY_BEHAVIOR_ENABLED` default `False` until full gate passes.
- Run both blocking promotion gate and non-blocking visible-night diagnostic pack.

Out of scope:

- New dependencies.
- Baseline model promotion.
- YOLO26 training/intake.
- Replacing ByteTrack/BoT-SORT/TemplateLockTracker.
- GUI changes.
- Hailo/Raspberry Pi.

---

## Files

- Modify: `src/uav_tracker/evaluation.py`
  - Add aggregate telemetry fields to `EvaluationReport`.
  - Populate counts from `FrameOutput` during evaluation.
- Modify: `python_scripts/run_action_policy_gate.py`
  - Surface new telemetry in per-row compact reports where useful.
  - Keep blocking/diagnostic semantics unchanged.
- Modify: `src/uav_tracker/tracking/action_policy.py`
  - Add guarded weak-evidence suppressor rules after telemetry confirms the signal.
- Modify: `tests/test_action_policy.py`
  - Unit-test every new policy rule with exact `TargetBelief` inputs.
- Modify: `tests/test_action_policy_gate.py`
  - Unit-test compact report fields and row decision compatibility.
- Create or modify: `tests/test_evaluation_telemetry.py`
  - Pure tests for `EvaluationReport.to_dict()` and telemetry aggregation helpers.
- Create: `orchestrator/reports/REPORT-FP-ID-SUPPRESSOR-V1-20260502.md`
  - Final accepted/rejected decision, metrics, and next step.
- Modify after approval only: `orchestrator/state/active_plan.md`
  - Open AP-FP-ID-SUPPRESSOR-V1 as the active cycle.
- Modify after completion only: `orchestrator/state/completed_tasks.md`
  - Record accepted result.

---

## Acceptance Criteria

Blocking promotion gate must pass:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_candidate_
```

Non-blocking visible-night diagnostic must run and remain non-blocking:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_candidate_
```

Hard thresholds:

- Day clip: `delta_presence >= -0.01`, `delta_false_lock <= +0.01`, `delta_hits_iou_01 >= -2`.
- IR clips: `delta_presence >= -0.01`, `delta_false_lock <= +0.01`, `delta_hits_iou_01 >= -2`.
- Noise clips: no increase in `presence` or `false_lock`.
- OFF sanity: `off_behavior_drop_count == 0` for all rows.
- ON behavior: `on_behavior_drop_rate <= 0.02` on blocking rows.

Target improvement:

- Prefer lowering `noise-airplane` false lock below current `0.1896`, but only if telemetry shows weak/noisy evidence.
- Prefer lowering visible-night `idchg/min` or false lock in diagnostic pack.
- If `noise-airplane` is high-confidence YOLO false positive, mark it as model/data problem and do not tune policy to pretend it is solved.

---

## Task 1: Establish Baseline and Freeze Evidence

**Files:** no code changes.

- [ ] Run repository sanity:

```bash
git status --short --branch
PYTHONPATH=src tracker_env/bin/python orchestrator/scripts/check_orchestration_state.py
```

Expected:

- `active_plan.md` is still `Completed` until Human approves this cycle.
- `orchestrator_state_check=OK`.

- [ ] Run blocking baseline gate:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_baseline_
```

Expected:

- `runs/evaluations/action_policy_gate/fp_suppressor_baseline_action_policy_gate.json`
- `gate_passed=true`

- [ ] Run diagnostic visible-night baseline:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_baseline_
```

Expected:

- `runs/evaluations/action_policy_gate/fp_suppressor_diag_baseline_action_policy_gate.json`
- `gate_passed=true`
- rows are `diagnostic=true`

- [ ] Record current problem rows in the report draft:

```bash
jq '.rows[] | {source,scene,off_presence,on_presence,off_false_lock,on_false_lock,off_idchg_pm,on_idchg_pm,on_behavior_drop_count,fail_reasons,diagnostic_reasons}' runs/evaluations/action_policy_gate/fp_suppressor_baseline_action_policy_gate.json
jq '.rows[] | {source,scene,diagnostic,off_presence,on_presence,off_false_lock,on_false_lock,off_idchg_pm,on_idchg_pm,on_behavior_drop_count,diagnostic_reasons}' runs/evaluations/action_policy_gate/fp_suppressor_diag_baseline_action_policy_gate.json
```

Expected known issues:

- `drone_detection_V_AIRPLANE_001` false lock around `0.19`.
- `night_ground_large_drones` high `idchg/min`.
- Anti-UAV visible-night rows behave like false-positive stress tests.

---

## Task 2: Add Evaluation Telemetry Before Changing Policy

**Files:**

- Modify: `src/uav_tracker/evaluation.py`
- Create or modify: `tests/test_evaluation_telemetry.py`

- [ ] Add telemetry fields to `EvaluationReport`:

```python
tracking_action_counts: dict[str, int]
decision_path_counts: dict[str, int]
target_source_counts: dict[str, int]
target_modality_counts: dict[str, int]
false_lock_action_counts: dict[str, int]
false_lock_source_counts: dict[str, int]
avg_target_reliability: float
avg_target_p_present: float
```

- [ ] In `Evaluator.run()`, initialize counters:

```python
tracking_action_counts: Counter[str] = Counter()
decision_path_counts: Counter[str] = Counter()
target_source_counts: Counter[str] = Counter()
target_modality_counts: Counter[str] = Counter()
false_lock_action_counts: Counter[str] = Counter()
false_lock_source_counts: Counter[str] = Counter()
target_reliability_values: list[float] = []
target_p_present_values: list[float] = []
```

- [ ] For each `FrameOutput`, aggregate:

```python
tracking_action_counts[str(result.tracking_action)] += 1
decision_path_counts[str(result.decision_path)] += 1
target_source_counts[str(result.active_source)] += 1
target_modality_counts[str(result.target_modality)] += 1
target_reliability_values.append(float(result.target_reliability))
target_p_present_values.append(float(result.target_p_present))
```

- [ ] When a frame is a false lock, aggregate:

```python
if result.active_id is not None and ((not gt_visible) or (gt_visible and result.gt_iou < 0.10)):
    false_lock_action_counts[str(result.tracking_action)] += 1
    false_lock_source_counts[str(result.active_source)] += 1
```

- [ ] Add pure tests:

```python
def test_evaluation_report_to_dict_includes_policy_telemetry():
    report = EvaluationReport(
        # use valid defaults for existing fields
        tracking_action_counts={"keep_lock": 3},
        decision_path_counts={"telemetry_only": 3},
        target_source_counts={"yolo": 2, "-": 1},
        target_modality_counts={"rgb": 3},
        false_lock_action_counts={"keep_lock": 1},
        false_lock_source_counts={"yolo": 1},
        avg_target_reliability=0.42,
        avg_target_p_present=0.50,
    )
    data = report.to_dict()
    assert data["tracking_action_counts"] == {"keep_lock": 3}
    assert data["false_lock_source_counts"] == {"yolo": 1}
```

If constructing the full dataclass is too noisy, add a local helper in the test with every existing required field.

- [ ] Run:

```bash
PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_evaluation_telemetry.py -q
PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_action_policy_gate.py -q
```

Expected: all pass.

---

## Task 3: Rerun Baseline With New Telemetry and Decide Suppressor Type

**Files:**

- Create draft: `orchestrator/reports/REPORT-FP-ID-SUPPRESSOR-V1-20260502.md`

- [ ] Run telemetry baseline:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_telemetry_
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_telemetry_
```

- [ ] Inspect false-lock telemetry:

```bash
jq '.rows[] | {source,scene,off_false_lock,on_false_lock,off_idchg_pm,on_idchg_pm,off: .off_false_lock_source_counts, on: .on_false_lock_source_counts, actions: .on_tracking_action_counts}' runs/evaluations/action_policy_gate/fp_suppressor_telemetry_action_policy_gate.json
jq '.rows[] | {source,scene,on_false_lock,on_idchg_pm,on_behavior_drop_count,on_tracking_action_counts,on_false_lock_source_counts}' runs/evaluations/action_policy_gate/fp_suppressor_diag_telemetry_action_policy_gate.json
```

- [ ] Decision checkpoint:

Use policy suppressor only if false locks concentrate in weak runtime evidence:

- `active_source` is `night`, `lock`, `roi`, or `local`;
- `tracking_action` is `local_validate`, `expand_roi`, or `global_rescan`;
- average reliability is low or middling;
- false lock improves when stale drops occur.

Do not add suppressor if false locks are mostly fresh/high-confidence `yolo` with high reliability. In that case, finish the report with decision `DEFER_TO_MODEL_DATASET`, keep code telemetry-only, and make the next cycle `YOLO26n candidate / dataset FP audit`.

---

## Task 4: Add Weak-Evidence Policy Rules Only If Justified

**Files:**

- Modify: `src/uav_tracker/tracking/action_policy.py`
- Modify: `tests/test_action_policy.py`

Candidate rules, guarded by evidence and conservative defaults:

```python
weak_source_drop_reliability_max: float = 0.25
weak_source_drop_lost_age_min: int = 4
night_weak_reliability_max: float = 0.35
night_weak_same_target_max: float = 0.45
night_weak_lost_age_min: int = 2
```

Add helper:

```python
def _is_weak_runtime_source(self, belief: TargetBelief) -> bool:
    return belief.source in {"night", "lock", "roi", "local"}
```

Add before existing stale/global-rescan logic:

```python
if (
    self._is_weak_runtime_source(belief)
    and belief.reliability <= self.weak_source_drop_reliability_max
    and belief.lost_age >= self.weak_source_drop_lost_age_min
):
    return TrackingAction.DROP_LOCK

if (
    belief.modality == "night"
    and self._is_weak_runtime_source(belief)
    and belief.reliability <= self.night_weak_reliability_max
    and belief.p_same_target <= self.night_weak_same_target_max
    and belief.lost_age >= self.night_weak_lost_age_min
):
    return TrackingAction.DROP_LOCK
```

Required tests:

```python
def test_weak_lock_source_drops_before_generic_stale_threshold():
    policy = ActionPolicy()
    belief = _belief(source="lock", reliability=0.20, lost_age=4, modality="rgb")
    assert policy.decide(belief, lock_score=0.1) == TrackingAction.DROP_LOCK

def test_yolo_low_reliability_is_not_suppressed_by_weak_source_rule():
    policy = ActionPolicy()
    belief = _belief(source="yolo", reliability=0.20, lost_age=4, modality="rgb")
    assert policy.decide(belief, lock_score=0.1) != TrackingAction.DROP_LOCK

def test_night_weak_same_target_drops_earlier():
    policy = ActionPolicy()
    belief = _belief(source="night", reliability=0.30, p_same_target=0.40, lost_age=2, modality="night")
    assert policy.decide(belief, lock_score=0.1) == TrackingAction.DROP_LOCK

def test_ir_weak_source_does_not_inherit_visible_night_rule():
    policy = ActionPolicy()
    belief = _belief(source="lock", reliability=0.30, p_same_target=0.40, lost_age=2, modality="ir")
    assert policy.decide(belief, lock_score=0.1) != TrackingAction.DROP_LOCK
```

Run:

```bash
PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_action_policy.py -q
PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_action_policy_behavior.py -q
```

Expected: pass.

---

## Task 5: Gate Candidate

**Files:** no further code changes unless gate fails for a clear root cause.

- [ ] Run smoke:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --max-frames 60 --tag fp_suppressor_smoke_
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --max-frames 60 --tag fp_suppressor_diag_smoke_
```

- [ ] Run full gates serially, not in parallel:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_candidate_
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_candidate_
```

Expected:

- Blocking gate: `gate_passed=true`.
- Diagnostic gate: `gate_passed=true`, with visible-night rows diagnostic.
- No parallel benchmark runs while FPS threshold is active.

- [ ] Compare candidate vs baseline:

```bash
jq '.rows[] | {source,scene,delta_presence,delta_false_lock,delta_idchg_pm,delta_avg_gt_iou,delta_hits_iou_01,on_behavior_drop_count,fail_reasons}' runs/evaluations/action_policy_gate/fp_suppressor_candidate_action_policy_gate.json
jq '.rows[] | {source,scene,diagnostic,delta_presence,delta_false_lock,delta_idchg_pm,on_behavior_drop_count,diagnostic_reasons}' runs/evaluations/action_policy_gate/fp_suppressor_diag_candidate_action_policy_gate.json
```

Reject candidate if any blocking row fails or day/IR presence materially drops.

---

## Task 6: Final Validation and Report

**Files:**

- Finalize: `orchestrator/reports/REPORT-FP-ID-SUPPRESSOR-V1-20260502.md`
- Modify: `orchestrator/state/completed_tasks.md`

- [ ] Run tests:

```bash
PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_tracking_evidence.py tests/test_action_policy.py tests/test_action_policy_behavior.py tests/test_action_policy_gate.py tests/test_evaluation_telemetry.py -q
PYTHONPATH=src tracker_env/bin/python -m pytest tests -q
PYTHONPATH=src tracker_env/bin/python -m compileall -q python_scripts src app orchestrator tests
git diff --check
PYTHONPATH=src tracker_env/bin/python orchestrator/scripts/check_orchestration_state.py
```

Expected:

- All pytest suites pass.
- compileall OK.
- git diff whitespace clean.
- orchestration state OK.

- [ ] Report must include:

| Section | Required content |
|---------|------------------|
| Что изменено | files and behavior changes |
| Baseline evidence | pre-change promotion + diagnostic metrics |
| Telemetry finding | whether false locks are weak evidence or model FP |
| Candidate result | full gate table |
| Decision | `PASS`, `FAIL`, or `DEFER_TO_MODEL_DATASET` |
| Risks | day/IR regression risk, FPS benchmark serial rule |
| Next step | enable default ON only if justified, otherwise model/data cycle |

- [ ] Commit:

```bash
git add src/uav_tracker/evaluation.py src/uav_tracker/tracking/action_policy.py python_scripts/run_action_policy_gate.py tests/test_action_policy.py tests/test_action_policy_gate.py tests/test_evaluation_telemetry.py orchestrator/reports/REPORT-FP-ID-SUPPRESSOR-V1-20260502.md orchestrator/state/completed_tasks.md
git commit -m "feat(tracking): add weak evidence suppressor telemetry"
```

If Task 3 decides `DEFER_TO_MODEL_DATASET` and no policy rule is added, commit message should be:

```bash
git commit -m "chore(tracking): add false-lock telemetry for action policy gate"
```

---

## Execution Recommendation

Use Codex as controller for Task 1-3 because the key decision is architectural. Use Claude only after Task 3 if the suppressor type is clear. Claude prompt must be bounded to Task 4-6, list allowed files, and require stop-after-task.

Do not let Claude choose whether to proceed to YOLO26/model cycle. That decision belongs to Codex/Human after the telemetry report.
