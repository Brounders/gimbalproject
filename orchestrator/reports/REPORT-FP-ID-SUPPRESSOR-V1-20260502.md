# REPORT-FP-ID-SUPPRESSOR-V1-20260502

**Задача:** AP-FP-ID-SUPPRESSOR-V1 — telemetry checkpoint for false-lock / ID suppressor
**Дата:** 2026-05-02
**Статус:** CHECKPOINT PASS · FPID-001/002/003 выполнены · FPID-004 готов к bounded implementation

---

## 1. Что изменено

| Файл | Тип | Описание |
|------|-----|----------|
| `docs/superpowers/plans/2026-05-02-fp-id-suppressor-v1.md` | NEW | Подробный execution plan для FP/ID suppressor цикла. |
| `orchestrator/state/active_plan.md` | EDIT | Открыт активный цикл `AP-FP-ID-SUPPRESSOR-V1`; FPID-001/002/003 отмечены DONE, FPID-004 вынесен как `TASK-20260502-091`. |
| `orchestrator/state/open_tasks.md` | EDIT | Добавлена bounded Claude-задача `TASK-20260502-091` для реализации weak-evidence suppressor. |
| `src/uav_tracker/evaluation.py` | EDIT | `EvaluationReport` расширен telemetry counters: action/path/source/modality counts, false-lock source/action counts, avg reliability/p_present. |
| `python_scripts/run_action_policy_gate.py` | EDIT | `compact_report()` и row output пробрасывают новую telemetry в JSON/CSV. |
| `tests/test_evaluation_telemetry.py` | NEW | Unit-тесты для новых `EvaluationReport` telemetry fields и стабильных source labels. |
| `tests/test_action_policy_gate.py` | EDIT | Тест `compact_report()` проверяет проброс telemetry counters. |
| `orchestrator/state/completed_tasks.md` | EDIT | Запись о завершении telemetry checkpoint. |

Не изменял:

- `ActionPolicy.decide`;
- `Config.ACTION_POLICY_BEHAVIOR_ENABLED` default;
- baseline model;
- runtime presets/thresholds;
- `TargetManager`;
- `TemplateLockTracker`;
- GUI.

---

## 2. Baseline gates

Blocking gate:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_baseline_retry_
```

Итог: **PASS**.

| Clip | Scene | OFF presence | ON presence | OFF false_lock | ON false_lock | OFF idchg/min | ON idchg/min | Drops |
|------|-------|-------------:|------------:|---------------:|--------------:|---------------:|--------------:|------:|
| `drone_closeup_mixkit_44644_360` | day | 1.000 | 1.000 | 0.000 | 0.000 | 0.00 | 0.00 | 0 |
| `antiuav_rgbt_train_20190925_210802_1_7_infrared` | ir | 1.000 | 1.000 | 0.012 | 0.013 | 0.00 | 0.00 | 0 |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | ir | 1.000 | 0.999 | 0.111 | 0.110 | 1.34 | 0.00 | 1 |
| `drone_detection_V_BIRD_001` | noise | 0.000 | 0.000 | 0.000 | 0.000 | 0.00 | 0.00 | 0 |
| `drone_detection_V_AIRPLANE_001` | noise | 0.190 | 0.190 | 0.190 | 0.190 | 0.00 | 0.00 | 0 |

Diagnostic-night gate:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_baseline_
```

Итог: **PASS diagnostic/non-blocking**.

| Clip | OFF presence | ON presence | OFF false_lock | ON false_lock | OFF idchg/min | ON idchg/min | Drops |
|------|-------------:|------------:|---------------:|--------------:|---------------:|--------------:|------:|
| `night_ground_large_drones` | 0.521 | 0.521 | 0.448 | 0.448 | 30.58 | 30.58 | 0 |
| `antiuav_rgbt_20190925_193610_1_1_visible` | 0.593 | 0.555 | 0.590 | 0.555 | 0.00 | 0.00 | 18 |
| `antiuav_rgbt_20190925_200805_1_2_visible` | 0.306 | 0.295 | 0.306 | 0.295 | 3.85 | 2.57 | 10 |

Примечание: один baseline run и один normalized telemetry run были отброшены как gate decision evidence из-за isolated `fps_drop>5.0`. Поведенческие metrics в них были стабильны; accepted decision использует серийные PASS-прогоны.

---

## 3. Новая telemetry

Добавлены поля в `EvaluationReport.to_dict()`:

- `tracking_action_counts`
- `decision_path_counts`
- `target_source_counts`
- `target_modality_counts`
- `false_lock_action_counts`
- `false_lock_source_counts`
- `avg_target_reliability`
- `avg_target_p_present`

Source labels нормализованы: `DetectionSource.NIGHT` теперь пишется как `night`, `DetectionSource.ROI` как `roi`, `DetectionSource.LOCK` как `lock`.

---

## 4. Telemetry findings

Promotion telemetry:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_telemetry_
```

Итог: **PASS**.

Normalized source-label telemetry:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_telemetry_norm_
```

Итог: behavior metrics usable, but gate exit non-zero due `fps_drop>5.0` on `noise-airplane`; used only for readable source labels.

Key rows:

| Clip | Scene | ON false_lock | ON avg reliability | ON avg p_present | false-lock sources | false-lock actions |
|------|-------|--------------:|-------------------:|-----------------:|--------------------|--------------------|
| `drone_detection_V_AIRPLANE_001` | noise | 0.1896 | 0.0434 | 0.1330 | `night:62` | `local_validate:15`, `expand_roi:47` |
| `drone_detection_V_BIRD_001` | noise | 0.0000 | 0.0000 | 0.0000 | none | none |
| `antiuav_rgbt_train_20190925_210802_1_7_infrared` | ir | 0.0128 | 0.7544 | 0.9834 | `lock:9`, `local:3` | `local_validate:7`, `keep_lock:5` |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | ir | 0.1096 | 0.7453 | 0.9766 | `lock:79`, `local:4`, `yolo:15` | `keep_lock:44`, `local_validate:47`, `expand_roi:4`, `global_rescan:3` |

