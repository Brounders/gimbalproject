# Active Plan

## Plan ID
- AP-PROJECT-STRUCTURE-STABILIZATION-V1

## Status
- Active

## Active Claude Tasks (execution allowed now)
- TASK-20260517-121

## Active RTX Tasks (execution allowed now)
- none

## Source Direction

Human approved shifting the current project focus from the completed QML/DTS
candidate-loop foundation to tracker evolution.  The application must now use
Target Lab as the operator-facing truth loop:

1. collect compact GT material from real clips without forcing full manual
   frame-by-frame annotation;
2. run the current tracker against GT with scene-aware presets;
3. explain failures in human terms: matched, missed, and off-target;
4. choose one high-impact tracker improvement at a time;
5. validate every tracker change through A/B diagnostics before treating it as
   progress;
6. return to candidate training only after the tracker evaluation loop is
   understandable and trustworthy.

The immediate target is not a new model and not cosmetic UI.  The immediate
target is a reliable diagnosis loop for autonomous tracking: target detection,
target size stability, prediction/reacquire behavior, scene-specific weakness,
and FPS impact.

## Structure Stabilization Direction

Human accepted the Claude full-project audit direction on 2026-05-17.  Detector
training is paused until the project has a basic ownership and migration map.
The immediate goal is not physical folder movement.  The immediate goal is to
turn the audit into a controlled backlog: inventory, ownership, runbooks, script
registry, archive-candidate proof, and commit-boundary review.

Structure stabilization has 6 stages:

0. Audit authority replacement — DONE in controller state once the full Claude
   audit files replace the temporary intake stubs.
1. TASK-20260517-109 — DONE: stabilization intake converted the audit into a
   concrete Now/Next/Later backlog and kept physical moves blocked.
2. TASK-20260517-110 — DONE: ownership documentation created script registry,
   UI primary runbook, `ui_web/` decision note, and `automation/state/` status note.
3. TASK-20260517-111 — DONE: proof-based cleanup plan, archive-candidate proof
   table, generated/local artifact ignore policy, no deletes without owner decision.
4. TASK-20260517-112 — DONE: safety hardening plan, NightSmallTargetDetector
   unit-test scope, offscreen PySide6 CI sanity, pipeline smoke-test proposal.
5. TASK-20260517-113 — DONE: physical restructure proposal defined migration
   order, validation gates, and rollback policy without moving files.

Return to `TASK-20260517-108` only after stages 1-3 are complete and pack/data
ownership is explicit.

## Completed Foundation

| ID | Задача | Статус | Результат |
|----|--------|--------|-----------|
| QML-001 | QML operator runtime | DONE | `app/main_qml.py`, `app/qml/**`, `app/qml_bridge/**`, QML smoke runner |
| QML-002 | Operator UI controls | DONE | source dialog, topbar cleanup, DTS entry, map/settings overlay, expandable map |
| TRACK-001 | Click-to-lock backend contract | DONE | operator click creates seeded target and tracker searches around operator-selected location |
| DTS-007 | Candidate loop UI | DONE | `СОБРАТЬ`, `ОБУЧИТЬ`, `СРАВНИТЬ`, `ПРИНЯТЬ` flow added to DTS |
| SAFE-001 | Candidate safety gate | DONE | candidate accept is safe copy only; production replacement requires separate full gate |
| LAB-001 | GT Assist / Target Lab | DONE | operator can create GT snippets and view Target Lab material/check/improvement flow |
| LAB-002 | Target Lab wording/layout fix | DONE | "false target" wording replaced by "off target"; material/check cards no longer overlap |
| LAB-003 | Scene-aware GT diagnostics | DONE | Target Lab launches diagnostics with scene labels for reporting; labels do not select presets |
| LAB-004 | Visual error samples | DONE | Target Lab diagnostics render matched/missed/off-target JPG samples for human review |
| TRACK-DIAG-001 | Weak-scene diagnosis | DONE | Human reviewed visual samples; failures split into missed detection, off-target source capture, OSD capture, and bbox-size instability |
| TRACK-IMPROVE-001 | EO source-conflict fix | DONE | EO/day `small_target` disables night detector; IR/night diagnostics use OSD-ignore presets |
| TRACK-GATE-001 | Act2 A/B gate | DONE | Act2 accepted: EO off-target 0.280->0.023, risk count 37->25; report accepted |
| TRACK-IMPROVE-002 | Act3 IR missed detection | DONE | Source-aware IR routing keeps OSD/airplane clips safe and uses `antiuav_thermal_peak` for drone IR clips |
| TRACK-GATE-002 | Act3 A/B gate | DONE | Act3 accepted: IR recall 0.103->0.556, missed 0.517->0.113, risk count 25->21 |
| TRACK-FOUNDATION-001 | Act4 live-auto foundation | DONE | Removed source-name preset routing; Target Lab uses `tracking_live_auto`; pipeline applies auto-scene overrides to actual night/peak detector |
| TRACK-ACT5-001 | Act5 universal selector/reacquire | DONE | 103a-103f complete: bbox stability, auto-scene v2, unified proposal trust table, lock-health release, re-acquisition suppression; 103g N/A |

