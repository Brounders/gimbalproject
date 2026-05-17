# REPORT — Tracking Tools Audit and Evolution Vector

Date: 2026-05-17
Scope: project tools, runtime interaction, detector/training bottlenecks, next tracking-evolution vector.
Runtime code changes: none.

## Executive Answer

Проект упёрся не в selector/reacquire слой. Act5 закрыл основные ошибки выбора активной цели: scene trust, bbox stability, auto-scene, lock-health release и suppression после release. Оставшиеся слабые клипы упираются в detector/data layer:

- `antiuav_rgbt_20190925_200805_1_2_infrared`: recall `0.000`, active bbox есть на всех 933 GT frames, но это off-target.
- `1_minie3_range_close`: recall `0.000`, 471 off-target frames, только 5 missed frames после Act3/Act5.
- `9_dji2_range_medium`: recall `0.276`, 521 missed visible frames.
- `antiuav_rgbt_train_20190925_205804_1_2_infrared`: recall `0.412`, 515 off-target frames.

Главный вывод: дальше нельзя делать очередной selector-fix. Нужен короткий цикл detector evidence → training smoke artifact → targeted detector training → GT gate.

## Tool Map

| Layer | Tools / Files | Role | Current Status |
|---|---|---|---|
| Orchestration | `orchestrator/state/*`, reports | Authority for active work and acceptance | Reconciled: `TASK-20260516-100` active |
| Runtime pipeline | `src/uav_tracker/pipeline.py` | YOLO/global, local, ROI, night, TargetManager, lock, telemetry | Feature-rich, but detector/source semantics are now the bottleneck |
| Detection sources | `DetectionSource`: yolo/local/lock/roi/night/operator | Defines primary vs auxiliary signal | `night` is not primary; this constrains promotion/focus semantics |
| Night/IR detector | `NightSmallTargetDetector` | MOG2/frame-diff/hotspot/peak small-target detector | Useful but unstable on RGBT/IR weak clips |
| Target selection | `proposal_trust.py`, `TargetManager.pick_active_by_trust()` | Scene-trust selector and health release | Act5 accepted; no evidence for more selector work now |
| GT diagnostics | `run_tracking_gt_diagnostics.py`, Target Lab | Matched/missed/off-target evidence loop | Strongest current project tool |
| Operator GT/DTS | `GtAssistBridge`, DTS, `stage_operator_training_pack.py` | Builds compact labelled data and hard negatives | Good foundation; not yet tied to 103h dataset decision |
| Candidate safety | `dts_candidate_gate.py`, `run_model_battle.py`, `run_quality_gate.py` | Candidate compare/accept/promotion safety | Good guardrails; smoke and full gate need sharper scope |
| YOLO training | `train_yolo_from_yaml.py`, Ultralytics | Candidate detector training | Script exists, but smoke-run policy/logging is incomplete |
| Configs/presets | `tracking_live_auto.yaml`, `antiuav_thermal_peak.yaml`, `night.yaml` | Runtime behavior control | Powerful but fragmented; hard to reason without evidence packs |

## Interaction Audit

### Runtime Signal Flow

Current flow:

1. `TrackerPipeline.process_frame()`
2. global YOLO or lock/local validation
3. ROI assist if enabled
4. night detector if scene/runtime budget allows
5. `TargetManager.age_targets()`
6. legacy `select_active()`
7. scene-aware `pick_active_by_trust()`
8. focus/lock state and TemplateLockTracker sync
9. telemetry/FrameOutput/Target Lab

This is now good enough to diagnose failures. The weak clips are no longer opaque.

### Critical Semantic Mismatch

`DetectionSource.primary_sources()` includes `YOLO`, `ROI`, `LOCAL`, `LOCK`, `OPERATOR`, but excludes `NIGHT`.

Effects:

- `has_confirmed_drone_lock()` refuses non-primary active targets.
- drone_score updates happen only for primary sources.
- night can be selected by trust, but it remains second-class for parts of lock/focus semantics.
- When night is wrong, selector cannot invent better evidence.
- When night is right but no primary source confirms it, promotion semantics remain fragile.

This is not automatically a bug: it was a safety design. But for IR/night evolution it is now a central design decision.

### Detector Behavior

Night/IR detector is heuristic:

- MOG2 background subtraction;
- frame diff;
- optional hotspot/peak selection;
- sticky single target;
- contour/area/aspect/border filters.

It can work very well (`IR_DRONE_025` recall `0.987`) and completely fail on similar-looking weak clips. That variance means the next lever is not another policy tweak; it is detector evidence and data.

### Target Lab and GT Diagnostics

This is the strongest part of the current toolchain:

- distinguishes `matched`, `missed`, `off_target`, `false_active`;
- uses raw bbox for recall so display smoothing does not corrupt evaluation;
- records source counts, scene runtime, proposal counts, bbox stability, latency;
- can render visual samples for human review.

Problem: it is still mostly a diagnostic endpoint, not yet the front door to training decisions. The next task should make it drive dataset composition.

### DTS / Training Pack

DTS and `stage_operator_training_pack.py` can produce YOLO-style data from accepted/staged operator annotations and hard negatives. This is valuable, but it is not enough by itself for 103h:

- accepted operator frames are not necessarily sampled from the four current weak clips;
- hard negatives are supported but need explicit ratio/scope;
- dataset composition remains the blocker, not the existence of a pack builder.

### YOLO26 Smoke Training

The stopped smoke run produced only:

- `runs/detect/runs/smoke_train/yolo26n_smoke_20ep/args.yaml`
- `runs/detect/runs/smoke_train/yolo26n_smoke_2k/args.yaml`

