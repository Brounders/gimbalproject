# TASK: TASK-20260313-080-large-target-problem-gate-evidence

## Goal
Produce a clear before/after evidence loop for the large-target night tuning cycle using the existing night problem-pack gate.

## Scope
- In scope:
  - before/after evidence for `night_ground_large_drones`
  - no-regression evidence for `night_ground_indicator_lights`
  - explicit verdict: improvement / no improvement / regression
- Out of scope:
  - no benchmark redesign
  - no new quality framework
  - no unrelated clip expansion

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `configs/problem_pack_gate_contract.json`
  - `configs/regression_pack_problem_night.csv`
  - `RUNBOOK.md`
- Context:
  - this cycle must end with reproducible evidence, not only tuning changes

## Implementation Steps
1. Run and capture before/after evidence for the night problem pack centered on the large-target clip.
2. Normalize the evidence so the verdict is explicit and easy to review.
3. Update the local contract/documentation only as needed so the evidence loop remains reproducible.

## Acceptance Criteria
- [ ] There is explicit before/after evidence for `night_ground_large_drones` and `night_ground_indicator_lights`.
- [ ] The cycle ends with a clear verdict: improvement, no improvement, or regression.
- [ ] The evidence loop remains local, reproducible, and tied to the existing problem-pack mini-gate.

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_problem_pack_gate.py --context night --preset night --tag large_target_evidence`
- Expected result:
  - compile/test pass; the night problem pack produces a reproducible before/after evidence artifact and explicit verdict

## Risks
- Risk:
  - evidence may remain too informal and collapse back into ad-hoc manual interpretation
- Mitigation:
  - require a concrete before/after verdict in the report and keep it tied to the existing mini-gate artifact flow
