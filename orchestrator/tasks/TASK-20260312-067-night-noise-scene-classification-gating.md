# TASK: TASK-20260312-067-night-noise-scene-classification-gating

Task ID: TASK-20260312-067
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Сделать `night` runtime менее грубым: явно выделить noise-like night behavior для сцен типа `night_ground_indicator_lights`, чтобы снизить ложные захваты без глобального ухудшения обычных ночных сцен.

## Scope
- In scope:
  - `src/uav_tracker/pipeline.py`
  - `src/uav_tracker/config.py`
  - `src/uav_tracker/tracking/target_manager.py`
  - `src/uav_tracker/tracking/lock_tracker.py`
  - `configs/night.yaml`
  - `OPERATOR_BASELINE.md` if the runtime contract changes
- Out of scope:
  - training changes
  - UI changes
  - full tracking-policy rewrite

## Constraints
- Minimal reversible diff
- Keep UI/business/runtime separation
- Do not broaden the change into a full scene classifier redesign
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
- Context:
  - after stage-2, `night_ground_indicator_lights` still behaves like a distinct noise scene rather than a normal night target scene

## Implementation Steps
1. Identify where noise-like night scenes can be distinguished without adding a broad new architecture layer.
2. Add narrow runtime gating so these scenes require stronger confirmation before becoming operator-visible lock transitions.
3. Validate that ordinary night behavior is not globally degraded.

## Acceptance Criteria
- [ ] noise-like night scenes are treated with narrower gating than the generic `night` path
- [ ] `night_ground_indicator_lights` behavior improves or is more tightly bounded in the short smoke loop
- [ ] no full scene-classifier redesign is introduced

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --sources test_videos/night_ground_indicator_lights.mp4,test_videos/night_ground_large_drones.mp4 --max-frames 180 --preset night`
- Expected result:
  - compile clean
  - existing tests still pass
  - indicator-lights false-lock behavior improves or is explicitly bounded without obvious collapse on the paired night clip

## Risks
- Risk: the gating becomes too conservative and starts suppressing weak real targets
- Mitigation: compare noise-scene improvement against the paired non-noise night clip in the same validation loop
