# REPORT-TASK-114-SYNC-BOUNDARY-DECISION-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted locally

## Scope

TASK-20260517-114 требовала выбрать стратегию синхронизации перед RTX sync,
push или возвратом к detector/training.

## Options Considered

| Strategy | Decision | Reason |
|----------|----------|--------|
| Push local `main` to `origin/main` | Rejected now | Local `main` is 171 commits ahead and mixes runtime, tests, configs, orchestrator, local agent/team artifacts and memory/docs. Too much blast radius for default branch. |
| Selective cherry-pick line | Rejected now | The useful detector/tracking/training state depends on a long chain of runtime/config/test/orchestrator commits. Cherry-picking by hand risks a broken RTX tree. |
| Patch bundle only | Rejected as primary | Technically safe, but awkward for RTX/Codex workflow and easy to desync. Useful only as fallback if remote branch cannot be used. |
| Clean sync branch from current verified HEAD | Selected | Preserves all dependencies and keeps `main` protected. RTX can fetch a named branch without forcing remote main forward. |

## Selected Strategy

Create/use branch:

```text
codex/sync-boundary-20260517
```

Rules:

- Do not push `main`.
- Do not ask RTX to pull `main`.
- Use the sync branch as the explicit Mac snapshot for RTX work.
- Before RTX training, verify that RTX checked out exactly this branch/commit.
- If the branch must be published, push only this branch, not `main`.

## Required RTX Intake Check

On RTX, after fetching the branch:

```bash
git fetch origin codex/sync-boundary-20260517
git switch codex/sync-boundary-20260517
git rev-parse --short HEAD
python --version
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO_CUDA")
PY
python orchestrator/scripts/check_orchestration_state.py
python -m compileall -q python_scripts src app orchestrator tests
```

Expected Mac HEAD at decision time:

```text
258f1c7
```

After this report is committed, the expected branch HEAD will be the commit that
contains this decision.

## Next Task

Open TASK-20260517-115:

- create/switch to `codex/sync-boundary-20260517`;
- validate branch state;
- decide whether to push the branch for RTX or keep it local until Human asks for
  network sync.

## Non-Changes

- No push performed by this report.
- No runtime/training/UI code changed.
- No detector training started.
