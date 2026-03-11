# Tests

Unit tests for `uav_tracker`. No external hardware or heavy deps required.

## Run all tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Run individual suites

```bash
PYTHONPATH=src python3 -m unittest -v tests.test_target_manager_lock_policy
PYTHONPATH=src python3 -m unittest -v tests.test_package_import
```

## Test suites

| File | Coverage |
|---|---|
| `test_target_manager_lock_policy.py` | Lock confirmation, active ID switch, lost transition, focus mode hysteresis, `select_active()` policy |
| `test_package_import.py` | Import boundary — Config and TargetManager accessible without pipeline/cv2 |
