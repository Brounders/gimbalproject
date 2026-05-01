# Worktree Review — 2026-05-01

Current status after Codex-control handoff.

No runtime changes are authorized by this file.
This is a classification registry for old Claude branches, local tool folders, and design reference folders.

## Current Main State

| Item | Status |
|------|--------|
| Current branch | `main` |
| Current head | `5b7b05e` before this risk-closure session |
| `active_plan.md` | `Completed` |
| Active Claude tasks | none |
| Active RTX tasks | none |
| Open backlog tasks | none |

## Claude Worktrees

Claude worktrees are archive/reference material unless `active_plan.md` names a specific task for one of them.

| Branch | Ahead of `main` | Behind `main` | Classification | Decision |
|--------|-----------------|---------------|----------------|----------|
| `claude/busy-bhaskara-4ebe9f` | 0 | 10 | merged/obsolete | archive only |
| `claude/busy-hamilton-9c2e2a` | 0 | 12 | merged/obsolete | archive only |
| `claude/cool-lehmann-1ef3aa` | 0 | 2 | merged/obsolete | archive only |
| `claude/elastic-hawking-25f3dd` | 0 | 45 | merged/obsolete | archive only |
| `claude/funny-hugle-328c74` | 0 | 55 | merged/obsolete | archive only |
| `claude/interesting-visvesvaraya-c35788` | 0 | 15 | merged/obsolete | archive only |
| `claude/nifty-golick-21e65b` | 0 | 56 | merged/obsolete | archive only |
| `claude/optimistic-wiles-6ee846` | 0 | 55 | merged/obsolete | archive only |
| `claude/sharp-spence-afd285` | 0 | 56 | merged/obsolete | archive only |
| `claude/trusting-bose-308c4d` | 0 | 56 | merged/obsolete | archive only |
| `claude/elastic-babbage-b20fe7` | 2 | 107 | stale wiki build | do not merge without review |
| `claude/elegant-vaughan-284df8` | 1 | 56 | stale phase-2 plan | do not merge without review |
| `claude/eloquent-ride-82b6f9` | 2 | 56 | stale phase-0 work | do not merge without review |
| `claude/inspiring-agnesi-c7897f` | 1 | 56 | stale UI/design work | preserve as UI reference only |
| `worktree-agent-a3ff75ebca884588b` | 1 | 120 | stale TD-003 duplicate | do not merge without review |

## Local Untracked Workspaces

These folders are intentionally ignored in `.gitignore`.
They are not deleted.

| Path | Classification | Decision |
|------|----------------|----------|
| `.claire/` | local agent workspace | ignore locally |
| `.claude/worktrees/` | Claude archive worktrees | ignore locally |
| `.obsidian/` | local Obsidian app state for this folder | ignore locally |
| `memory/claude-memory-compiler/` | external Claude memory repo/tool | ignore locally |
| `Gimbal design/` | UI reference prototype | keep as reference, not execution source |
| `design_refs/` | UI reference exports | keep as reference, not execution source |

## Authority Rule

- `main` + accepted reports + `active_plan.md` are canonical.
- Old Claude branches are not canonical.
- Obsidian is context, not proof of completion.
- Claude memory is archive only.
- Broad prompts to Claude are forbidden; use single-scope prompts only.

## Remaining Human Decision

`main` is ahead of `origin/main`.
Pushing to GitHub is the only way to remove the remote-backup risk, but it requires explicit Human approval.
