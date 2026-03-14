# CODEX HANDOFF LOG

> Лог автономной работы Claude Mac начиная с 2026-03-13.
> Codex: прочти этот файл перед открытием нового AP-цикла.
> Записи добавляются снизу в хронологическом порядке.

---

<!-- ЗАПИСИ НАЧИНАЮТСЯ ЗДЕСЬ -->

---

## 2026-03-13 — Сессия 1: Baseline + Day Gate + IR Hardening v1

### Что сделано

**1. Day Gate — Governance Fix**
- `configs/regression_pack_day.csv`: добавлен комментарий — day clip `drone_closeup_mixkit_44644_360.mp4` без GT, `false_lock=1.000` структурно для любой модели
- `RUNBOOK.md`: добавлена секция "Day Gate — известное ограничение (FPS-only)"
- **Вывод:** day gate теперь используется только для FPS и id_chg/min сравнений
- Commit: `governance: day gate is FPS-only`

**2. Baseline Formalization**
- Прогнан IR gate на `drone_bird_probe_fast` (первый раз): Demo_IR_DRONE_146 false_lock=0.840/id_chg=63.26 FAIL; IR_DRONE_001 false_lock=0.784 FAIL; IR_BIRD_001 false_lock=0.090 PASS
- `install_baseline.py` выполнен → `models/baseline.pt` установлен
- SHA256: `bedc77fe7b899de1ac68ae654f49fcee6301a9d3f8a61e9eff5c1e8d66641d44`
- `models/baseline_manifest.json` создан с gate-привязками (night + IR)
- `automation/state/decision_log.json`: добавлена запись `install_as_baseline`
- Отчёт: `orchestrator/reports/REPORT-baseline-formalization.md`
- Commit: `baseline: formalize drone_bird_probe_fast as models/baseline.pt`

**3. IR Hardening v1 — Null Result (диагностически важно)**
- Добавлены 4 lock policy knobs в `configs/antiuav_thermal.yaml`:
  `active_id_switch_cooldown_frames=60`, `track_state_acquire_frames=4`,
  `lock_mode_acquire_frames=3`, `active_id_switch_allow_if_lost_frames=12`
- Gate: Demo_IR_DRONE_146 id_chg **63.26 (без изменений)** → lock policy layer НЕ является драйвером
- Root cause: YOLO детекции нестабильны → трек уходит в LOST → SCAN → новый ID (track reset, не ID switch)
- Cooldown не применяется к track resets из SCAN mode
- Отчёт: `orchestrator/reports/REPORT-ir-hardening-v1.md`
- Commit: `IR hardening v1: null result`

### Ключевые числа после сессии

| Контекст | Clip | false_lock | id_chg/min | Статус |
|----------|------|-----------|------------|--------|
| Night | large_drones | **0.510** | **12.23** | PASS (AP-025) |
| Night | indicator_lights | **0.096** | 0.00 | PASS (AP-025) |
| IR | Demo_IR_DRONE_146 | 0.840 | 63.26 | FAIL — open |
| IR | IR_DRONE_001 | 0.784 | 5.98 | FAIL — open |
| IR | IR_BIRD_001 | **0.090** | 0.00 | PASS |
| Day | drone_closeup | 1.000* | 0.00 | *no GT — FPS-only |

### Что открыто для следующего цикла Codex

1. **IR id_chg (Demo_IR_DRONE_146)**: попробовать `track_state_lost_frames: 16-20` в `antiuav_thermal.yaml` — держать трек при кратковременных YOLO пропусках. Риск: может продлить false_lock events. Нужен отдельный AP-цикл.
2. **IR false_lock (IR_DRONE_001: 0.784)**: требует модельного решения — лучшая IR-trained модель. Runtime tuning даст лишь partial improvement.
3. **Day GT**: `drone_closeup_mixkit_44644_360.mp4` нужен `label.json` для полноценного day gate.
4. **Training strategy reset**: dataset audit drone-bird-yolo + новый training plan (одобрение Codex).

---