## Accepted Reports

- `orchestrator/reports/REPORT-DTS-TRAINING-DESK-20260505.md`
- `orchestrator/reports/REPORT-OPERATOR-UI-DTS-REDESIGN-20260506.md`
- `orchestrator/reports/REPORT-UI-DTS-REDESIGN-20260507.md`
- `orchestrator/reports/REPORT-FINAL-STABILIZATION-20260514.md`
- `orchestrator/reports/REPORT-TARGET-LAB-ACT2-GATE-20260516.md`
- `orchestrator/reports/REPORT-TARGET-LAB-ACT3-GATE-20260516.md`
- `orchestrator/reports/REPORT-TARGET-LAB-ACT4-LIVE-AUTO-20260516.md`
- `orchestrator/reports/REPORT-TASK-103-ACT5-FINAL-20260516.md`
- `orchestrator/reports/REPORT-TASK-103f-REACQ-SUPPRESSION-20260517.md`
- `orchestrator/reports/REPORT-TRACKING-TOOLS-AUDIT-20260517.md`
- `orchestrator/reports/REPORT-DETECTOR-EVIDENCE-WEAK4-20260517.md`
- `orchestrator/reports/REPORT-TASK-104-WEAK4-TRAINING-PREP-20260517.md`
- `orchestrator/reports/REPORT-TASK-105-MAC-SMOKE-MICRO3-20260517.md`
- `orchestrator/reports/REPORT-TASK-106-WEAK4-V2-V3-GATE-20260517.md`
- `orchestrator/reports/REPORT-TASK-107-WEAK4-LABEL-AUDIT-20260517.md`
- `orchestrator/reports/REPORT-FULL-PROJECT-AUDIT-20260517.md`
- `orchestrator/reports/REPORT-FULL-PROJECT-AUDIT-FILE-INVENTORY-20260517.md`
- `orchestrator/reports/REPORT-FULL-PROJECT-AUDIT-RESTRUCTURE-PLAN-20260517.md`
- `orchestrator/reports/REPORT-TASK-109-STRUCTURE-STABILIZATION-INTAKE-20260517.md`
- `orchestrator/reports/REPORT-TASK-110-OWNERSHIP-DOCUMENTATION-20260517.md`
- `orchestrator/reports/REPORT-TASK-111-PROOF-CLEANUP-PLAN-20260517.md`
- `orchestrator/reports/REPORT-TASK-112-SAFETY-HARDENING-PLAN-20260517.md`
- `orchestrator/reports/REPORT-TASK-113-PHYSICAL-RESTRUCTURE-PROPOSAL-20260517.md`
- `orchestrator/reports/REPORT-TASK-093-COMMIT-BOUNDARY-REVIEW-20260517.md`
- `orchestrator/reports/REPORT-TASK-114-SYNC-BOUNDARY-DECISION-20260517.md`
- `orchestrator/reports/REPORT-TASK-115-SYNC-BRANCH-VALIDATION-20260517.md`
- `orchestrator/reports/REPORT-TASK-116-RTX-SYNC-INTAKE-PROMPT-20260517.md`
- `orchestrator/reports/REPORT-TASK-117-NIGHT-DETECTOR-UNIT-COVERAGE-20260517.md`
- `orchestrator/reports/REPORT-TASK-118-NO-TRAINING-DETECTOR-STRATEGY-20260517.md`
- `orchestrator/reports/REPORT-TASK-119-NIGHT-SOURCE-AUTHORITY-AB-GATE-20260517.md`
- `orchestrator/reports/REPORT-TASK-120-NIGHT-PRIMARY-CANDIDATE-GATE-20260517.md`

