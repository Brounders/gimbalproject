# Active Plan

## Plan ID
- AP-TARGET-LAB-TRACKING-EVOLUTION-V1

## Status
- Active

## Active Claude Tasks (execution allowed now)
- TASK-20260516-103

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

## Accepted Reports

- `orchestrator/reports/REPORT-DTS-TRAINING-DESK-20260505.md`
- `orchestrator/reports/REPORT-OPERATOR-UI-DTS-REDESIGN-20260506.md`
- `orchestrator/reports/REPORT-UI-DTS-REDESIGN-20260507.md`
- `orchestrator/reports/REPORT-FINAL-STABILIZATION-20260514.md`
- `orchestrator/reports/REPORT-TARGET-LAB-ACT2-GATE-20260516.md`
- `orchestrator/reports/REPORT-TARGET-LAB-ACT3-GATE-20260516.md`
- `orchestrator/reports/REPORT-TARGET-LAB-ACT4-LIVE-AUTO-20260516.md`

## Current Execution Queue

| ID | Задача | Статус | Условие закрытия |
|----|--------|--------|------------------|
| TASK-20260516-096 | Target Lab scene-aware smoke | DONE | Report `target_lab_act1_20260516_112807` created with scene-aware metrics and 149 visual samples |
| TASK-20260516-097 | Weak-scene diagnosis | DONE | Visual review completed by Human; first lever selected: source-conflict and OSD contamination |
| TASK-20260516-098 | Tracker improvement v1 | DONE | `small_target` disables night detector; scene-aware diagnostics route IR/night through OSD-ignore presets |
| TASK-20260516-099 | A/B tracking gate | DONE | Act2 source-conflict fix accepted; keep for next baseline |
| TASK-20260516-101 | Act3 IR missed detection | DONE | Source-aware IR preset routing accepted; risk count 25->21; IR recall 0.103->0.556 |
| TASK-20260516-102 | Act4 live-auto foundation | DONE | Removed folder/source-name routing; Target Lab uses one live preset and runtime frame-content auto-scene |
| TASK-20260516-103 | Act5 universal selector and reacquire | DONE | 103a-103e реализованы и приняты; A/B gate pass; 103f conditional — решение по scope за Human/Codex |
| TASK-20260516-100 | Candidate-training return gate | WAITING_TRACKER_DIAG | Only after diagnostics are understandable: decide whether to collect more DTS data, train candidate, or compare YOLO26 |

## Deferred From Previous Plan

| ID | Причина паузы |
|----|---------------|
| TASK-20260514-093 | Commit boundary review remains necessary before final commit, but does not drive tracker evolution. |
| TASK-20260514-094 | Candidate data collection continues opportunistically, but no training decision until Target Lab diagnostics are trustworthy. |
| TRAIN-20260514-001 | Candidate training waits for useful accepted DTS/GT material and a clear tracker baseline. |
| TASK-20260514-095 | Full production promotion gate remains required before any production model replacement. |

## Current Next Step

TASK-20260516-103 закрыта. Следующие варианты (решение за Human/Codex):
1. 103f — lock_tracker multi-scale: даст эффект на off-target IR клипы; требует scope
2. TASK-20260516-100 — candidate-training return gate: диагностика достаточно понятна для решения о DTS/обучении
3. 103h — targeted training: улучшение детектора для missed-detection клипов
