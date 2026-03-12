# Active Plan

## Plan ID
- AP-20260312-018

## Source Direction
- Human direction: move to the next stage after local quality enforcement.
- Scope: runtime-quality hardening only — reduce false lock behavior on `night` / `ir` / noise scenes, make preset-specific runtime tuning explicit, and add one canonical problem-clip regression pack.

## Status
- Active

## Brief In Focus
- BRIEF-20260312-021-runtime-quality-hardening-v1

## Active Claude Tasks (execution allowed now)
- TASK-20260312-061 | night ir false lock suppression | Open
- TASK-20260312-062 | preset runtime tuning contract | Open
- TASK-20260312-063 | problem clip regression pack | Open

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [ ] false-lock behavior on the key `night` / `ir` problem clips is measurably improved or at least explicitly bounded
- [ ] runtime tuning differences for `day`, `night`, and `ir` are explicit in config and docs
- [ ] one canonical short problem-clip regression pack exists and is wired into the local evaluation flow