## 2026-03-14 — Сессия 2: Training Preparation — IR Finalization + Infrastructure + BRIEF

### Что сделано

**1. IR Hardening v2 — track_state_lost_frames sweep (окончательный вывод)**
- Протестированы `track_state_lost_frames=12` и `track_state_lost_frames=16` — оба дали **ноль эффекта** (id_chg=63.26 без изменений)
- Вывод: детекционные пропуски на Demo_IR_DRONE_146 длиннее 16 кадров (~0.73 сек)
- **Все runtime levers исчерпаны** — 6 параметров протестированы в v1 + v2, ни один не дал эффекта
- Отчёт: `orchestrator/reports/REPORT-ir-hardening-v2.md`
- Commit: `IR hardening v2: track_state_lost_frames sweep — runtime lever exhausted`

**2. Per-Context Model Infrastructure**
- `models/README.md`: добавлена секция "Per-Context Model Slots" — документированы 4 slot-файла (baseline/night/ir/day)
- `configs/night.yaml`, `configs/antiuav_thermal.yaml`, `configs/default.yaml`: добавлены комментарии к `model_path:` с указанием будущих специализированных слотов
- `python_scripts/install_baseline.py`: добавлен `--context {baseline,night,ir,day}` — маршрутизирует установку в `night_model.pt`, `ir_model.pt`, `day_model.pt` с отдельными manifest-файлами
- Commit: `feat: per-context model slots — README, preset comments, install_baseline --context`

**3. Training BRIEF v2**
- Создан: `orchestrator/briefs/BRIEF-training-v2-per-context.md`
- Стратегия: три независимых модели (не unified dataset — drone-bird-yolo провалил именно из-за смешения)
- Документированы: требования к датасету для каждого контекста, порядок обучения, early rejection threshold (chunk3), acceptance criteria
- **БЛОКЕР для Day**: нужен GT-файл (`label.json`) для `drone_closeup_mixkit_44644_360.mp4` — без него day acceptance невозможен
- Commit: `brief: training v2 — per-context model strategy, dataset reqs, early rejection`

**4. TASK-033 и TASK-034 — Уже выполнены (подтверждено)**
- `app/ui/theme.py`: уже существует с `APP_STYLESHEET`; `main_gui.py` уже импортирует из него
- `src/uav_tracker/frame_result.py` и `overlay.py`: уже существуют; `pipeline.py` уже импортирует из них
- Оба task выполнены в предыдущей сессии, не требуют дополнительной работы

### Ключевые числа после сессии (без изменений по IR)

| Контекст | Clip | false_lock | id_chg/min | Статус |
|----------|------|-----------|------------|--------|
| Night | large_drones | **0.510** | **12.23** | PASS (AP-025) |
| Night | indicator_lights | **0.096** | 0.00 | PASS (AP-025) |
| IR | Demo_IR_DRONE_146 | 0.840 | 63.26 | FAIL — **runtime exhausted** |
| IR | IR_DRONE_001 | 0.784 | 5.98 | FAIL — требует модели |
| IR | IR_BIRD_001 | **0.090** | 0.00 | PASS |
| Day | drone_closeup | 1.000* | 0.00 | *no GT — FPS-only |

### Что открыто для следующего цикла Codex

1. **RTX: обучение night_model** — приоритет 1. Night dataset уже есть (2 клипа с GT). Запустить обучение на ночных visible-light данных. Early rejection threshold: chunk3 false_lock > 0.63 → REJECT. После acceptance: `install_baseline.py --context night`.

2. **RTX: обучение ir_model** — приоритет 2. Нужны дополнительные IR-клипы для train-set (gate клипы не должны быть единственными обучающими данными). Gate target минимум: IR_BIRD_001 PASS (false_lock ≤ 0.15).

3. **Day GT разметка** — **БЛОКЕР для day_model**. Пользователь должен разметить `drone_closeup_mixkit_44644_360.mp4` (LabelMe/CVAT или manual label.json). Без GT day acceptance невозможен.

4. **Подробности в**: `orchestrator/briefs/BRIEF-training-v2-per-context.md`
