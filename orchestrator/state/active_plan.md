# Active Plan

## Plan ID
- AP-20260312-018

## Source Direction
- Human direction: move to the next stage after local quality enforcement.
- Scope: runtime-quality hardening only — reduce false lock behavior on `night` / `ir` / noise scenes, make preset-specific runtime tuning explicit, and add one canonical problem-clip regression pack.

## Status
- Completed

## Brief In Focus
- BRIEF-20260312-021-runtime-quality-hardening-v1

## Active Claude Tasks (execution allowed now)
- (none)

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [x] false-lock behavior on the key `night` / `ir` problem clips is measurably improved or at least explicitly bounded
- [x] runtime tuning differences for `day`, `night`, and `ir` are explicit in config and docs
- [x] one canonical short problem-clip regression pack exists and is wired into the local evaluation flow
