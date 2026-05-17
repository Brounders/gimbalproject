# REPORT-TASK-116-RTX-SYNC-INTAKE-PROMPT-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Mac-side handoff ready; RTX verification pending

## Branch

Use only:

```text
codex/sync-boundary-20260517
```

Do not pull `main` for this step.

## RTX Prompt

Paste this into the RTX Codex session from repository root:

```text
Продолжаем GimbalProject RTX sync intake.

Scope:
- Do not train yet.
- Do not modify files.
- Fetch and switch to Mac sync branch `codex/sync-boundary-20260517`.
- Verify exact branch/HEAD, Python/CUDA/Torch/Ultralytics, orchestrator state,
  and compileall.

Commands:
1. git fetch origin codex/sync-boundary-20260517
2. git switch codex/sync-boundary-20260517
3. git status --short --branch
4. git rev-parse --short HEAD
5. python --version
6. python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda_available", torch.cuda.is_available())
print("cuda_device_count", torch.cuda.device_count())
print("cuda_device_0", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO_CUDA")
PY
7. python - <<'PY'
import ultralytics
print("ultralytics", ultralytics.__version__)
PY
8. python orchestrator/scripts/check_orchestration_state.py
9. python -m compileall -q python_scripts src app orchestrator tests

Return:
- current branch;
- HEAD short hash;
- git status;
- Python/Torch/CUDA/Ultralytics versions;
- validation results;
- whether RTX is ready for detector/training next step.
```

## Mac Notes

- Branch was published to `origin/codex/sync-boundary-20260517`.
- `main` was not pushed.
- TASK-20260517-116 remains active until RTX returns verification.
