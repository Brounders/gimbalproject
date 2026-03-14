# BRIEF: Training v2 — Per-Context Model Strategy

Date: 2026-03-14
Status: Approved for next RTX cycle
Replaces: drone-bird-yolo curriculum (rejected AP-026)

---

## Контекст

**Почему предыдущая стратегия провалилась:**
drone-bird-yolo использовал unified dataset (IR + night + day в одном цикле).
Результат: IR-данные доминировали → night gate регрессировал с каждым chunk.
chunk6 (ep73-84): night false_lock=0.830; chunk10 (ep121-132): night false_lock=0.951.
Тренд ухудшался с эпохами → overfitting к IR-распределению.

**Новая стратегия: три независимых модели, три независимых датасета, три независимых gate.**

---

## Архитектура

| Модель | Slot файл | Пресет | Dataset profile |
|--------|-----------|--------|-----------------|
| night_model.pt | `models/night_model.pt` | `configs/night.yaml` | Только ночные visible-light клипы |
| ir_model.pt | `models/ir_model.pt` | `configs/antiuav_thermal.yaml` | Только IR/thermal клипы |
| day_model.pt | `models/day_model.pt` | `configs/default.yaml` | Только дневные visible-light клипы |

Базовый checkpoint для каждой: `models/baseline.pt` (drone_bird_probe_fast, SHA256: bedc77fe...)
Установка после acceptance: `install_baseline.py --context night|ir|day`

---

## Требования к датасету

### Night dataset
- Минимум 3 клипа с GT (label.json / gt.json рядом с видеофайлом)
- Имеющиеся: night_ground_large_drones (GT есть), night_ground_indicator_lights (GT есть)
- Нужно добавить: 1 клип с быстрым пролётом или частичной окклюзией (стресс-тест для NIGHT_CONFIRM=5)
- Классы: `drone` (основной), `bird` желательно
- Фон: городской + открытое небо + тёмный фон
- **НЕ смешивать** с IR или дневными клипами

### IR dataset
- Имеющиеся клипы для gate: Demo_IR_DRONE_146, IR_DRONE_001, IR_BIRD_001
- Минимум 5 клипов для обучения (3 gate + 2 дополнительных train-only)
- Классы: `drone`, `bird` (IR_BIRD_001 — ключевой негативный пример)
- Фон: термальный (тепловое излучение, различные тепловые сигнатуры)
- **НЕ смешивать** с visible-light клипами

### Day dataset
- Имеющиеся: drone_closeup_mixkit_44644_360.mp4 (GT отсутствует — БЛОКЕР)
- **БЛОКЕР: нужен GT-файл для drone_closeup_mixkit_44644_360.mp4**
  - Формат: `label.json` или `gt.json` рядом с видеофайлом
  - Аннотация: bounding box дрона per-frame (LabelMe / CVAT / manual)
- Минимум 3 клипа с GT: drone_closeup + 2 дополнительных
- Классы: `drone`, `bird`
- Фон: чистое небо + смешанный городской фон

---

## Порядок обучения (рекомендуемый)

1. **Night** → самая чёткая gate (2 PASS-клипа, известные threshold)
   - Обучить night_model на night-only dataset
   - Gate: `run_quality_gate.py --pack-file configs/regression_pack.csv --preset night`
   - Target: false_lock ≤ 0.55, id_chg ≤ 25.0 на обоих клипах
   - Если PASS: `install_baseline.py --context night`

2. **IR** → наиболее сложный контекст (gate FAIL известен, цель — improvement)
   - Обучить ir_model на IR-only dataset
   - Gate: `run_quality_gate.py --pack-file configs/regression_pack_ir.csv --preset antiuav_thermal`
   - Target минимум: IR_BIRD_001 PASS (не регрессировать); IR_DRONE_001 false_lock < 0.700
   - Stretch: Demo_IR_DRONE_146 id_chg < 30.0/min
   - Если улучшение: `install_baseline.py --context ir`

3. **Day** → только после GT-разметки drone_closeup клипа
   - Обучить day_model на day-only dataset
   - Gate: `run_quality_gate.py --pack-file configs/regression_pack_day.csv --preset default`
   - Пока нет GT: gate измеряет только FPS (не acceptance criteria)
   - После GT: target false_lock ≤ 0.55, id_chg ≤ 25.0

---

## Early Rejection Protocol

Каждый контекст проверяется после chunk3 (~36 epochs). Если условия не выполнены → REJECT:

### Night (chunk3 ≈ ep36)
```
false_lock > 0.55 × 1.15 = 0.63  →  REJECT
id_chg > 12.23 × 1.20 = 14.68   →  REJECT
```
Baseline (AP-025): false_lock=0.510, id_chg=12.23

### IR (chunk3 ≈ ep36)
```
IR_BIRD_001 false_lock > 0.15   →  REJECT (was 0.090 baseline — нельзя ухудшать PASS)
Demo_IR_DRONE_146 false_lock > 0.900  →  REJECT (хуже baseline 0.840)
```
Логика: IR gate уже провален на 2/3 клипах. Нельзя допустить регресс на единственном PASS-клипе.

### Day (chunk3 ≈ ep36)
```
FPS < 18.0  →  REJECT (деградация производительности)
```
Acceptance по false_lock недоступна до появления GT-файла.

---

## Acceptance Criteria (финальный gate)

Модель принимается в slot если ВСЕ условия выполнены:

| Контекст | Clip | false_lock threshold | id_chg threshold |
|----------|------|----------------------|------------------|
| Night | night_ground_large_drones | ≤ 0.55 | ≤ 25.0 |
| Night | night_ground_indicator_lights | ≤ 0.55 | ≤ 25.0 |
| IR | IR_BIRD_001 | ≤ 0.15 | ≤ 5.0 |
| IR | IR_DRONE_001 | ≤ 0.700 | ≤ 25.0 |
| IR | Demo_IR_DRONE_146 | ≤ 0.800 | ≤ 40.0 |
| Day | drone_closeup | ≤ 0.55* | ≤ 25.0* |

*Day acceptance требует GT-файла. До его появления gate — FPS-only.

---

## Что не входит в этот BRIEF

| Задача | Статус |
|--------|--------|
| Universal multi-context модель | Отклонено (доказано: вредит night при IR-обучении) |
| Data augmentation strategy | На усмотрение RTX-стороны |
| Hyperparameter sweep | На усмотрение RTX-стороны; используйте Ultralytics defaults |
| Hailo export | После acceptance на Mac; отдельный BRIEF |

---

## Ссылки

- Baseline: `models/baseline.pt`, SHA256: `bedc77fe7b899de1ac68ae654f49fcee6301a9d3f8a61e9eff5c1e8d66641d44`
- Baseline manifest: `models/baseline_manifest.json`
- IR runtime analysis: `orchestrator/reports/REPORT-ir-hardening-v1.md`, `REPORT-ir-hardening-v2.md`
- Rejection log: `automation/state/training_ledger.json` (drone-bird-yolo: rejected)
- Gate infrastructure: `python_scripts/run_quality_gate.py`, `python_scripts/install_baseline.py`
