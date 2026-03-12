# Active Plan

## Plan ID
- AP-20260312-019

## Source Direction
- Human direction: move to the next stage after the first runtime-quality hardening cycle.
- Scope: runtime hardening stage-2 only — tighten noise-scene lock gating, harden reacquire/short-gap hold behavior, and introduce one canonical A/B evidence loop on the problem clips.

## Status
- Active

## Brief In Focus
- BRIEF-20260312-022-runtime-hardening-stage2-v1

## Active Claude Tasks (execution allowed now)
- TASK-20260312-064 | noise-scene lock gating | Open
- TASK-20260312-065 | reacquire and hold policy hardening | Open
- TASK-20260312-066 | problem-pack A/B evidence | Open

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [ ] noise-scene false-lock behavior is measurably reduced or at least more tightly bounded on the canonical problem clips
- [ ] reacquire / short-gap hold behavior is less noisy and more operator-predictable without a full policy rewrite
- [ ] one canonical before/after evidence loop exists for problem-clip runtime tuning
