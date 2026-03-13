# Task ID
- TASK-20260313-082

# Owner
- Claude Mac

# Priority
- P0

# Goal
- Reduce runaway reacquire/release churn for the large-target night case without degrading the already-bounded `night_ground_indicator_lights` behavior.

# Files
- `src/uav_tracker/config.py`
- `src/uav_tracker/profile_io.py`
- `src/uav_tracker/pipeline.py`
- `configs/night.yaml`
- `RUNBOOK.md`

# Expected Result
- Reacquire/release behavior for large targets at night is more conservative and less bursty.
- `night_ground_large_drones` shows lower `active_id_changes_per_min` than the current accepted point.
- `night_ground_indicator_lights` stays at or better than the current bounded behavior.

# Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
- Re-run the night problem-pack and show before/after metrics for both:
  - `night_ground_large_drones`
  - `night_ground_indicator_lights`

# Constraints
- No training.
- No refactor beyond what is strictly needed for this runtime fix.
- Do not rewrite the whole lock policy.

# Status
- Accepted
