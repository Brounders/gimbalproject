# TASK: TASK-20260313-076-codex-conclusion-adversarial-review

## Goal
Independently review Codex's current conclusion about the next project step and determine whether the proposed `runtime hardening stage-5 / large-target night fix` is actually the most rational priority.

## Scope
- In scope:
  - analysis of current repository state and accepted runtime-hardening outcomes
  - review of the latest night/noise metrics and quality artifacts
  - adversarial challenge to Codex's conclusion, including a better alternative if warranted
- Out of scope:
  - no code/config changes
  - no training execution
  - no new orchestration tasks or state mutations beyond the report

## Constraints
- Analysis only
- No implementation
- Use evidence from the repo; do not rely on unsupported intuition
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `orchestrator/state/project_state.md`
  - `orchestrator/state/completed_tasks.md`
  - `orchestrator/reports/REPORT-20260313-073.md`
  - `orchestrator/reports/REPORT-20260313-074.md`
  - `orchestrator/reports/REPORT-20260313-075.md`
  - `configs/night.yaml`
  - `configs/problem_pack_gate_contract.json`
  - `RUNBOOK.md`
- Evidence:
  - latest problem-pack quality outputs for stage-4 and stage-4b

## Implementation Steps
1. Read the current accepted reports and state files that frame the runtime-hardening conclusion.
2. Compare Codex's conclusion to the actual metrics and quality artifacts.
3. Identify any errors, overstatements, blind spots, or stronger alternatives.
4. Write one concise review report with a final verdict:
   - `confirmed`
   - `partially_wrong`
   - `wrong`

## Acceptance Criteria
- [ ] The report explicitly states where Codex is correct.
- [ ] The report explicitly states where Codex is wrong or weak, if applicable.
- [ ] The report names the most rational next step and justifies it with evidence.
- [ ] No implementation changes are made.

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
- Expected result:
  - no project files change except the review report

## Risks
- Risk:
  - the review could drift into a repeat of the whole audit instead of challenging the current narrow conclusion
- Mitigation:
  - stay focused on whether Codex's immediate next-step recommendation is correct
