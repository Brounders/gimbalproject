# BRIEF: BRIEF-20260313-025-runtime-hardening-stage4b-v1

## Context
`runtime hardening stage-4` bounded the indicator-lights case but did not solve the large-target night failure mode. The current product bottleneck is no longer architecture or tooling; it is operator stability on the worst night/noise scenes.

## Objective
Run one narrow runtime-quality cycle that targets `night_ground_large_drones` and preserves the already-bounded `night_ground_indicator_lights` behavior.

## Success Metrics
- KPI 1: `night_ground_large_drones` shows materially lower `false_lock_rate` and `active_id_changes_per_min` than the stage-4 review point.
- KPI 2: `night_ground_indicator_lights` does not regress while tightening large-target night behavior.
- KPI 3: the problem-pack mini-gate becomes the canonical short acceptance barrier for this class of runtime changes.

## Boundaries
- Must do:
  - narrow runtime tuning only
  - work from existing `night` / `antiuav_thermal` preset contracts
  - use the existing problem-pack flow and produce explicit before/after evidence
- Must not do:
  - no training cycle
  - no GUI or `pipeline.py` refactor
  - no UI redesign
  - no automation or embedded work

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- One runtime hardening task for large-target night behavior
- One separation task for noise-like night vs large-target night scenes
- One problem-pack hard-gate task with explicit local evidence
- Validation plan and review gate
