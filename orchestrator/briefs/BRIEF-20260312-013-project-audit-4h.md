# BRIEF: BRIEF-20260312-013-project-audit-4h

## Context
- Human requested a full project audit from idea to implementation with a strict 4-hour analysis budget.
- The purpose of this cycle is diagnosis and planning only, not implementation.
- The project now has a large surface area: runtime tracking, PySide6 UI, training/eval workflows, orchestration, and emerging Codex automation scaffolding.

## Objective
- Produce a rigorous engineering audit of GimbalProject across:
  - architecture;
  - execution workflows;
  - filesystem structure;
  - training/evaluation conveyor;
  - validation and quality controls.
- Convert that audit into an actionable evolution plan with explicit priorities.

## Success Metrics
- One primary audit report exists with concrete findings, not general observations.
- Findings are prioritized (`P0/P1/P2`) and tied to code or workflow evidence.
- The report clearly separates:
  - what is working well;
  - what is fragile or contradictory;
  - what should be fixed next;
  - what should be left untouched for now.

## Boundaries
- Must do:
  - read code, docs, orchestration state, git history, and repo structure;
  - run validation and inspection commands as needed;
  - produce a concrete roadmap after the audit.
- Must not do:
  - modify runtime code;
  - refactor files;
  - change training artifacts, datasets, or runs;
  - open a new implementation cycle.

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- Primary audit report in `orchestrator/reports/REPORT-20260312-032.md`
- Architecture findings summary
- Filesystem findings summary
- Workflow findings summary
- Prioritized next-step roadmap
