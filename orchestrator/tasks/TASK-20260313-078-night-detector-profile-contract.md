# TASK: TASK-20260313-078-night-detector-profile-contract

## Goal
Expose detector-level night knobs through the profile/YAML contract so that large-target night tuning can be performed without hard-coded edits.

## Scope
- In scope:
  - profile/YAML plumbing for `NIGHT_MAX_AREA`, `NIGHT_TRACK_DIST`, `NIGHT_LOST_MAX`
  - config/profile mapping updates
  - minimal documentation updates for the night runtime contract
- Out of scope:
  - no new training
  - no GUI changes
  - no broad detector rewrite

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
  - `src/uav_tracker/profile_io.py`
  - `configs/night.yaml`
  - `OPERATOR_BASELINE.md`
- Context:
  - unified next-step conclusion from accepted corrected adversarial review

## Implementation Steps
1. Identify how detector-level night knobs are currently defined and where profile/YAML mapping is missing.
2. Add the minimal profile/YAML mapping for `night_max_area`, `night_track_dist`, and `night_lost_max`.
3. Update the night runtime contract documentation to reflect these new configurable knobs.

## Acceptance Criteria
- [ ] `NIGHT_MAX_AREA`, `NIGHT_TRACK_DIST`, and `NIGHT_LOST_MAX` are configurable through profile/YAML.
- [ ] The night runtime contract reflects the new knobs clearly.
- [ ] Changes remain narrow and do not alter unrelated runtime behavior.

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_problem_pack_gate.py --context night --preset night --tag detector_contract_check`
- Expected result:
  - compile/test pass; problem-pack gate still runs with the new profile contract present

## Risks
- Risk:
  - exposing the knobs could create inconsistent preset values if not documented clearly
- Mitigation:
  - keep the contract limited to `night` and update the night runtime documentation in the same diff
