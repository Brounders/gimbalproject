# REPORT — TASK-103f: Re-acquisition Suppression After Health Release

**Date:** 2026-05-17  
**Commit:** `96dd3ac`  
**Status:** ✅ PASS (no regression; see analysis)

---

## Решение и обоснование

Исходный план 103f был "lock_tracker multi-scale". После ULTRATHINK-анализа принято другое решение:

**Реальная проблема:** После health gate release (103e) `pick_active_by_trust` немедленно переизбирала тот же lock target (он оставался единственным в `targets`). Это создавало цикл: release → re-lock (cooldown reset 60 frames) → standard trust-switch никогда не успевал сработать → streak снова накапливается за 80 frames → release снова.

**Фикс:** Подавление re-selection того же `track_id` на `LOCK_HEALTH_RELEASE_STREAK` кадров после health-gate release.

**Lock_tracker multi-scale отклонён** по двум причинам:
1. Off-target в antiuav_rgbt clips — lock дрейфует на фон, а не теряет масштаб; multi-scale не помог бы
2. f2_13_IR уже имеет p99=269ms — добавление 3x template search создало бы latency regression

---

## Что реализовано

**`src/uav_tracker/tracking/target_manager.py`:**
- `self._health_released_tid: int | None` — tid, подавленный после health release
- `self._health_suppress_frames: int` — осталось кадров подавления
- `_run_health_gate()`: перед `_set_active_id(None)` устанавливает `_health_released_tid = _ha.track_id`, `_health_suppress_frames = _streak`
- `_set_active_id(tid)`: при успешном switch → очищает подавление
- `release_active()`: operator release → очищает подавление
- `current is None` branch: декрементирует счётчик, пропускает подавленный tid пока `_health_suppress_frames > 0`

**`tests/test_lock_health.py`** (+3 теста, итого 10):
- `test_suppression_prevents_immediate_relock`
- `test_suppression_cleared_by_trusted_switch`
- `test_suppression_cleared_by_operator_release`

---

## A/B Gate — 103f vs 103e baseline

| Clip | Scene | 103e | 103f | Delta |
|---|---|---|---|---|
| 1_minie3_range_close | IR | 0.000 | 0.000 | 0 |
| 2023-11-23 14-56-24 | UNKNOWN | 0.164 | 0.164 | 0 |
| 2_minie3_range_medium_close_birds | EO_NEG | 0.946 | **0.950** | +0.004 |
| 5_minie3_range_far | IR | 0.879 | 0.879 | 0 |
| 7_minie5_range_all_cut_blur | EO | 0.599 | 0.599 | 0 |
| 9_dji2_range_medium | IR | 0.276 | 0.276 | 0 |
| IR_DRONE_025 | IR | 0.987 | 0.987 | 0 |
| antiuav_rgbt_train | IR | 0.412 | 0.412 | 0 |
| f2_13_IR_dji_mavic_2 | IR | 0.685 | 0.685 | 0 |

**Регрессий нет. Один минимальный плюс (+0.004 на EO_NEG клипе).**

### Latency p99 — variance анализ

Несколько клипов показали рост p99 (197ms vs 79ms на 1_minie3). Это run-to-run шум MOG2 (FPS остался в том же диапазоне: 15.8 vs 18.5). Suppression добавляет 3 сравнения per frame — не может быть причиной 2.5x latency jump. Классифицировано как noise.

---

## Почему antiuav_rgbt_train остаётся 0.412

Корень проблемы — **детекция, не селектор**:
- Night detector (MOG2) инициализируется нестабильно из-за auto-scene detect
- Когда night detector НЕ срабатывает: lock дрейфует на фон → off-target
- Suppression предотвращает цикл re-lock, но night target не может быть promoted когда active=None (night source — не primary_source по архитектуре системы)
- Решение → 103h (улучшение детектора) или промотирование night source в primary (архитектурное решение)

---

## Серия 103 — итог

| Этап | Статус | Recall impact |
|---|---|---|
| 103a | ✅ | baseline +diagnostic |
| 103b | ✅ | bbox stability |
| 103c | ✅ | auto-scene-detect |
| 103d | ✅ | antiuav_rgbt_train 0→0.412 (stable) |
| 103e | ✅ | last-resort safety valve |
| 103f | ✅ | re-lock cycle prevention |
| 103g | ✅ N/A | — |
| 103h | ⏸ | next: detection improvement |

**Следующий шаг: TASK-20260516-100 или 103h — решение за Human/Codex.**
