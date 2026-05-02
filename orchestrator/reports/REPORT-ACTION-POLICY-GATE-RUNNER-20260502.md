# REPORT-ACTION-POLICY-GATE-RUNNER-20260502

**Задача:** AP-ACTION-POLICY-PROMOTION — reproducible ActionPolicy OFF/ON gate runner
**Дата:** 2026-05-02
**Статус:** PASS · runner добавлен в repo · full gate воспроизводим без `/tmp` harness

---

## 1. Что изменено

| Файл | Тип | Описание |
|------|-----|----------|
| `python_scripts/run_action_policy_gate.py` | NEW | CLI runner для сравнения `ACTION_POLICY_BEHAVIOR_ENABLED=False` vs `True` на одном pack. Пишет per-clip OFF/ON JSON, summary JSON/CSV и возвращает non-zero при gate failure. |
| `configs/action_policy_gate_pack.csv` | NEW | Канонический pack для ActionPolicy promotion: day TP + accepted IR TP + noise controls. Visible-night не включён как blocking gate. |
| `src/uav_tracker/evaluation.py` | EDIT | `EvaluationReport` теперь включает `behavior_drop_count`, агрегированный из `FrameOutput`. |
| `tests/test_action_policy_gate.py` | NEW | 8 unit-тестов helper-логики runner-а без тяжёлого inference. |
| `orchestrator/state/completed_tasks.md` | EDIT | Запись о завершении runner-задачи. |

Изменений в `ActionPolicy.decide`, thresholds, preset-ах, baseline, GUI и training нет.

---

## 2. Поведение runner-а

Runner читает CSV `source,scene` и выбирает preset по scene:

| Scene | Preset |
|-------|--------|
| `day` | `default` |
| `ir` | `antiuav_thermal` |
| `night` | `night` |
| `noise` / `background` | `default` |

Для каждого клипа runner запускает один и тот же `evaluate_source` дважды:

1. OFF: `cfg.ACTION_POLICY_BEHAVIOR_ENABLED=False`
2. ON: `cfg.ACTION_POLICY_BEHAVIOR_ENABLED=True`

Сравниваемые метрики:

- `active_presence_rate`
- `false_lock_rate`
- `active_id_changes_per_min`
- `avg_gt_iou`
- `hits_iou_01`
- `avg_fps`
- `behavior_drop_count`

Gate thresholds по умолчанию:

| Threshold | Значение |
|-----------|---------:|
| `max_presence_drop` | 0.01 |
| `max_false_lock_increase` | 0.01 |
| `max_noise_presence_increase` | 0.01 |
| `max_noise_false_lock_increase` | 0.01 |
| `max_iou_drop` | 0.02 |
| `max_hit01_drop` | 2 |
| `max_fps_drop` | 5.0 |
| `max_drop_rate` | 0.02 |

Дополнительный sanity check: OFF должен иметь `behavior_drop_count=0`.

---

## 3. Full gate result

Команда:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag full_20260502_
```

Артефакты:

- `runs/evaluations/action_policy_gate/full_20260502_action_policy_gate.json`
- `runs/evaluations/action_policy_gate/full_20260502_action_policy_gate.csv`

Итог: **PASS**.

| Clip | Scene | OFF presence | ON presence | OFF false_lock | ON false_lock | OFF idchg/min | ON idchg/min | OFF IoU | ON IoU | ON drops |
|------|-------|-------------:|------------:|---------------:|--------------:|---------------:|--------------:|--------:|-------:|---------:|
| `drone_closeup_mixkit_44644_360` | day | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.9392 | 0.9284 | 0 |
| `antiuav_rgbt_train_20190925_210802_1_7_infrared` | ir | 1.0000 | 1.0000 | 0.0118 | 0.0128 | 0.0000 | 0.0000 | 0.7646 | 0.7600 | 0 |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | ir | 1.0000 | 0.9989 | 0.1107 | 0.1096 | 1.3423 | 0.0000 | 0.6929 | 0.6929 | 1 |
| `drone_detection_V_BIRD_001` | noise | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 |
| `drone_detection_V_AIRPLANE_001` | noise | 0.1896 | 0.1896 | 0.1896 | 0.1896 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 |

Mean deltas:

| Metric | ON - OFF |
|--------|---------:|
| `delta_presence` | -0.0002 |
| `delta_false_lock` | -0.0000 |
| `delta_idchg_pm` | -0.2685 |
| `delta_avg_gt_iou` | -0.0031 |
| `delta_avg_fps` | +0.9380 |
| `on_behavior_drop_rate` | 0.0002 |

---

## 4. Решение

**PASS.**

Обоснование:

1. OFF sanity сохранён: `behavior_drop_count=0` во всех OFF прогонах.
2. ON не ухудшает day TP: presence/false_lock/hit01 идентичны.
3. ON не ухудшает IR materially: один IR клип имеет +0.001 false_lock и -1 hit01, второй улучшает false_lock и idchg/min.
4. Noise controls идентичны OFF/ON.
5. `noise-airplane` FP=0.1896 сохраняется, но не усиливается. Это отдельная задача FP-suppressor, не regression runner-а.
6. Runner теперь находится в repo и может использоваться перед любым изменением `ActionPolicy.decide`.

---

## 5. Почему visible-night не блокировал gate

Visible-night остаётся diagnostic-only согласно IR-first решению:

- ночной accepted gate закрывается IR/thermal клипами;
- RGB visible-night не обязан проходить как GT-positive, потому что в полной темноте основная сенсорная ставка — IR;
- `configs/action_policy_gate_pack.csv` намеренно не содержит `night_ground_large_drones`.

Для будущей modality-aware policy RGB-night можно проверять отдельно, но не как blocker promotion gate.

---

## 6. Validation

| Команда | Результат |
|---------|-----------|
| `pytest tests/test_action_policy_gate.py -q` | 8 passed |
| `py_compile python_scripts/run_action_policy_gate.py src/uav_tracker/evaluation.py` | OK |
| `run_action_policy_gate.py --max-frames 5 --tag smoke_` | PASS |
| `run_action_policy_gate.py --tag full_20260502_` | PASS |

Полная проверка проекта выполняется Codex после записи отчёта.

---

## 7. Риски

1. Runner теперь воспроизводим, но ещё не подключён в CI.
2. `ActionPolicy.decide` пока не modality-aware. Следующая задача должна менять policy только после запуска этого runner-а.
3. `noise-airplane` FP=0.1896 не лечится текущим drop guard. Для этого нужен отдельный FP-suppressor или modality/source-aware rule.
4. Gate thresholds conservative и могут потребовать закрепления в отдельном contract-файле, если runner станет обязательной pre-merge проверкой.

---

## 8. Следующий шаг

Следующая bounded задача: сделать `ActionPolicy.decide` modality-aware, но обязательно:

1. сначала запустить `python_scripts/run_action_policy_gate.py` как baseline;
2. изменить только policy thresholds/logic;
3. снова запустить runner;
4. принять изменение только если full gate остаётся PASS.