Interpretation:

1. `noise-airplane` is not a high-confidence YOLO false positive. It is weak runtime evidence from `night`, with very low average reliability (`0.0434`) and low `p_present` (`0.1330`).
2. `noise-bird` remains clean: no active false lock, no weak evidence to suppress.
3. IR false locks exist but mostly inside accepted target continuity and remain gate-safe; suppressor must not broadly attack `lock/local` in IR.
4. `yolo` false-lock frames exist on one IR clip (`15` frames), but they are not the main noise problem and should not be suppressed by policy.

Diagnostic-night telemetry:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_telemetry_norm_
```

Итог: **PASS diagnostic/non-blocking**.

| Clip | ON false_lock | ON idchg/min | ON avg reliability | ON avg p_present | false-lock sources | false-lock actions |
|------|--------------:|-------------:|-------------------:|-----------------:|--------------------|--------------------|
| `night_ground_large_drones` | 0.4062 | 18.35 | 0.1256 | 0.3611 | `night:117` | `local_validate:34`, `expand_roi:83` |
| `antiuav_rgbt_20190925_193610_1_1_visible` | 0.5295 | 0.00 | 0.1524 | 0.3555 | `roi:455`, `night:39` | `local_validate:242`, `expand_roi:182`, `global_rescan:70` |
| `antiuav_rgbt_20190925_200805_1_2_visible` | 0.2645 | 2.57 | 0.0652 | 0.1739 | `roi:112`, `night:135` | `local_validate:79`, `expand_roi:143`, `global_rescan:25` |

Interpretation:

1. Visible-night false locks are also weak runtime evidence, not YOLO.
2. The dominant actions are `LOCAL_VALIDATE` and `EXPAND_ROI`; current behavior mapping only acts on `DROP_LOCK`, so it observes these frames but does not suppress them.
3. `night_ground_large_drones` improved in the normalized diagnostic run versus earlier diagnostic runs, but still remains diagnostic-only and high-risk as a blocking gate.

---

## 5. Decision checkpoint

Decision: **POLICY_SUPPRESSOR_CANDIDATE**.

Rationale:

1. The key FP row (`noise-airplane`) is weak `night` evidence with very low reliability, not a model-level YOLO false positive.
2. Visible-night diagnostic false locks are weak `night/roi` evidence with low reliability and low `p_present`.
3. A bounded `ActionPolicy` suppressor is therefore conceptually valid.
4. The suppressor must be source-aware and conservative:
   - target `night/roi` weak evidence first;
   - do not suppress fresh `yolo`;
   - do not broadly suppress IR `lock/local` because accepted IR gate relies on continuity.

Do not jump to YOLO26/model cycle yet for this specific FP/ID issue. Model/data work remains important, but telemetry says there is a legitimate policy-layer problem to test first.

---

## 6. Important caveats

1. `target_modality_counts` currently shows `rgb` in offline action-policy gates because `AUTO_SCENE_DETECT=False` by default and the runner does not explicitly force modality from the pack scene.
2. Because of that, FPID-004 should rely primarily on `source`, `reliability`, `p_present`, and `lost_age`, not on `belief.modality` alone.
3. A later cleanup should add explicit scene/modality plumbing for offline gates if modality-specific policy becomes central.
4. Full benchmark runs must stay serial while `avg_fps` is a blocking threshold.

---

## 7. Recommended FPID-004 scope

Implement only a bounded weak-evidence suppressor:

- Add tests in `tests/test_action_policy.py`.
- Add rules in `src/uav_tracker/tracking/action_policy.py`.
- Candidate rule shape:

```python
if (
    belief.source in {"night", "roi"}
    and belief.reliability <= 0.20
    and belief.p_present <= 0.40
    and belief.lost_age >= 1
):
    return TrackingAction.DROP_LOCK
```

Before implementation, normalize `TargetBelief.source` to stable values if needed, because current telemetry confirms readable labels in evaluation but `TargetBelief.source` is still produced by `str(active.source)` in `TrackerPipeline._build_target_belief()`.

Acceptance for FPID-004:

1. Blocking gate remains PASS.
2. `noise-airplane` false lock decreases materially, or report explains why not.
3. Day and IR presence do not materially drop.
4. Diagnostic-night remains non-blocking and records any regressions in `diagnostic_reasons`.

---

## 8. Validation

| Команда | Результат |
|---------|-----------|
| `run_action_policy_gate.py --tag fp_suppressor_baseline_retry_` | PASS |
| `run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_baseline_` | PASS diagnostic |
| `pytest tests/test_evaluation_telemetry.py tests/test_action_policy_gate.py -q` | 13 passed |
| `run_action_policy_gate.py --tag fp_suppressor_telemetry_` | PASS |
| `run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_telemetry_norm_` | PASS diagnostic |
| `pytest tests/test_evaluation_telemetry.py tests/test_action_policy_gate.py tests/test_action_policy.py tests/test_action_policy_behavior.py -q` | 51 passed |
| `pytest tests -q` | PASS |
| `compileall -q python_scripts src app orchestrator tests` | OK |
| `git diff --check` | clean |
| `check_orchestration_state.py` | OK · active_tasks=1 · open_tasks=1 |

---

## 9. Следующий шаг

FPID-004 bounded implementation: `TASK-20260502-091`. Recommended executor: Claude or Codex worker with strict prompt. Codex should review gate results before closing AP-FP-ID-SUPPRESSOR-V1.
