# CODEX HANDOFF LOG

> Этот файл ведётся Claude Mac в период автономной работы без Codex-планировщика.
> Codex: прочти этот файл целиком перед тем как открывать новый AP-цикл.
> Обновляется снизу — новые записи добавляются в конец.

---

## Контекст момента (на 2026-03-13)

### Принятый runtime-стек (AP-025)

Все runtime-прогоны ведутся с пресетом `night` из `configs/night.yaml`:
```
night_confirm:    5     # default 3 — key AP-025 fix
night_track_dist: 65    # default 42 — AP-024 fix
night_max_area:   220   # default 200 — AP-024 fix
night_lost_max:   8     # default 8
lock_lost_grace:  1     # default 2 — kept at 1 (grace=2 caused id_chg regression)
```

Эти значения дали первый PASS ночного гейта в истории проекта.

### Принятые gate-результаты (de-facto baseline, AP-025)

| Clip | Пресет | false_lock | id_chg/min | Gate |
|------|--------|-----------|------------|------|
| night_ground_large_drones | night | **0.510** | **12.23** | PASS |
| night_ground_indicator_lights | night | **0.096** | 0.00 | PASS |
| drone_closeup_mixkit_44644_360 | default | 1.000 | 0.00 | FAIL* |
| IR_DRONE_001 | antiuav_thermal | 0.784 | 5.98 | FAIL |
| Demo_IR_DRONE_146 | antiuav_thermal | 0.840 | 63.26 | FAIL |

*Day clip false_lock=1.000 у ВСЕХ моделей включая baseline — структурная проблема, не связана с моделью.

### Модельный стек

| Роль | Файл | Статус |
|------|------|--------|
| de-facto baseline | `runs/detect/runs/drone_bird_probe_fast/weights/best.pt` | Используется через `resolve_model_path()` fallback |
| Формальный baseline | `models/baseline.pt` | **ОТСУТСТВУЕТ** — не установлен |
| Последний RTX (rejected) | `models/checkpoints/rtx_drone_stability_12h_v1_epoch176_best.pt` | Отклонён |
| Curriculum drone-bird-yolo | chunk1..chunk10 (ep1-132) | **Отклонён** (AP-026) |

### Решение AP-026

`reject_and_reset_training_strategy` для curriculum `drone-bird-yolo`.
Записано в `automation/state/decision_log.json` (первая запись).
Причина: night gate regression нарастает с эпохами (chunk6: 0.830, chunk10: 0.951 vs baseline 0.510).

---

## Нерешённые задачи (backlog — ждут нового AP от Codex)

### Приоритет 1 — Baseline Formalization
**Что нужно сделать:**
- Запустить полный three-context gate (`day/night/ir`) на `drone_bird_probe_fast` модели
- Если day gate по-прежнему failing — разобраться, это структурная проблема клипа или модели
- Формально установить baseline через `install_baseline.py` с manifest и sha256

**Команды:**
```bash
source tracker_env/bin/activate
PYTHONPATH=src python python_scripts/run_quality_gate.py --pack-file configs/regression_pack_day.csv --preset default --tag baseline_formalization_day
PYTHONPATH=src python python_scripts/run_quality_gate.py --pack-file configs/regression_pack_night.csv --preset night --tag baseline_formalization_night
PYTHONPATH=src python python_scripts/run_quality_gate.py --pack-file configs/regression_pack_ir.csv --preset antiuav_thermal --tag baseline_formalization_ir
```

**Риск:** day gate структурно failing на текущем клипе (`drone_closeup_mixkit_44644_360`). Возможно, нужен новый day test clip.

### Приоритет 2 — Training Strategy Reset
**Что нужно сделать:**
- Аудит датасета `drone-bird-yolo`: какова реальная доля ночных / visible-light / IR клипов
- Определить: перетренировать на mixed-context датасете или fine-tune drone_bird_probe_fast
- Открыть новый BRIEF и AP-цикл для RTX training с новой стратегией

**Контекст отклонения:**
- Curriculum обучался с `scene_profile: ir` — возможно в датасете мало visible-light ночных клипов
- Это объясняет, почему больше эпох = хуже ночные метрики (модель всё больше специализируется на IR)

### Приоритет 3 — IR Gate Improvement
**Что:** IR clips по-прежнему fail (IR_DRONE_001 false_lock=0.784, Demo_IR_DRONE_146 false_lock=0.840).
**Не открывать** без baseline formalization и без отдельного BRIEF.

---

## Лог действий Claude Mac в автономном режиме

### 2026-03-13 — Начало автономного периода

**Статус на момент начала:**
- AP-026 принят и закрыт
- Открытых задач нет (`open_tasks.md` пуст)
- `active_plan.md` в статусе Completed

**Первые действия:**
- Создан этот handoff-лог: `orchestrator/handoff/CODEX_HANDOFF.md`
- Ожидание указаний от пользователя или самостоятельный выбор следующего шага из backlog

---

<!-- НОВЫЕ ЗАПИСИ ДОБАВЛЯЮТСЯ НИЖЕ ЭТОЙ СТРОКИ -->
