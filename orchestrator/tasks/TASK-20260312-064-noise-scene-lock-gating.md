# TASK: TASK-20260312-064-noise-scene-lock-gating

Task ID: TASK-20260312-064
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Отдельно ужесточить `lock` / `reacquire` gating на шумовых `night`-сценах типа `night_ground_indicator_lights`, чтобы снизить ложные operator-visible захваты без глобального переписывания tracking policy.

## Scope
- In scope:
  - `src/uav_tracker/pipeline.py`
  - `src/uav_tracker/config.py`
  - `src/uav_tracker/tracking/target_manager.py`
  - `src/uav_tracker/tracking/lock_tracker.py`
  - `configs/night.yaml`
  - `configs/antiuav_thermal.yaml` if the same gating path is shared
  - `RUNBOOK.md` / `OPERATOR_BASELINE.md` if the runtime contract changes
- Out of scope:
  - training changes
  - UI changes
  - full tracking-policy redesign

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
  - `configs/antiuav_thermal.yaml`
- Context:
  - `night_ground_indicator_lights` remains the clearest noise-scene weakness after the first hardening cycle;
  - the goal is to reduce false acquisition pressure only where the noise problem is real.

## Implementation Steps
1. Audit where noise-like night scenes still pass into lock/reacquire despite the first hardening pass.
2. Apply narrow gating changes so noisy scenes need stronger confirmation before becoming operator-visible lock transitions.
3. Validate against the problem clips and confirm the change does not globally degrade continuity.

## Acceptance Criteria
- [ ] noise-scene false locks are reduced or more tightly bounded on the canonical problem clips
- [ ] no global behavior rewrite is introduced
- [ ] runtime behavior remains compatible with the current operator baseline contract

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --sources test_videos/night_ground_indicator_lights.mp4,test_videos/night_ground_large_drones.mp4 --max-frames 180 --preset night`
- Expected result:
  - compile clean
  - existing tests still pass
  - problem-clip metrics show improved or explicitly bounded noise-scene false-lock behavior

## Risks
- Risk: over-tightening gating suppresses weak true targets
- Mitigation: validate continuity/presence alongside false-lock metrics on the same clips