## Current Execution Queue

| ID | Задача | Статус | Условие закрытия |
|----|--------|--------|------------------|
| TASK-20260516-096 | Target Lab scene-aware smoke | DONE | Report `target_lab_act1_20260516_112807` created with scene-aware metrics and 149 visual samples |
| TASK-20260516-097 | Weak-scene diagnosis | DONE | Visual review completed by Human; first lever selected: source-conflict and OSD contamination |
| TASK-20260516-098 | Tracker improvement v1 | DONE | `small_target` disables night detector; scene-aware diagnostics route IR/night through OSD-ignore presets |
| TASK-20260516-099 | A/B tracking gate | DONE | Act2 source-conflict fix accepted; keep for next baseline |
| TASK-20260516-101 | Act3 IR missed detection | DONE | Source-aware IR preset routing accepted; risk count 25->21; IR recall 0.103->0.556 |
| TASK-20260516-102 | Act4 live-auto foundation | DONE | Removed folder/source-name routing; Target Lab uses one live preset and runtime frame-content auto-scene |
| TASK-20260516-103 | Act5 universal selector and reacquire | DONE | 103a-103f реализованы и приняты; 103g N/A; 103h не selector-fix и переносится в detector/training gate |
| TASK-20260516-100 | Detector/training decision gate | DONE | Weak4 detector evidence pack completed; Act5 ceiling classified as detector/data problem; 103h opened as bounded preparation task |
| TASK-20260517-104 | 103h detector/training preparation | DONE | Weak4 GT-to-YOLO pack created at `runs/training_packs/weak4_103h_20260517`; smoke contract drafted, but not run on RTX |
| TASK-20260517-105 | Mac-local smoke triage | DONE | Corrected Mac-vs-RTX accounting; fixed training project path; tiny smoke passed; Micro3 candidate rejected as not promotable due regression |
| TASK-20260517-106 | Weak4 v2 protected training gate | DONE | V2/V3 candidates rejected; lower-risk variants did not preserve Micro3 improvement and protected gate |
| TASK-20260517-107 | Weak4 label/pack audit | DONE | Contact sheets rendered; source/scale label conflict found; blind fine-tune variants stopped |
| TASK-20260517-108 | Scale/source-aware weak4 pack | PAUSED | Paused by full-project audit intake; resume after structure stabilization and pack ownership decisions |
| TASK-20260517-109 | Project structure stabilization intake | DONE | Full audit converted into 6-stage stabilization backlog; no folder moves or runtime changes |
| TASK-20260517-110 | Ownership documentation | DONE | Script registry, primary UI authority, ui_web decision note, and automation/state status note documented; no file moves |
| TASK-20260517-111 | Proof-based cleanup plan | DONE | Archive-candidate proof table and generated/local artifact policy documented; AppleDouble ignore rule added; no deletes/moves |
| TASK-20260517-112 | Safety hardening plan | DONE | NightSmallTargetDetector unit-test scope, offscreen QML sanity, and pipeline smoke proposal documented; no runtime/CI changes |
| TASK-20260517-113 | Physical restructure proposal | DONE | Migration order, validation gates, and rollback policy documented; no physical moves |
| TASK-20260514-093 | Commit boundary review | DONE | Local main is clean but 170 commits ahead with mixed project/agent history; wholesale push blocked pending sync-boundary decision |
| TASK-20260517-114 | Sync boundary decision | DONE | Selected isolated branch strategy: `codex/sync-boundary-20260517`; do not push/pull `main` for RTX |
| TASK-20260517-115 | Sync branch validation | DONE | Created and validated `codex/sync-boundary-20260517` as local sync snapshot |
| TASK-20260517-116 | RTX sync intake | DEFERRED | Human deferred RTX/training; branch remains available but is not the active blocker |
| TASK-20260517-117 | Night detector unit coverage | DONE | Added synthetic NightSmallTargetDetector tests; 7 targeted tests pass locally |
| TASK-20260517-118 | No-training detector strategy gate | DONE | Training not required now; selected local night-source authority A/B gate as next bounded step |
| TASK-20260517-119 | Night-source authority A/B gate | DONE | Added default-off night primary source switch and tests; current presets unchanged |
| TASK-20260517-120 | Night-primary candidate A/B gate | DONE | Candidate rejected: no weak4 improvement and 9_dji false-lock worsened; production presets unchanged |
| TASK-20260517-121 | Weak4 off-target geometry audit | ACTIVE | Analyze baseline active bbox vs GT center/scale to find next no-training geometry/proposal lever |

