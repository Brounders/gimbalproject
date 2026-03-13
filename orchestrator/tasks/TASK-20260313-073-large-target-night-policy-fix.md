# TASK: TASK-20260313-073-large-target-night-policy-fix

## Goal
Reduce `false_lock_rate` and `active_id_changes_per_min` for the `night_ground_large_drones` problem clip without globally tightening all `night` behavior.

## Scope
- In scope:
  - targeted tuning of large-target night acquire/release/reacquire/hold behavior
  - minimal reversible runtime changes in existing config/runtime plumbing
  - evidence on the problem night pack
- Out of scope:
  - no training
  - no GUI changes
  - no broad refactor

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `src/uav_tracker/config.py`
  - `src/uav_tracker/pipeline.py`
  - `configs/night.yaml`
  - `configs/regression_pack_problem_night.csv`
- Context:
  - stage-4 reviewer result left `night_ground_large_drones` as the main unresolved runtime defect

## Implementation Steps
1. Inspect the current large-target night behavior and identify the narrowest runtime knobs that influence acquire/release/reacquire churn.
2. Implement only the minimal changes needed to improve `night_ground_large_drones`.
3. Produce before/after evidence on the problem-pack clips and summarize the tradeoff.

## Acceptance Criteria
- [ ] `night_ground_large_drones` shows materially improved `false_lock_rate` and `active_id_changes_per_min` versus the stage-4 review point.
- [ ] No intentional regression is introduced on `night_ground_indicator_lights`.
- [ ] Changes remain narrow and runtime-focused, without broader refactor.

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_problem_pack_gate.py --context night --preset night --tag stage4b_large_target`
- Expected result:
  - compile/test pass; problem-pack evidence shows improvement on the large-target clip

## Risks
- Risk:
  - over-tightening may suppress weak real targets
- Mitigation:
  - preserve the indicator-lights clip as a no-regression reference in the same loop