No `results.csv`, `weights/best.pt`, `weights/last.pt`, or log. Therefore it is not result evidence. It only proves that the run directory was initialized.

Likely failure class: startup/first-epoch stall or manual stop before checkpoint creation. Exact cause cannot be proven without a log.

## Current Bottlenecks

1. Detector recall / detector correctness.
   Selector is selecting among bad or missing proposals on weak clips.

2. Night source governance.
   `night` is trusted in scene table but not primary in core target semantics.

3. Dataset composition.
   OQ-001 remains real: a dataset name is not enough; we need content-derived composition for weak clips.

4. Smoke-run observability.
   A train run without tee log and artifact policy cannot be debugged.

5. Preset fragmentation.
   Many YAMLs encode candidate behavior. This is useful for experiments, but risky if not tied to named evidence packs.

6. Dirty worktree / commit boundary.
   The repository has many modified/untracked files. That does not block audit, but it increases integration risk.

## Recommended Evolution Vector

### Direction

Move from “tracking policy patches” to “detection-first tracking evolution”.

The tracker should evolve into a system where:

1. detector evidence is measured before tracker changes;
2. source reliability is learned or calibrated per scene;
3. selector/lock consumes reliable proposals instead of compensating for detector gaps;
4. model/data changes are accepted only through GT gates;
5. operator annotations feed targeted detector training, not broad unfocused retraining.

### Phase 1 — Detector Evidence Pack

Bounded task:

- input: four weak clips;
- output: per-clip evidence table and contact sheets;
- measure YOLO proposals at several conf thresholds, night peak/contour proposals, GT overlap, source counts, missed/off-target split;
- no runtime behavior change.

Acceptance:

- for each weak clip, decide one of:
  - detector absent;
  - detector present but wrong bbox;
  - source promotion/primary semantics issue;
  - GT/scene issue;
  - latency/budget issue.

### Phase 2 — Short YOLO26 Smoke as Artifact Test

Purpose: not quality, only “can training produce logs and checkpoints”.

Policy:

- `epochs=1`;
- tiny verified dataset subset;
- `workers=0`;
- `save_period=1`;
- `val=True` only if dataset val split is valid;
- tee stdout/stderr to `train.log`;
- external timeout 45-60 min;
- required artifacts: `args.yaml`, `results.csv`, `weights/last.pt`; `best.pt` expected if validation runs.

If artifacts do not appear, stop and debug environment/startup. Do not launch longer training.

### Phase 3 — 103h Targeted Detector Training

Open only after Phase 1+2.

Dataset composition should be content-derived:

- positives from weak clips, especially `9_dji2_range_medium`, `1_minie3_range_close`, antiuav RGBT IR frames;
- hard negatives from airplane/bird/OSD/background frames;
- preserve scene labels: IR, EO, NIGHT, NEGATIVE;
- include manifest with source clip, frame index, bbox source, status, and split;
- no production replacement.

Gate:

- candidate must improve at least two weak clips without regressing safe clips;
- mandatory checks on `IR_DRONE_025`, `2_minie3_range_medium_close_birds`, `IR_AIRPLANE_*`, `V_BIRD_030`;
- report matched/missed/off-target, not just mAP.

### Phase 4 — Source Semantics Decision

After detector evidence:

Option A: keep `night` auxiliary.

- safer;
- only use night to seed/assist primary validation;
- requires YOLO/local confirmation for lock.

Option B: promote `night` to primary for IR/night scenes only.

- may fix IR lock semantics;
- higher false-lock risk;
- must be gated by negative IR/night clips.

Recommended: do not decide this by intuition. Make it an A/B architecture task after 103h evidence.

### Phase 5 — Tracker Evolution Beyond Heuristics

Once detector proposals improve, evolve tracking:

- keep TargetManager as state owner;
- add a typed DetectionEvidence/TrackCandidate layer before TargetManager;
- calibrate per-source reliability from GT diagnostics;
- consider ByteTrack/BoT-SORT only as baseline comparators, not drop-in replacement;
- make TemplateLockTracker a bounded continuity tool, not the truth source.

## Immediate Next Tasks

1. `TASK-20260517-104` — Detector Evidence Pack for four weak clips.
   No runtime changes. Produce summary CSV/JSON/contact sheets and decision table.

2. `TASK-20260517-105` — YOLO26 smoke artifact harness.
   Add or document a safe one-epoch run command with log, timeout, and artifact check.

3. `TASK-20260517-106` — 103h dataset scope.
   Build dataset manifest from evidence pack + DTS/GT material; no training until manifest is approved.

4. `TASK-20260517-107` — Night primary semantics A/B design.
   Only after detector evidence says source semantics, not detector absence, is blocking.

## Do Not Do Next

- Do not implement another selector tweak without detector evidence.
- Do not run a long YOLO26 training session before one-epoch smoke artifacts are proven.
- Do not promote any candidate model from smoke results.
- Do not treat mAP alone as acceptance; this project needs GT tracking outcomes.
- Do not merge/commit broad dirty worktree state without commit-boundary review.

## Validation Performed

- Read orchestrator state after reconciliation.
- Reviewed accepted Act5 reports.
- Reviewed runtime flow in `pipeline.py`, `target_manager.py`, `proposal_trust.py`, `night_detector.py`.
- Reviewed Target Lab diagnostics implementation.
- Reviewed DTS/training pack and candidate gate code.
- Checked YOLO26 smoke directories: args only, no train artifacts.
- Verified current Ultralytics route via local docs map and Context7 query.
