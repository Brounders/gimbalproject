# REPORT: Baseline Formalization

Date: 2026-03-13
Status: Done
Type: Governance. No runtime code changes.

---

## Проблема

`models/baseline.pt` отсутствовал с начала проекта.
Runtime использовал implicit fallback в `resolve_model_path()` на `drone_bird_probe_fast`.
Все gate-прогоны AP-018..026 сравнивались против неформального reference без sha256 и manifest.

---

## Действия

### 1. IR gate на de-facto baseline (первый раз)

```
PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quality_gate.py \
  --pack-file configs/regression_pack_ir.csv --preset antiuav_thermal \
  --tag baseline_formalization_ir
```

| Clip | scene | false_lock | id_chg/min | Gate |
|------|-------|-----------|------------|------|
| Demo_IR_DRONE_146 | ir | 0.840 | 63.26 | FAIL |
| IR_DRONE_001 | ir | 0.784 | 5.98 | FAIL |
| IR_BIRD_001 | noise | **0.090** | 0.00 | **PASS** |

IR gate FAIL — зафиксировано как known open issue. Установка baseline не означает
принятия IR gate — это фиксация reference point для будущих кандидатов.

### 2. Установка formal baseline

```
PYTHONPATH=src ./tracker_env/bin/python python_scripts/install_baseline.py \
  --source runs/detect/runs/drone_bird_probe_fast/weights/best.pt \
  --notes "..." \
  --preset-gates "night=...,ir=..."
```

| Артефакт | Результат |
|----------|-----------|
| `models/baseline.pt` | ✅ создан (5.2MB) |
| `models/baseline_manifest.json` | ✅ создан |
| SHA256 | `bedc77fe7b899de1ac68ae654f49fcee6301a9d3f8a61e9eff5c1e8d66641d44` |

### 3. Gate reference для baseline

| Контекст | Результат | Отчёт |
|----------|-----------|-------|
| Night | **PASS** (AP-025) | `runs/evaluations/quality_gate/quality_gate_night.json` |
| IR | FAIL (known) | `runs/evaluations/quality_gate/baseline_formalization_irquality_gate_antiuav_thermal.json` |
| Day | FPS-only (no GT) | не привязывается к baseline |

---

## Accepted baseline KPIs

| Контекст | Clip | false_lock | id_chg/min |
|----------|------|-----------|------------|
| Night | night_ground_large_drones | **0.510** | **12.23** |
| Night | night_ground_indicator_lights | **0.096** | 0.00 |
| IR | Demo_IR_DRONE_146 | 0.840 (open) | 63.26 (open) |
| IR | IR_DRONE_001 | 0.784 (open) | 5.98 |
| IR | IR_BIRD_001 | **0.090** | 0.00 |

---

## Следствие

Следующий training cycle теперь имеет формальную точку отсчёта:
- sha256 зафиксирован → integrity verification возможна
- gate reports привязаны → сравнение будет честным
- `automation/state/decision_log.json` обновлён — запись `install_as_baseline`