## Deferred From Previous Plan

| ID | Причина паузы |
|----|---------------|
| TASK-20260514-094 | Candidate data collection continues opportunistically, but no training decision until Target Lab diagnostics are trustworthy. |
| TRAIN-20260514-001 | Candidate training waits for useful accepted DTS/GT material and a clear tracker baseline. |
| TASK-20260514-095 | Full production promotion gate remains required before any production model replacement. |

## Current Decision Gate

TASK-20260517-121 активна. RTX/training is deferred by Human; sync branch `codex/sync-boundary-20260517` remains available but is not the active blocker. Night-primary candidate was rejected; next work is weak4 off-target geometry/proposal audit without training.

Closed in Act5:
- universal proposal selection and scene trust table;
- bbox stability layer;
- auto-scene-detect v2;
- lock-health release valve;
- health-release re-acquisition suppression;
- decision not to add lock_tracker multi-scale now because expected benefit is low and latency risk is real.

Not closed in Act5:
- detector recall on weak clips: `antiuav_rgbt_20190925=0.000`, `1_minie3_range_close=0.000`, `9_dji2_range_medium=0.276`, `antiuav_rgbt_train=0.412`;
- dataset composition for the next training cycle;
- any production model replacement or baseline promotion;
- 103h targeted training scope.

Invalid training evidence:
- YOLO26 smoke-train attempt on 2026-05-17 was manually stopped and produced only `args.yaml`; no `results.csv`, `weights/best.pt`, or `weights/last.pt`. Do not count it as a result.

Detector evidence pack result:
- `1_minie3_range_close`: best `yolo@0.05`, Hit@0.1 `0.5312`; YOLO signal exists but current confidence/policy is too strict.
- `9_dji2_range_medium`: best `antiuav_thermal_peak`, Hit@0.1 `0.2171`; YOLO is effectively absent and targeted detector data is needed.
- `antiuav_rgbt_20190925_200805_1_2_infrared`: best `antiuav_thermal_peak`, Hit@0.1 `0.3333`; YOLO is effectively absent and targeted detector data is needed.
- `antiuav_rgbt_train_20190925_205804_1_2_infrared`: best `yolo@0.05`, Hit@0.1 `0.9543`; YOLO signal exists but operating threshold/ranking needs training/gate treatment.

Next bounded step:
1. Do not start RTX training.
2. Do not push `main`.
3. Run TASK-20260517-121: inspect baseline active bbox vs GT geometry on weak4.
4. Only consider a new runtime candidate if the geometry audit points to a
   bounded filter/scoring/sizing lever.
5. Keep TRAIN-20260517-002 deferred until Human explicitly reopens RTX training.
