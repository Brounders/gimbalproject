# TASK: TASK-20260312-068-large-drones-night-stability-fix

Task ID: TASK-20260312-068
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Сфокусированно исправить поведение на `night_ground_large_drones`, где stage-2 дал резкий рост `active_id_changes_per_min` и высокий `false_lock_rate`.

## Scope
- In scope:
  - `src/uav_tracker/pipeline.py`
  - `src/uav_tracker/tracking/target_manager.py`
  - `src/uav_tracker/tracking/lock_tracker.py`
  - `src/uav_tracker/config.py`
  - `configs/night.yaml`
  - `OPERATOR_BASELINE.md` if runtime knobs change
- Out of scope:
  - training changes
  - UI changes
  - broad refactor of tracking architecture

## Constraints
- Minimal reversible diff
- Fix the specific large-drones night behavior, not all night scenes at once
- Keep operator-visible semantics stable
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `src/uav_tracker/pipeline.py`
  - `src/uav_tracker/tracking/target_manager.py`
  - `src/uav_tracker/tracking/lock_tracker.py`
  - `src/uav_tracker/config.py`
  - `configs/night.yaml`
- Context:
  - the last accepted cycle documented a hard regression on `night_ground_large_drones`

## Implementation Steps
1. Trace why the current night runtime creates repeated ID churn / reacquire instability on the large-drones clip.
2. Apply narrow hold/release/reacquire tuning specifically to reduce operator-visible instability on this scenario.
3. Validate that the fix does not simply trade the regression for a complete lock collapse.

## Acceptance Criteria
- [ ] `night_ground_large_drones` no longer shows runaway `active_id_changes_per_min`
- [ ] the clip remains operator-usable; the fix is not just a hard suppression collapse
- [ ] the change stays within the current runtime architecture

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --sources test_videos/night_ground_large_drones.mp4 --max-frames 180 --preset night`
- Expected result:
  - compile clean
  - existing tests still pass
  - the large-drones clip shows materially lower `id_changes/min` and no obvious continuity collapse

## Risks
- Risk: the “fix” degenerates into simply suppressing all activity on the clip
- Mitigation: review continuity and presence together with `id_changes/min` and `false_lock`
