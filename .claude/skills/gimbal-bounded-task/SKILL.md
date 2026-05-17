---
name: gimbal-bounded-task
description: Use for every GimbalProject task from Codex/Human. Enforces bounded-worker behavior: exact scope, minimal reads, no autonomous planning, no broad wiki/memory/report loading, no commits or pushes unless explicitly requested.
---

# Gimbal Bounded Task

## Purpose

Use this skill before any GimbalProject work.
Claude is a bounded worker. Codex/Human controls planning, scope, acceptance, and next steps.

## Startup Contract

Read only:

1. Current Codex/Human prompt or handoff.
2. `git status --short --branch`.
3. Files explicitly named by the prompt.
4. Narrow `rg` / `rg --files` discovery needed inside the allowed scope.

Do not read by default:

- `../wiki/**`
- `memory/**`
- `orchestrator/reports/**`
- `orchestrator/tasks/**`
- `.claude/playbooks/**`
- old `.claude/worktrees/**`

## Before Editing

State briefly:

- task goal;
- allowed files;
- files that must not be edited;
- validation commands;
- blocker if scope is unclear.

If the task lacks allowed files, infer the smallest safe set from the prompt.
If you must go outside that set, stop and ask.

## Work Rules

- Minimal reversible diff.
- Preserve existing public names, Qt signals/slots, worker lifecycle, and tests.
- Do not add dependencies.
- Do not update wiki/memory/session logs by default.
- Do not commit or push unless explicitly requested.
- Do not choose the next project task.

## Final Answer

Always answer:

1. Plan
2. Changes
3. Validation
4. Risks

Keep it concise and factual.
