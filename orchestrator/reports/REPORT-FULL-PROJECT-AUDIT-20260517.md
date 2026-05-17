# Full Project Audit Intake

Date: 2026-05-17
Source: Claude audit summary provided by Human
Status: Accepted as structure-stabilization intake

## Executive Summary

The project requires a structure-stabilization pass before more detector
training or physical folder moves.  The audit found that the current repository
contains active runtime code, UI layers, training/evaluation tools, orchestration
state, generated artifacts, legacy automation, and unclear web/UI material in a
single loosely organized tree.

The immediate decision is to pause `TASK-20260517-108` and open a stabilization
cycle that converts the audit into an executable migration backlog without
moving files yet.

## Report Artifacts

The full Claude audit was reported by Human as three files:

| File | Reported size |
|---|---:|
| `REPORT-FULL-PROJECT-AUDIT-20260517.md` | ~644 lines, 34 KB |
| `REPORT-FULL-PROJECT-AUDIT-FILE-INVENTORY-20260517.md` | ~225 lines, 11 KB |
| `REPORT-FULL-PROJECT-AUDIT-RESTRUCTURE-PLAN-20260517.md` | ~249 lines, 10 KB |

This file records the accepted intake summary in the Mac controller workspace.

## Validation Reported By Audit

- `compileall` across all modules: PASS, 0 errors.
- Repository scale: 605 files.
- Python scale: 187 Python files.
- Test scale: 868 test functions in 56 files.

## Top Findings

1. `TASK-20260517-108` is active, but weak4 pack has geometrically incompatible labels: strips, silhouettes, and hotspots are mixed.
2. YOLO recall is 0 on two IR clips; this is detector/data, not selector.
3. `TRAIN-20260517-002` is still Draft; RTX smoke has not run.
4. `NightSmallTargetDetector` has no unit tests despite high quality variance.
5. Two UI layers are active: PySide6 widgets and QML; primary UI priority is not documented.
6. `ui_web/` is 244 KB TypeScript/React, CI builds it, but its runtime role is unknown.
7. `automation/state/` is stale and contains Windows paths last updated around 2026-03-12/13.
8. Five `python_scripts` have zero references and are archive candidates.
9. `DetectionSource.NIGHT` is not primary source by design, but this constrains IR evolution.
10. CI runs pytest without PySide6; UI tests may silently skip.

## Recommended Actions

1. Execute `TASK-20260517-108` only after pack cleanup: quarantine strip labels and train on compact thermal positives.
2. Run `TRAIN-20260517-002` smoke on RTX with artifact gate and 45-60 minute timeout.
3. Add unit tests for `NightSmallTargetDetector` using synthetic content.
4. Document `ui_web/`: purpose, owner, and connection to runtime.
5. Add `python_scripts/README.md` with script purpose/owner/status.
6. Archive five dead `python_scripts` after proof and owner decision.
7. Execute `TASK-20260514-093` before remote push.
8. Add CI offscreen PySide6 sanity test.
9. Refresh or document `automation/state/` as RTX-specific historical state.
10. Add `RUNBOOK.md` declaring the primary operator UI.

## Controller Decision

Accepted for planning:

- The project needs a structure-stabilization cycle now.
- Physical restructuring must not happen as the first step.
- Detector/training work pauses until the audit is converted into a migration backlog and commit boundary is reviewed.

Not accepted as immediate action:

- deleting files;
- moving folders;
- archiving scripts without owner/risk proof;
- launching more training before pack/data ownership is clarified.
