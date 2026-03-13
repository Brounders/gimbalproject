# TASK: TASK-20260313-079-large-target-night-detector-tuning

## Goal
Tune the newly exposed large-target night detector/runtime knobs to improve `night_ground_large_drones` without regressing `night_ground_indicator_lights`.

## Scope
- In scope:
  - large-target night tuning using `night_max_area`, `night_track_dist`, `night_lost_max`
  - minimal supporting tuning of existing night runtime knobs only if required for the large-target scenario
  - before/after evidence on the night problem pack
- Out of scope:
  - no new training
  - no GUI changes
  - no global retune of all night behavior

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
  - `src/uav_tracker/config.py`
  - `src/uav_tracker/profile_io.py`
  - `configs/regression_pack_problem_night.csv`
- Context:
  - accepted stage-4b caveat: `night_ground_large_drones` remains the main unresolved runtime defect

## Implementation Steps
1. Use the exposed detector-level night knobs as the primary tuning surface for the large-target night case.
2. Adjust the smallest set of values needed to reduce large-target `false_lock_rate` and `active_id_changes_per_min`.
3. Keep `night_ground_indicator_lights` as the no-regression clip in the same loop and summarize the tradeoff.

## Acceptance Criteria
- [ ] `night_ground_large_drones` improves beyond the current stage-4b point (`false_lock < 0.750`, `id_chg/min < 55.05`).
- [ ] `night_ground_indicator_lights` does not regress versus the current accepted point.
- [ ] Changes remain detector/runtime-contract focused, not a broad night-policy rewrite.

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_problem_pack_gate.py --context night --preset night --tag large_target_tuned`
- Expected result:
  - compile/test pass; the night problem pack shows measurable improvement on `night_ground_large_drones` without indicator-light regression

## Risks
- Risk:
  - large-target tuning may widen false reacquire or suppress weak true targets
- Mitigation:
  - keep tuning local to the exposed detector/runtime knobs and validate against both night problem clips
