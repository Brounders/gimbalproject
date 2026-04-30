# REPORT-20260430 — Model Intake: antiuav_ir_v1

**Тип:** Model Intake Report  
**Статус:** IR_CANDIDATE_HOLD  
**Дата:** 2026-04-30

---

## Артефакт

| Поле | Значение |
|------|----------|
| Путь | `~/Desktop/Обученные модели/antiuav_ir_v1/weights/best.pt` |
| SHA256 | `dc9d3718510b38e0b0d1da8a7f9eaa391138d27396f0c107975a5ae8adfb83c5` |
| Архитектура | yolo11n.pt fine-tune |
| Датасет | Anti-UAV RGBT infrared subset (C:\train\antiuav_ir_v1\dataset.yaml) |
| Epochs | 200 |
| Training mAP50 | 0.989 |
| nc | 1 (класс: drone) |

---

## Gate результаты

### IR gate (preset: antiuav_thermal)

| Клип | Сцена | Кадров | lock_rate | continuity | idchg/min | Результат |
|------|-------|--------|-----------|------------|-----------|-----------|
| Demo_IR_DRONE_146 | ir | 313 | 99% | 1.000 | 0.00 | ✅ PASS |
| IR_DRONE_001 | ir | 301 | 99% | 1.000 | 0.00 | ✅ PASS |
| IR_BIRD_001 | noise | 310 | 99% | 1.000 | 0.00 | ✅ PASS* |

**IR gate: PASS** *(но см. Known Limitations)*

*GT отсутствует у всех IR клипов → false_lock не проверялся.

### Night gate (preset: night)

| Клип | Сцена | idchg/min | Порог | Результат |
|------|-------|-----------|-------|-----------|
| night_ground_large_drones | night | 24.47 | <8.0 | ❌ FAIL |

**Night gate: FAIL** — модель не предназначена для visible-light ночи.

---

## Known Limitations

- **Датасет drone-only:** nc=1, нет класса bird, нет background/negative кадров.
  Converter (`convert_antiuav_rgbt_to_yolo.py`) пропускает кадры где дрон не виден.
- **IR bird rejection не обучена и не валидирована:**
  IR_BIRD_001 (noise scene) имеет lock_rate=99% — модель не различает IR дронов и птиц.
  Это structural limitation текущего датасета, не устраняется конфигом.

---

## Статус

**IR_CANDIDATE_HOLD** — не production, не baseline.

Условия для promotion (context_specific, IR):
1. Human approval
2. GT-аннотации для IR тест-клипов (OQ-002)
3. Решение по IR bird rejection (отдельный training цикл)
