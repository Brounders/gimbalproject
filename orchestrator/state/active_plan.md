# Active Plan

## Plan ID
- AP-FP-ID-SUPPRESSOR-V1

## Status
- Active

## Active Claude Tasks (execution allowed now)
- TASK-20260502-091 — FPID-004 weak-evidence suppressor bounded implementation.

Allowed scope:
- `src/uav_tracker/tracking/action_policy.py`
- `src/uav_tracker/tracking/evidence.py` only if needed for source normalization helpers
- `src/uav_tracker/pipeline.py` only for `TargetBelief.source` normalization, not broad pipeline rewrites
- `tests/test_action_policy.py`
- `tests/test_action_policy_behavior.py`
- `tests/test_tracking_evidence.py`
- `python_scripts/run_action_policy_gate.py` only if compact telemetry needs test-safe formatting
- `orchestrator/reports/REPORT-FP-ID-SUPPRESSOR-IMPLEMENTATION-20260502.md`
- `orchestrator/state/completed_tasks.md` after validation

Strict non-scope:
- model changes;
- baseline promotion;
- GUI;
- new dependencies;
- replacing `TargetManager` or `TemplateLockTracker`;
- enabling `ACTION_POLICY_BEHAVIOR_ENABLED=True` by default;
- changing gate thresholds to make failures pass.

Validation required:
- `PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_tracking_evidence.py tests/test_action_policy.py tests/test_action_policy_behavior.py tests/test_action_policy_gate.py tests/test_evaluation_telemetry.py -q`
- `PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_candidate_`
- `PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_candidate_`
- `PYTHONPATH=src tracker_env/bin/python -m compileall -q python_scripts src app orchestrator tests`
- `git diff --check`
- `PYTHONPATH=src tracker_env/bin/python orchestrator/scripts/check_orchestration_state.py`

Stop after task. Do not choose the next task.

## Active RTX Tasks (execution allowed now)
- none

## Source Direction
Human approved the next cycle on 2026-05-02 after the ActionPolicy gate runner, modality-aware policy, and visible-night diagnostic gate were completed.

Цель цикла: понять, можно ли безопасно уменьшить ложные удержания и ID-дёрганье на weak/noise evidence без ухудшения accepted day/IR gate. Codex выполняет control/telemetry/decision этап одним проходом; Claude может быть подключён только после telemetry checkpoint и только с bounded prompt.

**Строго вне рамок AP-FP-ID-SUPPRESSOR-V1:**
- смена baseline model;
- YOLO26 training/intake/promotion;
- новые зависимости;
- замена `TemplateLockTracker`;
- переписывание `TargetManager`;
- GUI;
- Hailo/Raspberry Pi;
- включение `ACTION_POLICY_BEHAVIOR_ENABLED=True` по умолчанию без отдельного решения.

## AP-FP-ID-SUPPRESSOR-V1 — False Positive / ID Suppressor

### Цель

Сначала добавить измерительный слой для false-lock evidence, затем принять архитектурное решение:

- `POLICY_SUPPRESSOR`: если false locks идут из слабого runtime evidence (`night`, `lock`, `roi`, `local`, низкая reliability);
- `DEFER_TO_MODEL_DATASET`: если false locks идут из уверенной YOLO/model детекции и policy не имеет честного runtime-сигнала для подавления.

### Рабочий план

| ID | Задача | Статус | Acceptance |
|----|--------|--------|------------|
| FPID-001 | Baseline promotion + diagnostic gates | ✅ DONE | Blocking retry PASS; diagnostic-night PASS |
| FPID-002 | Evaluation telemetry for false locks | ✅ DONE | `EvaluationReport` содержит action/source/modality/reliability counters |
| FPID-003 | Telemetry rerun + decision checkpoint | ✅ DONE | `POLICY_SUPPRESSOR_CANDIDATE`: false locks идут из weak runtime evidence |
| FPID-004 | Weak-evidence suppressor implementation | READY | Следующий bounded implementation task; не менять model/baseline |
| FPID-005 | Final report and state close | PENDING | Закрывать после FPID-004 gate result |

### Канонический план

`docs/superpowers/plans/2026-05-02-fp-id-suppressor-v1.md`

### Gate commands

Blocking promotion gate:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_candidate_
```

Visible-night diagnostic gate:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_candidate_
```

### Exit Criteria

- Blocking promotion gate remains PASS.
- Diagnostic-night gate remains non-blocking and records diagnostic reasons.
- OFF sanity: `behavior_drop_count=0`.
- If telemetry proves model-level false positive, do not add suppressor rules.
- If telemetry proves weak runtime evidence, add only guarded `ActionPolicy` rules and rerun gates.
- `pytest tests -q`, `compileall`, `git diff --check`, and `check_orchestration_state.py` pass before close.
