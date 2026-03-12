# Active Plan

## Plan ID
- AP-20260312-015

## Source Direction
- Human direction: move to the next audit-driven stage after local baseline governance and focus on the most rational architecture repair first.
- Scope: `pipeline.py` stage-1 split only — extract `FrameOutput`, extract overlay/draw helpers, and thin `pipeline.py` into an orchestration-first module.

## Status
- Active

## Brief In Focus
- BRIEF-20260312-018-pipeline-stage1-split-v1

## Active Claude Tasks (execution allowed now)
- TASK-20260312-052 | pipeline frameoutput extract | Open
- TASK-20260312-053 | pipeline overlay extract | Open
- TASK-20260312-054 | pipeline orchestrator thinning | Open

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [ ] `FrameOutput` no longer lives in `src/uav_tracker/pipeline.py`.
- [ ] overlay/draw helpers are extracted from `src/uav_tracker/pipeline.py`.
- [ ] `pipeline.py` is smaller and orchestration-first without changing runtime semantics.
