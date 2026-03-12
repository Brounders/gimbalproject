# TASK: TASK-20260312-061-night-ir-false-lock-suppression

Task ID: TASK-20260312-061
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Снизить ложные `lock` и шумовые reacquire на `night` / `ir` / noise сценах без глобального переписывания tracking logic и без резкого ухудшения continuity на реальной цели.

## Scope
- In scope:
  - `src/uav_tracker/pipeline.py`
  - `src/uav_tracker/config.py`
  - `src/uav_tracker/tracking/target_manager.py`
  - `src/uav_tracker/tracking/lock_tracker.py`
  - `OPERATOR_BASELINE.md`
  - targeted validation scripts/reports if needed
- Out of scope:
  - новый training cycle
  - полный redesign tracking policy
  - UI changes

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `src/uav_tracker/pipeline.py`
  - `src/uav_tracker/config.py`
  - `src/uav_tracker/tracking/target_manager.py`
  - `src/uav_tracker/tracking/lock_tracker.py`
  - `OPERATOR_BASELINE.md`
- Context:
  - main operational weakness remains high `false_lock_rate` on `night` / `ir` / noise clips;
  - recent candidate models improved some continuity metrics but remained too aggressive in false activation behavior.

## Implementation Steps
1. Audit current `lock confirm`, `unverified_active`, `reacquire`, and short-gap hold behavior under `night` / `ir` / noise contexts.
2. Apply narrow runtime changes that harden false-lock suppression only where the noise problem is real.
3. Validate the result against the problem clips and ensure the operator flow still behaves coherently.

## Acceptance Criteria
- [ ] false-lock suppression is measurably tighter on the known `night` / `ir` problem clips
- [ ] no broad tracking-policy rewrite is introduced
- [ ] runtime behavior remains compatible with current local baseline governance and operator flow

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --sources test_videos/night_ground_large_drones.mp4,test_videos/night_ground_indicator_lights.mp4,test_videos/IR_DRONE_001.mp4 --max-frames 180 --preset night`
- Expected result:
  - compile clean
  - existing tests still pass
  - problem-clip metrics demonstrate improved or at least non-regressed false-lock behavior

## Risks
- Risk: over-tightening suppression reduces sensitivity to a weak real target
- Mitigation: validate not only `false_lock_rate`, but also continuity/presence on the same clips
