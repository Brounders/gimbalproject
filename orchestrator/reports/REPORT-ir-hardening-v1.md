# REPORT: IR Runtime Hardening v1

Date: 2026-03-13
Status: Done — null result, diagnostic value
Type: YAML tuning + evidence. No training changes.

---

## Before (baseline_formalization_ir)

| Clip | false_lock | id_chg/min | Gate |
|------|-----------|------------|------|
| Demo_IR_DRONE_146 | 0.840 | 63.26 | FAIL |
| IR_DRONE_001 | 0.784 | 5.98 | FAIL |
| IR_BIRD_001 (noise) | **0.090** | 0.00 | **PASS** |

---

## Изменения в antiuav_thermal.yaml

Добавлены 4 lock policy knobs (из night.yaml experience, AP-021/stage-3):
```yaml
active_id_switch_cooldown_frames: 60   # default 30
track_state_acquire_frames: 4          # default 3
lock_mode_acquire_frames: 3            # default 2
active_id_switch_allow_if_lost_frames: 12  # default 6
```

---

## After (ir_hardening_v1)

| Clip | false_lock | id_chg/min | Gate |
|------|-----------|------------|------|
| Demo_IR_DRONE_146 | 0.840 | **63.26** | FAIL |
| IR_DRONE_001 | 0.784 | **5.98** | FAIL |
| IR_BIRD_001 (noise) | **0.090** | 0.00 | **PASS** |

**Все метрики идентичны.** Нет улучшений, нет регрессий.

---

## Root Cause Analysis

Lock policy layer **не является** источником `id_chg=63.26` на Demo_IR_DRONE_146.

**Почему knobs не помогли:**

`active_id_switch_cooldown_frames=60` должен был предотвращать переключения ID на 60 кадров
(~2.7 секунды при 22fps). Если id_chg остался 63.26/min (~1.05 switch/sec), то переключения
происходят через механизм, который НЕ контролируется cooldown.

**Вероятный механизм:**
1. YOLO detection на Demo_IR_DRONE_146 нестабилен — dетекции пропадают на несколько кадров
2. После пропуска детекций трек переходит в LOST (track_state_lost_frames=8, default)
3. Из LOST система переходит в SCAN (recover mode)
4. SCAN находит новую цель → новый ID → новая инициализация трека
5. Это **не ID switch** (cooldown не применяется) — это **track reset**

**Следствие:** `active_id_switch_cooldown_frames` контролирует переключения в TRACK/LOCK mode.
Track resets из SCAN mode обходят cooldown полностью.

---

## Следующий шаг для IR (для Codex/следующего цикла)

Проблема разделяется на два независимых слоя:

| Проблема | Слой | Инструмент |
|----------|------|-----------|
| id_chg=63.26 на Demo_IR_DRONE_146 | Track persistence | Попробовать `track_state_lost_frames: 16-20` в antiuav_thermal.yaml — держать трек дольше при пропусках детекций |
| false_lock=0.840 на IR_DRONE_001 | Model/YOLO | Требует IR-обученную модель или IR-специфичный conf_thresh tuning |

**Предостережение для track_state_lost_frames:** в AP-022 это значение вызвало регрессию
на night clips. Для IR контекст другой (false_lock=0.840 это уже плохо, не 0.510 как у night).
Риск: увеличение lost_frames может продлить false lock events. Нужен отдельный цикл.

---

## Retained knobs

4 добавленных knobs оставлены в `antiuav_thermal.yaml` — не вызвали регрессий,
обеспечивают governance-согласованность с night.yaml. При наличии нормальных YOLO
детекций они предотвратят быстрые ID switches.
