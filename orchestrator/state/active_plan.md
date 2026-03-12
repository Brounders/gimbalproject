# Active Plan

## Plan ID
- AP-20260312-017

## Source Direction
- Human direction: move to the next stage after `main_gui.py` stage-0 split.
- Scope: local quality enforcement only — make preset-specific gate usage explicit, harden local baseline/candidate decision flow, and normalize local benchmark/quality summary artifacts.

## Status
- Active

## Brief In Focus
- BRIEF-20260312-020-local-quality-enforcement-v1

## Active Claude Tasks (execution allowed now)
- TASK-20260312-058 | preset gate enforcement | Open
- TASK-20260312-059 | baseline candidate decision hardening | Open
- TASK-20260312-060 | quality report normalization | Open

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [ ] preset-specific gate contexts for `day`, `night`, and `ir` are explicit in the local quality flow
- [ ] local baseline/candidate decision flow is tied to preset-specific evidence and install traceability
- [ ] benchmark and quality-gate outputs converge on one canonical local summary artifact contract
