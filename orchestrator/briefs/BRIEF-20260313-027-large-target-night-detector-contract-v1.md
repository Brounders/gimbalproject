# BRIEF: BRIEF-20260313-027-large-target-night-detector-contract-v1

## Context
Post-hardening reviewer synthesis confirms that the main remaining product defect is `night_ground_large_drones`. The current runtime hardening cycles improved bounded behavior on other night/noise scenes, but the large-target night clip still shows unacceptable `false_lock_rate` and `active_id_changes_per_min`. The accepted corrected adversarial review concluded that the next rational step is not a new training cycle and not a broad lock-policy rewrite, but a narrow detector/runtime contract cycle around night large-target behavior.

## Objective
Expose the remaining detector-level night knobs through the profile/YAML contract and use them to tune large-target night behavior without regressing the already-bounded indicator-lights scene.

## Success Metrics
- `night_ground_large_drones` improves versus the current stage-4b reference point:
  - `false_lock_rate < 0.750`
  - `active_id_changes_per_min < 55.05`
- `night_ground_indicator_lights` does not regress versus the current accepted point.
- The detector-level night knobs are configurable through profile/YAML, not only hard-coded in runtime.

## Boundaries
- Must do:
  - expose `NIGHT_MAX_AREA`, `NIGHT_TRACK_DIST`, `NIGHT_LOST_MAX` through profile/YAML plumbing
  - tune only the large-target night detector/runtime contract
  - produce before/after evidence on the night problem pack
- Must not do:
  - no training
  - no GUI changes
  - no `pipeline.py`/`main_gui.py` refactor
  - no broad night-policy rewrite
  - no embedded/Hailo work

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- Task list for the narrow detector/runtime contract cycle
- Validation plan using the existing problem-pack gate
- Review gate based on large-target night improvement without indicator-light regression
