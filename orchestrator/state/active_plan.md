# Active Plan

## Plan ID
- AP-20260312-013

## Source Direction
- Human direction: continue executing the audit fixes, but prioritize the local desktop product over temporary RTX/GitHub/web infrastructure.
- Scope: local reproducibility and quality discipline only — dependency contract, preset-specific regression packs, and canonical local quality-gate flow.

## Status
- Active

## Brief In Focus
- BRIEF-20260312-016-local-reproducibility-and-quality-v1

## Active Claude Tasks (execution allowed now)
- TASK-20260312-046 | dependency lock and bootstrap | Open
- TASK-20260312-047 | preset-specific regression packs | Open
- TASK-20260312-048 | minimal local quality-gate contract | Open

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [ ] Local bootstrap no longer depends on implicit `tracker_env` state.
- [ ] Regression/evaluation assets are split by `day`, `night`, and `ir` scenarios.
- [ ] Local `quick smoke -> benchmark -> quality-gate` flow is canonical and documented.
