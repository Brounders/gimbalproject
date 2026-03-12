# BRIEF: BRIEF-20260312-024-runtime-hardening-stage4-v1

## Context
The first three runtime-hardening cycles improved tooling discipline, IR behavior, and some noise-scene bounding, but they did not close the remaining operator-facing weakness on the hardest night scenes. The most persistent failures are `night_ground_indicator_lights` and especially `night_ground_large_drones`, where false-lock behavior and ID churn are still too high for a reliable operator workflow.

## Objective
Run one narrow stage-4 runtime-quality cycle that targets the remaining night/noise problem directly, without opening a new training cycle, UI redesign, or architecture refactor.

## Success Metrics
- KPI 1: `night_ground_indicator_lights` remains bounded and does not regress into runaway noise-driven lock behavior.
- KPI 2: `night_ground_large_drones` shows materially lower `active_id_changes_per_min` and lower `false_lock_rate` in the short problem-pack loop.
- KPI 3: the problem-pack mini-gate becomes a real short acceptance barrier for future runtime cycles.

## Boundaries
- Must do:
  - narrow night/noise runtime hardening only
  - focus on scene-specific gating, reacquire/release/hold behavior, and problem-pack thresholds
  - keep current local desktop product flow intact
- Must not do:
  - new training cycle
  - new UI redesign
  - `pipeline.py` or `main_gui.py` refactor
  - Hailo / RPi migration
  - automation expansion

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- Task list
- Validation plan
- Review gate
