# TASK: TASK-20260313-075-problem-pack-hard-gate-tightening

## Goal
Turn the current problem-pack mini-gate into a hard, local acceptance barrier for the two night problem scenes.

## Scope
- In scope:
  - threshold tightening for the split night problem pack
  - one canonical before/after evidence path
  - local decision-ready output
- Out of scope:
  - no redesign of the full quality-gate system
  - no new benchmark framework
  - no training changes

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
  - `python_scripts/run_problem_pack_gate.py`
  - `RUNBOOK.md`
- Context:
  - the problem pack exists, but the next cycle needs it to act as a true short barrier for night/noise runtime changes

## Implementation Steps
1. Tighten the problem-pack night thresholds so the gate becomes decision-useful for stage-4b changes.
2. Ensure there is one canonical local invocation and one canonical output path for before/after comparison.
3. Update docs so future runtime cycles must pass this barrier before broader evaluation.

## Acceptance Criteria
- [ ] The problem-pack gate contract is stricter and clearly focused on the current night problem scenes.
- [ ] There is one canonical local invocation and one canonical output interpretation path.
- [ ] The gate is suitable as a mandatory short barrier for future runtime cycles.

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_problem_pack_gate.py --context night --preset night --tag stage4b_gate_contract`
- Expected result:
  - compile succeeds and the gate produces a clear local output suitable for A/B comparison

## Risks
- Risk:
  - thresholds may become aspirational and unusable
- Mitigation:
  - keep them strict but still evidence-driven from the current reviewer baseline
