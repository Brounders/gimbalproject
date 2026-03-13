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

## Runtime Hardening Changes (AP-018)

Изменения внесены в `night.yaml` и `antiuav_thermal.yaml` для снижения false-lock на ночных и IR сценах.

| Параметр | Файл | Было | Стало | Цель |
|----------|------|------|-------|------|
| `drone_lock_score_min` | `night.yaml` | 0.58 | **0.64** | Строже порог lock |
| `drone_reacquire_score_min` | `night.yaml` | 0.45 | **0.52** | Строже reacquire |
| `lock_confirm_frames` | `night.yaml` | 5 (default) | **7** | Дольше подтверждение lock |
| `drone_lock_score_min` | `antiuav_thermal.yaml` | 0.56 | **0.60** | Строже порог lock |
| `drone_reacquire_score_min` | `antiuav_thermal.yaml` | 0.42 | **0.48** | Алайн с default |
| `lock_confirm_frames` | `antiuav_thermal.yaml` | 5 (default) | **7** | Дольше подтверждение lock |

> `lock_confirm_frames` доступен через YAML начиная с AP-018 (добавлен в `profile_io.py` mapping).

---

## Runtime Hardening Changes (AP-019)

Второй слой hardening: сокращение grace-period, ускорение release, сужение spatial gate reacquire.

| Параметр | Файл | Было | Стало | Цель |
|----------|------|------|-------|------|
| `lock_lost_grace` | `night.yaml` | 2 (default) | **1** | Меньше tolerance для gap в detection |
| `lock_mode_release_frames` | `night.yaml` | 6 (default) | **4** | Быстрее отпускает ложный lock |
| `lock_reacquire_dist` | `night.yaml` | 120 (default) | **90** | Уже spatial gate для reacquire |
| `lock_lost_grace` | `antiuav_thermal.yaml` | 2 (default) | **1** | Меньше tolerance для gap |
| `lock_mode_release_frames` | `antiuav_thermal.yaml` | 6 (default) | **4** | Быстрее release |
| `lock_reacquire_dist` | `antiuav_thermal.yaml` | 120 (default) | **90** | Уже spatial gate |

> `lock_lost_grace` и `lock_reacquire_dist` доступны через YAML начиная с AP-019.
> Effective reacquire dist = base + speed_bonus (до +90 px): быстрые цели reacquire штатно.

---

## Runtime Hardening Changes (AP-020)

Третий слой hardening: снижение ID-нестабильности на ночных сценах с крупными дронами.

| Параметр | Файл | Было | Стало | Цель |
|----------|------|------|-------|------|
| `active_id_switch_cooldown_frames` | `night.yaml` | 30 (default) | **60** | Двойной cooldown между ID-switches |
| `class_ema_alpha` | `night.yaml` | 0.22 | **0.15** | Медленнее EMA, стабильнее drone_score |

> Оба параметра уже доступны через YAML mapping (AP-019 и ранее).

---

## Runtime Hardening Changes (AP-021)

Четвёртый слой hardening: тighter track acquisition и cooldown bypass для индикаторных огней и крупных дронов.

| Параметр | Файл | Было | Стало | Цель |
|----------|------|------|-------|------|
| `track_state_acquire_frames` | `night.yaml` | 3 (default) | **4** | 4 детекции для установления трека (меньше false tracks от мигающих огней) |
| `lock_mode_acquire_frames` | `night.yaml` | 2 (default) | **3** | 3 фрейма для входа в lock mode (меньше false lock entries) |
| `active_id_switch_allow_if_lost_frames` | `night.yaml` | 6 (default) | **12** | 12 фреймов потери до bypass cooldown (сильно снижает id_changes/min) |

> Все три параметра уже доступны через YAML mapping.
> Effective: `cooldown_frames=60` + `allow_if_lost=12` — ID switch байпасится только после долгой потери.

---

## Runtime Hardening Changes (AP-022)

Пятый слой hardening: lock tracker correlation gate + track persistence для large-target night scenes.

| Параметр | Файл | Было | Стало | Цель |
|----------|------|------|-------|------|
| `track_state_lost_frames` | `night.yaml` | 8 (default) | **12** | Держать track 12 кадров до LOST — меньше бросает трек на large drone |
| `lock_tracker_min_score` | `night.yaml` | 0.42 (default) | **0.52** | Строже correlation gate для lock tracker — меньше false lock entries |

> Оба параметра уже доступны через YAML mapping.

---

## Preset Runtime Tuning Contract

Ключевые runtime knobs для каждого контекста. Источник: YAML конфиги + `profile_io.py::apply_overrides` mapping.

> **Важно:** не все поля `Config` доступны через YAML — только те, что есть в mapping `apply_overrides`.

| Параметр | day (default) | night | ir (antiuav_thermal) | Эффект |
|----------|--------------|-------|---------------------|--------|
| `conf_thresh` | 0.30 | 0.12 | 0.12 | Detection sensitivity |
| `imgsz` | 640 | 960 | 960 | Resolution for detection |
| `small_target_mode` | false | true | true | Small target path |
| `lock_confirm_frames` | 5 | **7** | **7** | Frames to confirm lock |
| `lock_lost_grace` | 2 | **1** | **1** | Grace frames in lock confirmation |
| `lock_mode_release_frames` | 6 | **4** | **4** | Frames to exit lock state |
| `lock_reacquire_dist` | 120 | **90** | **90** | Base spatial gate for reacquire (px) |
| `drone_lock_score_min` | 0.62 | **0.64** | **0.60** | Minimum lock score |
| `drone_reacquire_score_min` | 0.48 | **0.52** | **0.48** | Minimum reacquire score |
| `night_mot_thresh` | 18 (default) | 14 | 14 | Night motion threshold |
| `night_diff_thresh` | 12 (default) | 10 | 10 | Night diff threshold |
| `display_min_hit_streak_night` | 3 (default) | 4 | 4 | Min hits before display |
| `display_max_lost_frames` | 2 (default) | 1 | 1 | Max frames lost before drop |
| `active_id_switch_cooldown_frames` | 30 (default) | **60** | 30 (default) | Cooldown frames between ID switches |
| `track_state_acquire_frames` | 3 (default) | **4** | 3 (default) | Consecutive detections to acquire track |
| `lock_mode_acquire_frames` | 2 (default) | **3** | 2 (default) | Confirm-frames to enter lock mode |
| `active_id_switch_allow_if_lost_frames` | 6 (default) | **12** | 6 (default) | Lost frames before cooldown bypass |
| `track_state_lost_frames` | 8 (default) | **12** | 8 (default) | Frames before track goes to LOST state |
| `lock_tracker_min_score` | 0.42 (default) | **0.52** | 0.42 (default) | Minimum correlation score for lock tracker |
| `class_ema_alpha` | 0.18 (default) | **0.15** | 0.24 | Drone score EMA alpha |
| `budget_target_fps` | 24.0 (default) | 22.0 | 20.0 | Budget FPS target |
| `velocity_alpha` | 0.55 (default) | 0.68 | 0.72 | Motion smoothing |

---

## Ссылки

- Smoke data: `orchestrator/state/operator_smoke_20260311.md`
- Quality gate: `python_scripts/run_quality_gate.py` + `configs/regression_pack.csv`
- Runbook: `RUNBOOK.md`
