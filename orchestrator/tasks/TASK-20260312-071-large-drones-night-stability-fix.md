# TASK: TASK-20260312-071-large-drones-night-stability-fix

Task ID: TASK-20260312-071
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Точечно стабилизировать runtime поведение на `night_ground_large_drones`, снизив runaway `active_id_changes_per_min` и уменьшив ложные reacquire/release циклы без переписывания tracking policy целиком.

## Scope
- In scope:
  - `src/uav_tracker/pipeline.py`
  - `src/uav_tracker/config.py`
  - `src/uav_tracker/tracking/target_manager.py`
  - `src/uav_tracker/tracking/lock_tracker.py`
  - `configs/night.yaml`
  - `OPERATOR_BASELINE.md` if runtime contract values change
- Out of scope:
  - training changes
  - GUI changes
  - global algorithm rewrite

## Constraints
- Minimal reversible diff
- No full tracking-policy rewrite
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
  - `configs/night.yaml`
  - `configs/problem_pack_gate_contract.json`
- Context:
  - `night_ground_large_drones` remains the worst night runtime scene, with runaway `id_changes/min` and high `false_lock_rate` even after stage-3 hardening.

## Implementation Steps
1. Identify which release/reacquire/hold transitions still generate instability on the large-drones night clip.
2. Apply narrow runtime changes that reduce repeated lock switching and short-gap reacquire churn.
3. Validate specifically against `night_ground_large_drones` and its paired problem-pack context.

## Acceptance Criteria
- [ ] `night_ground_large_drones` shows materially lower `active_id_changes_per_min` in the short problem-pack loop
- [ ] `false_lock_rate` on the clip is reduced or clearly bounded better than the current stage-3 baseline
- [ ] no full tracking-policy rewrite is introduced

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --sources test_videos/night_ground_large_drones.mp4,test_videos/night_ground_indicator_lights.mp4 --max-frames 180 --preset night`
- Expected result:
  - compile clean
  - existing tests still pass
  - the large-drones clip no longer shows runaway instability in the short loop

## Risks
- Risk: over-stabilizing large-drones behavior can add lag or suppress valid reacquire
- Mitigation: keep the changes local to release/reacquire/hold behavior and validate against the paired problem clip set
