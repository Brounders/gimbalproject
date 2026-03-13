# BRIEF: BRIEF-20260313-026-codex-conclusion-adversarial-review

## Context
Codex concluded that the next most rational engineering step is a narrowly scoped `runtime hardening stage-5` focused on the remaining `night_ground_large_drones` / large-target night failure mode, and that a new training cycle should not start first.

## Objective
Run one adversarial review cycle in which Claude independently checks that conclusion against the current repository state, metrics, accepted reviews, and quality artifacts, and explicitly calls out any errors, weak assumptions, or better next-step alternatives.

## Success Metrics
- KPI 1: Claude produces an evidence-based review that explicitly states whether Codex is correct, partially wrong, or wrong.
- KPI 2: The review names the strongest alternative next step if it rejects Codex's conclusion.
- KPI 3: The review stays analysis-only and does not drift into implementation.

## Boundaries
- Must do:
  - read the current orchestration state, accepted reports, relevant configs, and recent quality evidence
  - challenge Codex's conclusion rather than merely restating it
  - produce one concise review report with a clear verdict
- Must not do:
  - no runtime/code/config changes
  - no new training
  - no orchestration state edits beyond the report itself
  - no backlog reshaping or task creation

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- One adversarial review report:
  - `orchestrator/reports/REPORT-20260313-076.md`
- The report must include:
  - where Codex is correct
  - where Codex is overstating or understating risk
  - the best next step and why
  - one verdict: `confirmed`, `partially_wrong`, or `wrong`
