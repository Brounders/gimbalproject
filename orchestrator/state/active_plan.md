# Active Plan

## Plan ID
- AP-20260311-009

## Source Direction
- Human direction: apply the next rational steps after the `epoch142` intake result:
  - do not relaunch training immediately;
  - run a short code cycle around the imported `epoch142` candidate;
  - suppress false locks and ID churn on the weakest night/noise scenes;
  - retune and reevaluate the same model before any promotion decision.

## Status
- Active

## Brief In Focus
- BRIEF-20260311-012-epoch142-retune-cycle

## Active Claude Tasks (execution allowed now)
- TASK-20260311-029 | false-lock suppression hardening | Open
- TASK-20260311-030 | candidate model eval override | Open
- TASK-20260311-031 | epoch142 retune gate | Open

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- A short runtime hardening pass is applied around `epoch142`.
- Candidate model evaluation no longer depends on ad hoc temporary presets.
- `epoch142` receives a fresh benchmark/gate decision after retune.
