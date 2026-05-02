# REPORT-ACTION-POLICY-DIAGNOSTIC-NIGHT-20260502

**Задача:** AP-ACTION-POLICY-PROMOTION — visible-night diagnostic gate
**Дата:** 2026-05-02
**Статус:** PASS · visible-night измеряется отдельно · promotion gate остаётся day/IR/noise

---

## 1. Что изменено

| Файл | Тип | Описание |
|------|-----|----------|
| `python_scripts/run_action_policy_gate.py` | EDIT | Добавлены `--diagnostic` и `--diagnostic-scenes`. Diagnostic rows сохраняют failures в `diagnostic_reasons`, но не блокируют exit status/gate. |
| `configs/action_policy_diagnostic_pack.csv` | NEW | Отдельный visible-night pack из 3 клипов: `night_ground_large_drones`, два Anti-UAV visible-night клипа. |
| `tests/test_action_policy_gate.py` | EDIT | +3 unit-теста: scene-set parsing, blocking row decision, non-blocking diagnostic row decision. |
| `orchestrator/state/completed_tasks.md` | EDIT | Запись о завершении diagnostic-night задачи. |

Не изменял:

- `ActionPolicy.decide`;
- `ACTION_POLICY_BEHAVIOR_ENABLED` default;
- `configs/action_policy_gate_pack.csv`;
- runtime presets, model, pipeline behavior.

---

## 2. Diagnostic semantics

Runner теперь разделяет два типа строк:

| Type | `passed` | `fail_reasons` | `diagnostic_reasons` | Влияет на `gate_passed` |
|------|----------|----------------|----------------------|--------------------------|
| Blocking row | `False`, если есть failures | failures | пусто | Да |
| Diagnostic row | всегда `True` | пусто | failures | Нет |

Diagnostic row можно включить двумя способами:

```bash
--diagnostic
--diagnostic-scenes night
```

Для текущего решения используется `--diagnostic-scenes night`, чтобы только visible-night был diagnostic-only, а основной promotion pack оставался строгим.

---

## 3. Visible-night diagnostic result

Команда:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag diagnostic_night_
```

Артефакты:

- `runs/evaluations/action_policy_gate/diagnostic_night_action_policy_gate.json`
- `runs/evaluations/action_policy_gate/diagnostic_night_action_policy_gate.csv`

Итог: **PASS as diagnostic**.

| Clip | OFF presence | ON presence | OFF false_lock | ON false_lock | OFF idchg/min | ON idchg/min | ON drops | Diagnostic reasons |
|------|-------------:|------------:|---------------:|--------------:|---------------:|--------------:|---------:|--------------------|
| `night_ground_large_drones` | 0.5208 | 0.5208 | 0.4479 | 0.4479 | 30.5823 | 30.5823 | 0 | |
| `antiuav_rgbt_20190925_193610_1_1_visible` | 0.5295 | 0.5091 | 0.5295 | 0.5091 | 0.0000 | 0.0000 | 19 | `drop_rate>0.02;presence_drop>0.01` |
| `antiuav_rgbt_20190925_200805_1_2_visible` | 0.2773 | 0.2827 | 0.2773 | 0.2827 | 3.8544 | 2.5696 | 9 | |

Вывод:

1. Visible-night остаётся нестабильным как самостоятельный blocking gate.
2. RGB-night strictness не даёт убедимого улучшения на `night_ground_large_drones`: id churn остаётся высоким.
3. На Anti-UAV visible-night клипах baseline detector фактически даёт false-positive lock (`false_lock == presence`), поэтому эти клипы полезны как diagnostic noise/weak-signal evidence, но не как promotion acceptance.

---

## 4. Promotion gate unaffected

Команда:

```bash
PYTHONPATH=src tracker_env/bin/python python_scripts/run_action_policy_gate.py --tag promotion_after_diagnostic_serial_
```

Артефакты:

- `runs/evaluations/action_policy_gate/promotion_after_diagnostic_serial_action_policy_gate.json`
- `runs/evaluations/action_policy_gate/promotion_after_diagnostic_serial_action_policy_gate.csv`

Итог: **PASS**.

| Clip | Scene | Δ presence | Δ false_lock | Δ avg IoU | Δ hit01 | ON drops |
|------|-------|-----------:|-------------:|----------:|--------:|---------:|
| `drone_closeup_mixkit_44644_360` | day | 0.0000 | 0.0000 | -0.0074 | 0 | 0 |
| `antiuav_rgbt_train_20190925_210802_1_7_infrared` | ir | 0.0000 | +0.0010 | -0.0046 | -1 | 0 |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | ir | -0.0011 | -0.0011 | +0.0005 | 0 | 1 |
| `drone_detection_V_BIRD_001` | noise | 0.0000 | 0.0000 | 0.0000 | 0 | 0 |
| `drone_detection_V_AIRPLANE_001` | noise | 0.0000 | 0.0000 | 0.0000 | 0 | 0 |

Примечание: один параллельный прогон promotion gate был отброшен как невалидный, потому что одновременно шёл full diagnostic benchmark и `fps_drop` загрязнился конкурирующей нагрузкой. Серийный повтор прошёл PASS.

---

## 5. Решение

**PASS.**

Обоснование:

1. Visible-night теперь регулярно измеряется, но не блокирует IR-first release decision.
2. Основной `configs/action_policy_gate_pack.csv` не изменён и остаётся blocking promotion pack.
3. Diagnostic failures сохраняются в JSON/CSV, поэтому слабые visible-night места не теряются.
4. ActionPolicy behavior path не менялся; задача добавила только runner/pack/test/report слой.

---

## 6. Validation

| Команда | Результат |
|---------|-----------|
| `pytest tests/test_action_policy_gate.py -q` | 11 passed |
| `run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --max-frames 5 --tag diagnostic_smoke_` | PASS |
| `run_action_policy_gate.py --pack-file configs/action_policy_diagnostic_pack.csv --diagnostic-scenes night --tag diagnostic_night_` | PASS diagnostic |
| `run_action_policy_gate.py --tag promotion_after_diagnostic_serial_` | PASS |

Полная проверка проекта выполняется Codex после записи отчёта.

---

## 7. Риски

1. Diagnostic visible-night pack не доказывает готовность RGB-night tracking. Он только сохраняет наблюдаемость.
2. `night_ground_large_drones` имеет высокий id churn, значит будущий FP/ID-suppressor всё равно нужен.
3. Anti-UAV visible-night клипы в текущем baseline больше похожи на false-positive stress test, чем на reliable TP gate.
4. Full benchmark нельзя запускать параллельно с другим full benchmark, если `avg_fps` остаётся blocking threshold.

---

## 8. Следующий шаг

Следующий bounded шаг: FP/ID suppressor для weak/noise evidence, начиная с `noise-airplane` и visible-night false locks. Перед изменением обязательно запускать `run_action_policy_gate.py` как baseline, после изменения — promotion gate + diagnostic night pack.
