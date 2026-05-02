# REPORT-ACTION-POLICY-MODALITY-AWARE-20260502

**Задача:** AP-ACTION-POLICY-PROMOTION — modality-aware `ActionPolicy.decide`
**Дата:** 2026-05-02
**Статус:** PASS · RGB-night стал строже · IR/day/noise gate сохранён

---

## 1. Что изменено

| Файл | Тип | Описание |
|------|-----|----------|
| `src/uav_tracker/tracking/action_policy.py` | EDIT | Добавлены modality-aware thresholds для `belief.modality == 'night'`: более высокий keep threshold и более ранний stale drop. IR/day используют baseline thresholds. |
| `tests/test_action_policy.py` | EDIT | +3 TDD-теста: RGB-night marginal reliability не `KEEP_LOCK`; IR на той же reliability всё ещё `KEEP_LOCK`; RGB-night stale lock раньше даёт `DROP_LOCK`. |
| `orchestrator/reports/REPORT-ACTION-POLICY-MODALITY-AWARE-20260502.md` | NEW | Этот отчёт. |
| `orchestrator/state/completed_tasks.md` | EDIT | Запись о завершении modality-aware задачи. |

Не изменял:

- `ACTION_POLICY_BEHAVIOR_ENABLED` — остаётся default `False`;
- `TrackingAction` enum;
- pipeline wiring;
- presets, thresholds runtime config, baseline model;
- visible-night pack status: diagnostic-only.

---

## 2. Новая policy-семантика

Baseline thresholds остались прежними для `rgb` и `ir`.

Новые поля в `ActionPolicy`:

| Field | Value | Meaning |
|-------|------:|---------|
| `night_keep_reliability_min` | 0.70 | RGB-night должен иметь более сильную reliability, чтобы получить `KEEP_LOCK`. |
| `night_drop_reliability_max` | 0.15 | RGB-night stale target дропается при чуть менее жёстком reliability cutoff. |
| `night_drop_lost_age_min` | 10 | RGB-night stale target дропается раньше, чем generic RGB. |

Логика:

```python
if belief.modality == 'night':
    keep_reliability_min = 0.70
    drop_reliability_max = 0.15
    drop_lost_age_min = 10
else:
    keep_reliability_min = 0.60
    drop_reliability_max = 0.10
    drop_lost_age_min = 12
```

IR не наследует RGB-night strictness, потому что IR/thermal является accepted night gate.

---

## 3. TDD evidence

RED:

```bash
PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_action_policy.py -q
```

Ожидаемо упали 2 новых теста:

- `test_night_modality_requires_stronger_reliability_to_keep_lock`
- `test_night_modality_drops_stale_lock_earlier`

GREEN:

После минимального изменения `ActionPolicy`:

```bash
PYTHONPATH=src tracker_env/bin/python -m pytest tests/test_action_policy.py -q
```

Результат: PASS.

---

## 4. Gate evidence

Baseline перед изменением:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag pre_modality_
```

Результат:

- `runs/evaluations/action_policy_gate/pre_modality_action_policy_gate.json`
- `gate_passed=True`

После изменения:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag post_modality_
```

Результат:

- `runs/evaluations/action_policy_gate/post_modality_action_policy_gate.json`
- `gate_passed=True`

Сводка post-change:

| Clip | Scene | Δ presence | Δ false_lock | Δ idchg/min | Δ avg IoU | ON drops |
|------|-------|-----------:|-------------:|------------:|----------:|---------:|
| `drone_closeup_mixkit_44644_360` | day | 0.0000 | 0.0000 | 0.0000 | -0.0100 | 0 |
| `antiuav_rgbt_train_20190925_210802_1_7_infrared` | ir | 0.0000 | +0.0010 | 0.0000 | -0.0007 | 0 |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | ir | -0.0011 | -0.0011 | -1.3423 | 0.0000 | 1 |
| `drone_detection_V_BIRD_001` | noise | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 |
| `drone_detection_V_AIRPLANE_001` | noise | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 |

Mean:

| Metric | ON - OFF |
|--------|---------:|
| `delta_presence` | -0.0002 |
| `delta_false_lock` | -0.0000 |
| `delta_idchg_pm` | -0.2685 |
| `delta_avg_gt_iou` | -0.0021 |
| `delta_avg_fps` | -0.5928 |
| `on_behavior_drop_rate` | 0.0002 |

---

## 5. Решение

**PASS.**

Обоснование:

1. `ActionPolicy.decide` теперь действительно использует `TargetBelief.modality`.
2. RGB-night стал строже, но accepted gate pack day/IR/noise остался PASS.
3. IR не ухудшен materially: `ir-train-1_7` имеет +1 false-lock frame из 934; `ir-train-1_2` улучшает false_lock/idchg.
4. Noise не ухудшен: bird и airplane идентичны OFF/ON.
5. Behavior flag остаётся default OFF; изменение безопасно как telemetry и как candidate ON-path.

---

## 6. Почему visible-night всё ещё diagnostic-only

Эта задача не превращает visible-night в blocking gate. Она только меняет поведение policy, если pipeline уже пометил evidence как `modality='night'`.

Причина прежняя:

- в полной темноте primary night sensor = IR/thermal;
- RGB-night может быть полезным сигналом по огням/силуэту, но не должен удерживать marginal lock так же легко, как day RGB или IR;
- accepted promotion gate остаётся day + IR + noise.

---

## 7. Риски

1. В текущем `configs/action_policy_gate_pack.csv` нет blocking visible-night клипа, поэтому прямой измеримый выигрыш RGB-night пока не доказан.
2. `night_keep_reliability_min=0.70` и ранний drop (`0.15`, `10`) выбраны консервативно. Если будущий RGB-night diagnostic pack покажет чрезмерные drops, thresholds нужно будет ретюнить.
3. `noise-airplane` FP=0.190 не лечится этой задачей, потому что он проходит как `modality='rgb'` noise, а не RGB-night. Для него нужен отдельный FP-suppressor.

---

## 8. Следующий шаг

Следующий bounded шаг: добавить диагностический `night` row в отдельный non-blocking runner mode или отдельный `action_policy_diagnostic_pack.csv`, чтобы видеть effect RGB-night strictness без блокировки promotion gate.

