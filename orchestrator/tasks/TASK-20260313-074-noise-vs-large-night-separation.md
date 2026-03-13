# TASK: TASK-20260313-074-noise-vs-large-night-separation

## Goal
Separate runtime handling for noise-like night scenes and large-target night scenes so the project does not keep using one blunt `night` policy for both.

## Scope
- In scope:
  - narrow runtime/config separation for noise-like vs large-target night behavior
  - explicit and readable contract for the distinction
- Out of scope:
  - no ML scene classifier
  - no large config-system rewrite
  - no UI changes

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `configs/night.yaml`
  - `configs/problem_pack_gate_contract.json`
  - `RUNBOOK.md`
  - runtime files touched by `night` tuning if needed
- Context:
  - `indicator_lights` is bounded; `large_drones` is still failing; these should not be forced through one undifferentiated policy

## Implementation Steps
1. Identify the smallest configuration/runtime contract that distinguishes noise-like night from large-target night behavior.
2. Implement that distinction without adding broad new complexity.
3. Document the resulting local runtime contract in the canonical docs.

## Acceptance Criteria
- [ ] The code/config/docs show an explicit separation between noise-like night and large-target night handling.
- [ ] The separation is narrow, understandable, and does not require a major new subsystem.
- [ ] The resulting contract is reflected in the local runtime docs.

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_problem_pack_gate.py --context night --preset night --tag stage4b_separation_check`
- Expected result:
  - compile succeeds and the problem-pack flow runs with the updated contract

## Risks
- Risk:
  - the distinction may become too implicit or too ad hoc
- Mitigation:
  - require the contract to be explicit in config/docs and evidenced by the problem-pack loop
