# TASK-20260517-109 Structure Stabilization Intake

Date: 2026-05-17
Owner: Codex Mac

## Result

TASK-20260517-109 is complete. The full Claude audit was converted into a
controlled stabilization backlog. No folders were moved. No runtime, training,
or UI code was changed.

## Stage Map

Structure stabilization is now split into 6 stages:

| Stage | Task | Purpose | Status |
|---:|---|---|---|
| 0 | Audit authority replacement | Replace temporary intake stubs with full Claude audit reports. | DONE |
| 1 | TASK-20260517-109 | Convert audit into Now/Next/Later backlog and block physical moves. | DONE |
| 2 | TASK-20260517-110 | Ownership documentation: script registry, primary UI runbook, `ui_web/`, `automation/state/`. | NEXT |
| 3 | TASK-20260517-111 | Proof-based cleanup plan: archive candidates and generated/local artifact policy. | NEXT |
| 4 | TASK-20260517-112 | Safety hardening plan: night-detector unit tests, PySide6 CI sanity, pipeline smoke. | LATER |
| 5 | TASK-20260517-113 | Physical restructure proposal: `python_scripts/`/tools, config split, archive moves. | LATER |

Return to `TASK-20260517-108` after stages 1-3 are complete and pack/data
ownership is explicit.

## Now

These are documentation/control-plane tasks. They may add docs/reports, but must
not move folders or change runtime behavior.

1. `TASK-20260517-110`: create ownership documentation:
   - script registry for `python_scripts/`;
   - primary operator UI runbook;
   - `ui_web/` purpose/owner decision note;
   - `automation/state/` RTX/historical status note.
2. `TASK-20260517-111`: create cleanup proof table:
   - candidate archive files with reference proof;
   - generated/local artifact policy;
   - AppleDouble/local file handling;
   - no deletes without owner decision.
3. `TASK-20260514-093`: commit boundary review before any remote push.

## Next

These tasks prepare safe cleanup but still avoid physical restructure.

1. Add unit-test plan for `NightSmallTargetDetector`.
2. Add CI plan for offscreen PySide6 sanity.
3. Add pipeline smoke-test proposal.
4. Decide whether `TRAIN-20260517-002` should be sent to RTX after structure
   stabilization or after `TASK-108` resumes.

## Later

Only after Now/Next are accepted:

1. Decide whether to archive candidate scripts by `git mv`, not delete.
2. Decide whether to rename `python_scripts/` to `tools/`.
3. Decide whether to split configs into presets/gates/datasets.
4. Decide whether to start monolith slicing (`pipeline.py`, `main_gui.py`).

## Blocked Actions

Until stages 1-3 are accepted:

- no physical folder moves;
- no script archive moves;
- no runtime refactors;
- no detector training from weak4 packs;
- no remote push from this branch.

## Acceptance Criteria

This task is accepted when:

- full audit reports are present in the Mac workspace;
- `active_plan.md` names the stabilization stages;
- `open_tasks.md` has tasks 110-113 with clear sequencing;
- `TASK-20260517-108` is paused, not cancelled;
- validation passes.
