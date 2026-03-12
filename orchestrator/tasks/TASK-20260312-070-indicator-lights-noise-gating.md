# TASK: TASK-20260312-070-indicator-lights-noise-gating

Task ID: TASK-20260312-070
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Точечно доработать runtime gating для noise-like night сцены `night_ground_indicator_lights`, чтобы уменьшить ложные lock и не ухудшить нормальные ночные сцены.

## Scope
- In scope:
  - `src/uav_tracker/pipeline.py`
  - `src/uav_tracker/config.py`
  - `src/uav_tracker/tracking/target_manager.py`
  - `src/uav_tracker/tracking/lock_tracker.py`
  - `configs/night.yaml`
  - `RUNBOOK.md` only if the runtime tuning contract changes
- Out of scope:
  - training changes
  - UI changes
  - full scene-classifier redesign

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
  - `configs/night.yaml`
  - `configs/problem_pack_gate_contract.json`
- Context:
  - `night_ground_indicator_lights` is now bounded better than before, but still remains one of the canonical night/noise problem scenes and must become more reliably controlled.

## Implementation Steps
1. Inspect the current night/noise gating path and identify where indicator-light noise still enters lock/reacquire too easily.
2. Add narrow runtime gating or confirmation changes specifically aimed at this noise-like night behavior.
3. Validate against the paired problem clips so the fix does not globally suppress normal night tracking.

## Acceptance Criteria
- [ ] `night_ground_indicator_lights` shows lower or more tightly bounded false-lock behavior in the short problem-pack loop
- [ ] the change stays narrow and does not become a broad new scene-classifier architecture
- [ ] ordinary night behavior does not obviously collapse in the paired problem-pack run

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --sources test_videos/night_ground_indicator_lights.mp4,test_videos/night_ground_large_drones.mp4 --max-frames 180 --preset night`
- Expected result:
  - compile clean
  - existing tests still pass
  - indicator-lights behavior improves or is more tightly bounded without obvious collapse on the paired night clip

## Risks
- Risk: over-tightening the noise gate suppresses weak true targets
- Mitigation: validate only with the paired night problem clips and keep the change narrow
