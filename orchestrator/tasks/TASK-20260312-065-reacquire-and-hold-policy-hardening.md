# TASK: TASK-20260312-065-reacquire-and-hold-policy-hardening

Task ID: TASK-20260312-065
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Сделать `reacquire`, short-gap hold и release/acquire hysteresis более предсказуемыми, чтобы уменьшить ложные повторные захваты и дергание на кратких пропусках цели без ухудшения operator continuity.

## Scope
- In scope:
  - `src/uav_tracker/pipeline.py`
  - `src/uav_tracker/tracking/target_manager.py`
  - `src/uav_tracker/tracking/lock_tracker.py`
  - `src/uav_tracker/config.py`
  - `configs/night.yaml`
  - `configs/antiuav_thermal.yaml`
  - `OPERATOR_BASELINE.md` if runtime knobs change
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
  - `src/uav_tracker/tracking/target_manager.py`
  - `src/uav_tracker/tracking/lock_tracker.py`
  - `src/uav_tracker/config.py`
  - `configs/night.yaml`
  - `configs/antiuav_thermal.yaml`
- Context:
  - the first runtime hardening cycle tightened lock confirmation, but reacquire and short-gap transitions still need a cleaner operator-facing behavior on problem scenes.

## Implementation Steps
1. Inventory where reacquire/hold hysteresis is still too aggressive or too eager after the first hardening pass.
2. Tighten short-gap hold, reacquire confirmation, and release/acquire hysteresis without rewriting the full tracking policy.
3. Validate on the canonical problem clips and confirm that operator continuity is not sacrificed.

## Acceptance Criteria
- [ ] short-gap reacquire behavior is less noisy on the canonical problem scenes
- [ ] hold/release/acquire transitions are more predictable without a full policy rewrite
- [ ] the runtime contract remains understandable and traceable in config/docs

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --sources test_videos/IR_DRONE_001.mp4,test_videos/Demo_IR_DRONE_146.mp4,test_videos/night_ground_large_drones.mp4 --max-frames 180 --preset ir`
- Expected result:
  - compile clean
  - existing tests still pass
  - reacquire/hold behavior is more stable on the problem scenes without obvious continuity collapse

## Risks
- Risk: too much hysteresis adds lag or suppresses legitimate reacquire
- Mitigation: validate continuity and active presence together with false-lock/id-change metrics
