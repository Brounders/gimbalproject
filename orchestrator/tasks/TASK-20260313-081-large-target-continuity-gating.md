# Task ID
- TASK-20260313-081

# Owner
- Claude Mac

# Priority
- P0

# Goal
- Reduce false target switching on `night_ground_large_drones` by tightening spatial/scale continuity checks for already-held large night targets.

# Files
- `src/uav_tracker/config.py`
- `src/uav_tracker/profile_io.py`
- `src/uav_tracker/detectors/night_detector.py`
- `src/uav_tracker/pipeline.py`
- `configs/night.yaml`

# Expected Result
- Large-target night continuity is governed by explicit runtime parameters rather than implicit detector behavior.
- The runtime becomes more resistant to abrupt candidate replacement when a large target is already being tracked at night.
- No intended behavior change outside the large-target night path.

# Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
- Run the canonical problem-pack loop and provide before/after evidence for `night_ground_large_drones`.

# Constraints
- Minimal, reversible diff.
- No training changes.
- No GUI changes.
- Do not broaden to a full global `night` retune.

# Status
- Accepted
