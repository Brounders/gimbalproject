# Codex Control Protocol

Status: active
Date: 2026-05-01

## Purpose

Codex is the default project controller for GimbalProject.
Claude is no longer the autonomous project driver.

This protocol keeps Obsidian in the loop as the long-term second brain while preventing stale memory from overriding the actual project state.

## Roles

| Role | Responsibility | Authority |
|------|----------------|-----------|
| Human | product direction, approvals, priorities | final decision |
| Codex | project control, audits, active-plan shaping, acceptance review, default implementation | can propose and execute after Human intent is clear |
| Claude | optional bounded worker for a single task | cannot choose strategy or continue outside scope |
| Obsidian wiki | second brain, long-term synthesis, decision context | context source, not execution authority |
| Claude memory compiler | archive of Claude conversations | reference only, never canonical |
| Git + accepted reports | factual record of what changed and why | highest authority |

## Canonical Read Order

Codex should start GimbalProject control work with this cheap route:

1. `git status --short --branch`
2. `git log --oneline --decorate -12`
3. `orchestrator/state/active_plan.md`
4. `orchestrator/state/open_tasks.md`
5. `orchestrator/state/open_training.md`
6. Latest relevant files in `orchestrator/reports/`
7. `../wiki/maps/GimbalProject Map.md`
8. `../wiki/synthesis/source_of_truth.md`
9. `../wiki/synthesis/current_state.md`
10. `../wiki/synthesis/open_questions.md`

Claude memory is read only when the question is historical or when git/reports/wiki do not explain why a decision was made.

## Authority Rule

When sources disagree:

1. Git history and committed files win for facts.
2. Accepted reports explain why.
3. `active_plan.md` controls execution only if it passes `check_orchestration_state.py`.
4. Obsidian explains context but must be reconciled when stale.
5. Claude memory is never allowed to override git, reports, active_plan, or Obsidian canonical pages.

## Claude Usage Rule

Claude may be used only with a prompt that includes:

- exact task ID or explicit one-shot scope;
- allowed files or modules;
- non-scope list;
- validation commands;
- instruction to stop after the task and not choose the next task.

Claude must not receive broad prompts such as:

- "continue the project";
- "what next";
- "fix everything";
- "sync and proceed";
- "do the whole plan".

Old Claude branches and worktrees are archive/reference material unless `active_plan.md` explicitly activates one task that uses them.
Their current classification is recorded in `orchestrator/state/worktree_review.md`.

## Obsidian Rule

Obsidian remains part of the control loop.

Use it for:

- long-term architecture context;
- rationale behind model and dataset decisions;
- open-question history;
- relationships between reports, tasks, and concepts.

Do not use it for:

- deciding whether code changed;
- deciding whether a task is completed;
- replacing gate reports;
- overriding current `active_plan.md`.

## Ultralytics Documentation Rule

For any task whose meaning involves detectors, YOLO, tracking, models, datasets, training, validation, export, benchmarks, Raspberry Pi, Hailo, runtime inference, or deployment, Codex must use the Ultralytics knowledge route even if the user writes the request in Russian and does not use exact English trigger words.

Required local read route:

1. `../wiki/sources/ultralytics_site_map.md`
2. `../wiki/sources/ultralytics_yolo.md` when API/code details are needed
3. `../wiki/maps/Training Models Datasets Map.md` when the task affects model lifecycle or dataset decisions

If the decision depends on current API behavior, model names, export formats, tracker options, or version-specific defaults, verify against official Ultralytics docs before deciding.

Ultralytics documentation is an external technical reference. Project promotion, baseline install, and acceptance decisions still require project gates and accepted reports.

## Session Start Rule

Before new work:

1. Run or inspect orchestrator state consistency.
2. If `active_plan.md` is `Completed`, do not start work until Human selects the next cycle.
3. If `active_plan.md` is `Active`, execute only listed active tasks.
4. If state fails validation, perform reconciliation before implementation.

## Session Close Rule

For Codex-controlled work:

1. Update only the state files needed for the task.
2. Keep Obsidian updates separate unless the task explicitly changes project memory.
3. Run validation.
4. Commit governance changes separately from runtime/code changes.
5. Report remaining drift explicitly.

## Remote Publication Rule

Do not push `main` to `origin/main` from an orchestration session unless Human explicitly approves remote publication.
If local commits are ahead of `origin/main`, report the count and keep the project locally backed up before continuing.
