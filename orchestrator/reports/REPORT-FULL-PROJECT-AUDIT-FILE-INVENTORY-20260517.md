# Full Project Audit File Inventory Intake

Date: 2026-05-17
Source: Claude audit summary provided by Human
Status: Accepted as inventory intake

## Inventory Scale

- Total files reported: 605.
- Python files reported: 187.
- Test functions reported: 868 in 56 files.

## Classification Summary

| Area | Audit status | Controller note |
|---|---|---|
| `src/uav_tracker/` | Core runtime | Do not move before import migration plan. |
| `app/` | Active UI/app layer | Contains PySide6/QML bridge surface; needs primary UI decision. |
| `app/qml/` | Active QML UI | Current QML path appears active, but relationship to PySide6 widgets must be documented. |
| `python_scripts/` | Active plus legacy tooling | Needs README/status table before archive decisions. |
| `configs/` | Active presets/dataset material | Needs split between presets, gates, datasets, GT. |
| `orchestrator/` | Control plane | Keep as execution authority; reports/state/tasks/training remain here. |
| `runs/` | Generated artifacts | Should stay ignored; do not commit training/eval outputs. |
| `models/` | Model artifacts | Needs production/candidate/external ownership model. |
| `automation/state/` | Stale or RTX-specific | Needs owner decision before deletion/archive. |
| `ui_web/` | Unknown active/legacy | Must be documented before movement/removal. |
| `.claude/` and Codex files | Agent config | Needs commit-boundary review before push. |

## Archive Candidates From Summary

The audit reports five `python_scripts` with zero references.  The exact file
list was not present in the Human summary, so the Mac controller must not delete
or move them yet.

Required next evidence:

1. path;
2. reference search;
3. owner/mechanism;
4. replacement path if any;
5. risk level.

## Required Inventory Work

The stabilization intake must produce:

- `python_scripts/README.md` or equivalent script registry;
- UI ownership note covering QML, PySide6 widgets, and `ui_web/`;
- generated-artifact policy for `runs/`, model outputs, and AppleDouble files;
- archive-candidate table with risk levels.
