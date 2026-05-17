# REPORT — TASK-20260517-108: Scale/Source-Aware Weak4 Pack & Candidate Gate

**Date:** 2026-05-17  
**Status:** ✅ EXECUTED — Candidate REJECTED (false positive gate fail)

---

## Что сделано

### 1. Аудит геометрии меток (из TASK-107)

| Клип | bbox w_mean | Диагноз |
|---|---|---|
| `1_minie3_range_close` | 0.731 (w_max=0.842) | **ПОЛОСА** — горизонтальная полоса на 73% кадра. Квантированы. |
| `antiuav_rgbt_train` | 0.102 | Крупный силуэт → Gate only |
| `9_dji2_range_medium` | 0.082 | ✅ Компактный hotspot |
| `antiuav_rgbt_20190925` | 0.037 | ✅ Маленький hotspot |

### 2. Построен пак `weak4_thermal_compact_20260517`

| Split | Клипы | Кол-во |
|---|---|---|
| **Train positives** | `9_dji2` + `antiuav_rgbt_20190925` | 273 (w<0.1) |
| **Hard negatives (train)** | airplane + bird clips | 78 |
| **Val/Gate** | `antiuav_rgbt_train` | 175 (не давит на обучение) |
| **Quarantined** | `1_minie3_range_close` strip labels | 96 исключены |

### 3. Обучение: baseline.pt fine-tune, 30 epoch, freeze=10, lr=0.001, MPS

mAP50 на val pack = **0.437** (compact thermal val set)

---

## Результаты GT Diagnostic — Кандидат vs Baseline

| Клип | Сцена | Baseline | Кандидат | Δ |
|---|---|---|---|---|
| 9_dji2_range_medium | IR | 0.276 | **0.412** | +0.136 ✅ |
| antiuav_rgbt_20190925 | IR | 0.000 | **0.163** | +0.163 ✅ |
| antiuav_rgbt_train | IR | 0.412 | **0.855** | +0.443 ✅ |
| f1_3_EO_dji_mavic_2 | EO | 0.000 | 0.385 | +0.385 ✅ |
| IR_DRONE_025 | IR | 0.987 | 0.987 | 0 ✅ |
| 2_minie3_range_birds | EO_NEG | 0.946 | 0.712 | **-0.234** ❌ |
| 7_minie5_blur | EO | 0.599 | 0.396 | **-0.203** ❌ |
| f2_13_IR_dji | IR | 0.685 | 0.424 | **-0.261** ❌ |
| 5_minie3_range_far | IR | 0.879 | 0.836 | -0.043 ⚠️ |
| **IR_AIRPLANE_014** | IR_NEG | **0.000** | **1.000** | 🔴 ЛОЖНАЯ БЛОКИРОВКА |
| **V_BIRD_030** | NEG | **0.000** | **0.201** | 🔴 ЛОЖНАЯ БЛОКИРОВКА |

---

## Вердикт: ОТКЛОНЁН

### Причина 1 (критическая) — Ложные блокировки:
- `IR_AIRPLANE_014` (IR_NEGATIVE клип): recall=1.000 — модель замкнулась на реальный самолёт и держала его **321/321 кадров**
- `V_BIRD_030` (NEGATIVE клип): recall=0.201 — ложный захват птицы
- Это неприемлемо для боевого применения

### Причина 2 — EO регрессии:
- `2_minie3_range_birds`: 0.946→0.712 (-23%)
- `7_minie5_blur`: 0.599→0.396 (-20%)
- `f2_13_IR_dji`: 0.685→0.424 (-26%)

### Что произошло:
Compact thermal pack обучил модель агрессивно детектировать маленькие тепловые цели (compact hotspots). Это дало прирост на целевых IR-клипах, но те же признаки срабатывают на самолёты (тепловой след) и птиц (тепловой контраст). 78 hard negatives оказалось недостаточно для подавления.

---

## Анализ: почему hard negatives не помогли

Airplane и bird hard negatives находятся в полном стационарном кадре. Модель видела их как фоновые объекты. Но в runtime самолёт движется и даёт компактный тепловой след — это неотличимо от тренировочных примеров `antiuav_rgbt_20190925` (w=0.037, h=0.022).

---

## Что нужно для следующей итерации

1. **Больше airplane hard negatives с движением** — статичные airplane кадры не учат различать движущийся тепловой объект
2. **Разделить по масштабу:** антидрон детектор и антиptица — возможно отдельные головы или conf пороги
3. **Либо:** не обучать на `antiuav_rgbt_20190925` пока нет достаточных negative counterexamples для тепловых объектов того же масштаба
4. **Либо:** RTX с полным датасетом — M1 smoke-train имеет ограниченную regularization на 30 ep

---

## Открытые задачи

- Baseline = `drone_bird_probe_fast` (baseline.pt) — не изменён, не затронут
- Candidate weights в `runs/smoke_train/compact_thermal_30ep/weights/` — не промоутить
- Следующий шаг: решение Human/Codex о направлении (RTX с лучшими негативами vs другая стратегия)
