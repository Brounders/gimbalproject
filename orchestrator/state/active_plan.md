# Active Plan

## Plan ID
- AP-20260312-013

## Source Direction
- Human direction: continue executing the audit fixes, but prioritize the local desktop product over temporary RTX/GitHub/web infrastructure.
- Scope: local reproducibility and quality discipline only — dependency contract, preset-specific regression packs, and canonical local quality-gate flow.

## Status
- Completed

## Brief In Focus
- BRIEF-20260312-016-local-reproducibility-and-quality-v1

## Active Claude Tasks (execution allowed now)
- (none)

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [x] Local bootstrap no longer depends on implicit `tracker_env` state. (`requirements.txt` + Bootstrap section in RUNBOOK)
- [x] Regression/evaluation assets are split by `day`, `night`, and `ir` scenarios. (`regression_pack_day/night/ir.csv`)
- [x] Local `quick smoke -> benchmark -> quality-gate` flow is canonical and documented. (RUNBOOK quality-gate flow section)
