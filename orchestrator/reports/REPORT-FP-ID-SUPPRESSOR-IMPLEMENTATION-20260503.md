# REPORT-FP-ID-SUPPRESSOR-IMPLEMENTATION-20260503

**Задача:** TASK-20260502-091 / FPID-004 — weak-evidence suppressor implementation  
**Дата:** 2026-05-03  
**Статус:** PASS · blocking gate сохранён · `noise-airplane` false lock снижен

---

## 1. Что изменено

| Файл | Тип | Описание |
|------|-----|----------|
| `src/uav_tracker/tracking/evidence.py` | EDIT | Добавлен `normalize_source()`; `TargetBelief.source` теперь стабилизируется до `yolo/local/roi/lock/night/-`. |
| `src/uav_tracker/pipeline.py` | EDIT | `_build_target_belief()` использует нормализованный `active_source` для `SOURCE_RELIABILITY` и `TargetBelief.source`. |
| `src/uav_tracker/tracking/action_policy.py` | EDIT | Добавлено узкое правило `DROP_LOCK` для weak runtime evidence источников `night/roi`. |
| `tests/test_tracking_evidence.py` | EDIT | Тесты нормализации `DetectionSource.*` и string-valued enum. |
| `tests/test_action_policy.py` | EDIT | Тесты suppressor-а: `night/roi` drop; `yolo/lock/local` не подавляются этим правилом. |

Не изменял:

- baseline model;
- runtime presets / thresholds;
- `TargetManager`;
- `TemplateLockTracker`;
- GUI;
- `ACTION_POLICY_BEHAVIOR_ENABLED` default;
- gate thresholds.

---

## 2. Реализованное правило

В `ActionPolicy` добавлены параметры:

```python
weak_runtime_sources = frozenset({'night', 'roi'})
weak_runtime_drop_reliability_max = 0.20
weak_runtime_drop_p_present_max = 0.40
weak_runtime_drop_lost_age_min = 1
```

Правило:

```python
if (
    belief.source in self.weak_runtime_sources
    and belief.reliability <= self.weak_runtime_drop_reliability_max
    and belief.p_present <= self.weak_runtime_drop_p_present_max
    and belief.lost_age >= self.weak_runtime_drop_lost_age_min
):
    return TrackingAction.DROP_LOCK
```

Ограничение намеренное:

- `yolo` не подавляется;
- `lock/local` не подавляются широким правилом, чтобы не ударить по IR continuity;
- `modality` не используется как основной сигнал, потому что offline gate сейчас показывает `target_modality='rgb'`.

---

## 3. Blocking gate

Команда:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag fp_suppressor_candidate_
```

Итог: **PASS**.

| Clip | Scene | OFF presence | ON presence | Δ presence | OFF false_lock | ON false_lock | Δ false_lock | OFF idchg/min | ON idchg/min | Drops |
|------|-------|-------------:|------------:|-----------:|---------------:|--------------:|-------------:|---------------:|--------------:|------:|
| `drone_closeup_mixkit_44644_360` | day | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 0.00 | 0 |
| `antiuav_rgbt_train_20190925_210802_1_7_infrared` | ir | 1.0000 | 1.0000 | 0.0000 | 0.0118 | 0.0128 | +0.0010 | 0.00 | 0.00 | 0 |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | ir | 1.0000 | 0.9989 | -0.0011 | 0.1107 | 0.1096 | -0.0011 | 1.34 | 0.00 | 1 |
| `drone_detection_V_BIRD_001` | noise | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 0.00 | 0 |
| `drone_detection_V_AIRPLANE_001` | noise | 0.1896 | 0.1713 | -0.0183 | 0.1896 | 0.1713 | -0.0183 | 0.00 | 0.00 | 6 |

Решение по blocking gate:

- day не изменился;
- IR не просел materially;
- `noise-airplane` false lock снизился на 6 кадров из 327;
- `behavior_drop_rate` на `noise-airplane` = 0.0183, ниже blocking threshold 0.02;
- gate PASS.

---

## 4. Diagnostic-night gate

Команда:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag fp_suppressor_diag_candidate_
```

Итог: **PASS diagnostic/non-blocking**.

| Clip | OFF presence | ON presence | Δ presence | OFF false_lock | ON false_lock | Δ false_lock | OFF idchg/min | ON idchg/min | Drops | Diagnostic reasons |
|------|-------------:|------------:|-----------:|---------------:|--------------:|-------------:|---------------:|--------------:|------:|--------------------|
| `night_ground_large_drones` | 0.5208 | 0.4792 | -0.0416 | 0.4479 | 0.4306 | -0.0173 | 30.58 | 0.00 | 12 | `drop_rate>0.02;presence_drop>0.01;hit01_drop>2` |
| `antiuav_rgbt_20190925_193610_1_1_visible` | 0.8950 | 0.4309 | -0.4641 | 0.8950 | 0.4309 | -0.4641 | 0.00 | 0.00 | 127 | `drop_rate>0.02;fps_drop>5.0;presence_drop>0.01` |
| `antiuav_rgbt_20190925_200805_1_2_visible` | 0.2923 | 0.2270 | -0.0653 | 0.2923 | 0.2270 | -0.0653 | 3.85 | 0.00 | 49 | `drop_rate>0.02;presence_drop>0.01` |

Interpretation:

- visible-night false locks and ID churn are reduced;
- the suppressor is too aggressive for treating visible-night as a positive gate;
- this is acceptable only because visible-night remains diagnostic-only under the IR-first decision.

---

## 5. Тесты

Добавлены/обновлены tests:

- `test_normalize_source_accepts_enum_style_strings`
- `test_normalize_source_uses_string_enum_value`
- `test_weak_night_runtime_evidence_drops_early`
- `test_weak_roi_runtime_evidence_drops_early`
- `test_weak_yolo_evidence_is_not_suppressed_by_runtime_rule`
- `test_weak_lock_and_local_are_not_suppressed_by_runtime_rule`

Targeted result:

```bash
PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_tracking_evidence.py tests/test_action_policy.py -q
```

Result: PASS.

---

## 6. Решение

**PASS for blocking gate.**

Обоснование:

1. Главная blocking FP-точка (`noise-airplane`) улучшена без ухудшения day/IR.
2. Правило не подавляет `yolo`, `lock`, `local` broad-path.
3. `ACTION_POLICY_BEHAVIOR_ENABLED` остаётся default OFF.
4. Diagnostic-night показывает ожидаемую tradeoff-картину: false_lock/idchg ниже, но presence ниже и drops выше.

---

## 7. Риски

1. Rule threshold находится близко к blocking `max_drop_rate=0.02` на `noise-airplane`: ON drop rate = 0.0183.
2. Diagnostic-night сильно режется; это нельзя превращать в visible-night positive gate без отдельной настройки.
3. Offline `target_modality` всё ещё не является надёжным gate-сигналом; suppressor сознательно не зависит от modality.
4. 60-frame smoke gate оказался шумным и не использовался как acceptance evidence.

---

## 8. Следующий шаг

Codex review/acceptance:

1. подтвердить validation;
2. закрыть `TASK-20260502-091`;
3. закрыть или продолжить `AP-FP-ID-SUPPRESSOR-V1` отдельным решением.
