# TASK: TASK-20260313-077-codex-conclusion-review-corrected

Task ID: TASK-20260313-077
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Re-run the adversarial review of Codex's current conclusion, but this time explicitly use the already accepted post-hardening reviewer measurements from stage-4 and stage-4b instead of assuming that no such measurements exist.

## Scope
- In scope:
  - analysis of the current repository state and accepted reviewer evidence
  - challenge Codex's conclusion using the actual accepted post-hardening metrics
  - propose the most rational next step if Codex's conclusion is not fully correct
- Out of scope:
  - no code/config/runtime changes
  - no training execution
  - no orchestration state edits beyond the report

## Constraints
- Analysis only
- No implementation
- Must use accepted reviewer evidence already recorded in the repository
- Do not repeat the whole audit; stay focused on whether Codex's current next-step conclusion is correct
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `orchestrator/state/project_state.md`
  - `orchestrator/state/completed_tasks.md`
  - `orchestrator/reports/REPORT-20260312-070.md`
  - `orchestrator/reports/REPORT-20260312-071.md`
  - `orchestrator/reports/REPORT-20260312-072.md`
  - `orchestrator/reports/REPORT-20260313-073.md`
  - `orchestrator/reports/REPORT-20260313-074.md`
  - `orchestrator/reports/REPORT-20260313-075.md`
  - `configs/night.yaml`
  - `configs/problem_pack_gate_contract.json`
  - `RUNBOOK.md`
- Evidence:
  - accepted reviewer summaries for stage-4 and stage-4b in `project_state.md`
  - the current problem-pack contract and latest accepted runtime-hardening outputs

## Implementation Steps
1. Read the accepted reviewer summaries for stage-4 and stage-4b from `project_state.md`.
2. Re-check Codex's current conclusion against those accepted post-hardening measurements.
3. Identify where Codex is correct, where Codex is weak or wrong, and whether a better next step exists.
4. Write one concise review report with a final verdict:
   - `confirmed`
   - `partially_wrong`
   - `wrong`

## Acceptance Criteria
- [ ] The report explicitly cites the accepted post-hardening reviewer measurements.
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
  - the follow-up could still ignore accepted reviewer evidence and restate unsupported assumptions
- Mitigation:
  - force the task to anchor itself on `project_state.md` reviewer summaries before drawing conclusions
