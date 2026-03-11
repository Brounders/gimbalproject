# Operator Baseline — 2026-03-11

> Зафиксированная опорная точка для сравнения будущих изменений.
> Данные получены из: `orchestrator/state/operator_smoke_20260311.md`

---

## Canonical Operator Modes

| Кнопка | Пресет | Night override | Auto scene |
|--------|--------|----------------|------------|
| **Авто** | `default` | preset default | ✅ Day/Night/IR heuristic |
| **День** | `default` | `False` (off) | ❌ |
| **Ночь** | `night` | preset default | ❌ |
| **IR** | `antiuav_thermal` | preset default | ❌ |

Источник: `app/main_gui.py → CANONICAL_OPERATOR_MODES`

---

## Preset → Config mapping

| Пресет | Файл | conf_thresh | imgsz | night_enabled |
|--------|------|-------------|-------|---------------|
| `default` | `configs/default.yaml` | 0.30 | 640 | True |
| `night` | `configs/night.yaml` | 0.12 | 960 | True |
| `antiuav_thermal` | `configs/antiuav_thermal.yaml` | 0.12 | 960 | True |
| `small_target` | `configs/small_target.yaml` | 0.15 | 960 | True |

---

## Smoke Snapshot (2026-03-11)

**Команда:**
```
PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py \
  --sources test_videos/drone_closeup_mixkit_44644_360.mp4,\
test_videos/night_ground_large_drones.mp4,\
test_videos/Demo_IR_DRONE_146.mp4,\
test_videos/IR_BIRD_001.mp4 \
  --max-frames 180 --preset default
```

**Aggregate (4 клипа, 180 кадров каждый):**

| KPI | Значение |
|-----|----------|
| avg_fps | **85.2** |
| active_id_changes_per_min | 14.68 |
| lock_switches_per_min | 0.00 |
| false_lock_rate | 0.724 |

**Per-clip:**

| Клип | FPS | id_chg/min | false_lock_rate |
|------|-----|-----------|-----------------|
| `drone_closeup_mixkit_44644_360.mp4` | 164.8 | 0.00 | 1.000 |
| `night_ground_large_drones.mp4` | 59.5 | 58.72 | 0.861 |
| `Demo_IR_DRONE_146.mp4` | 55.0 | 0.00 | 0.556 |
| `IR_BIRD_001.mp4` | 61.5 | 0.00 | 0.478 |

---

## Интерпретация baseline

**Сильные стороны:**
- Высокий FPS на дневных клипах (>160 fps)
- Стабильный ID (0 изменений/мин) на дневных и IR-клипах
- lock_switches_per_min = 0 — нет нежелательных переключений

**Слабые сцены текущего baseline:**
1. **Ночные клипы** (`night_ground_large_drones.mp4`):
   - id_chg/min = 58.72 — крайне высокая нестабильность ID
   - false_lock_rate = 0.861 — большинство lock-кадров ложные
2. **Дневной closeup** (`drone_closeup_mixkit_44644_360.mp4`):
   - false_lock_rate = 1.000 — полный false lock (цель выходит из кадра быстро?)
3. **IR** (`Demo_IR_DRONE_146.mp4`, `IR_BIRD_001.mp4`):
   - Приемлемый id_chg, но false_lock ~0.5 — умеренный

**Основной pressure point:**
- Ночные сцены: false-lock и ID instability — главный приоритет для улучшений.

---

## Граница baseline (что не менять без пересчёта)

- Пресет `default` остаётся canonical для Day/Auto режимов
- Пресет `night` остаётся canonical для ночного режима
- Модели: не менять до прохождения quality gate на regression pack
- Порог: `false_lock_rate < 0.5` на IR-клипах как target для следующего цикла

---

## Ссылки

- Smoke data: `orchestrator/state/operator_smoke_20260311.md`
- Quality gate: `python_scripts/run_quality_gate.py` + `configs/regression_pack.csv`
- Runbook: `RUNBOOK.md`
