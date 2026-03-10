# Tests

Unit tests for GimbalProject tracking logic.

## Run

From the project root with virtualenv activated:

```bash
source tracker_env/bin/activate
PYTHONPATH=src python3 -m unittest -q tests.test_target_manager_lock_policy
```

Or run all tests in the directory:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -q
```

## Compile check

```bash
PYTHONPATH=src python3 -m compileall -q python_scripts src app tests
```

## Coverage

| File | Tests |
|---|---|
| `test_target_manager_lock_policy.py` | Lock confirmation hysteresis, active ID switch cooldown, LOST transition, focus mode enter/exit |

## Rules

- No external dependencies beyond the standard library.
- No model inference or video processing in unit tests.
- Test only contractual behavior (state transitions, counters). Not internal variable names.
