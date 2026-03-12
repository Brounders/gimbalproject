# Active Plan

## Plan ID
- AP-20260312-016

## Source Direction
- Human direction: move to the next stage after `pipeline.py` stage-1 split.
- Scope: `app/main_gui.py` stage-0 split only — extract theme/style wiring, display-card/HUD helpers, and thin non-worker UI plumbing so the main window becomes orchestration-first.

## Status
- Done

## Brief In Focus
- BRIEF-20260312-019-main-gui-stage0-split-v1

## Active Claude Tasks (execution allowed now)
- TASK-20260312-055 | gui theme style extract | Done
- TASK-20260312-056 | gui display card extract | Done
- TASK-20260312-057 | gui nonworker plumbing thinning | Done

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [x] theme/style-related helper code is extracted out of `app/main_gui.py`.
- [x] display-card/HUD helper code is extracted out of `app/main_gui.py`.
- [x] `app/main_gui.py` is smaller and orchestration-first without changing operator behavior.
