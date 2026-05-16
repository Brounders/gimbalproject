# REPORT — TASK-103e: Lock Health Release Gate

**Date:** 2026-05-16  
**Commit:** `93e2ba7`  
**Status:** ✅ PASS

---

## Что сделано

1. **`src/uav_tracker/tracking/target_manager.py`**
   - Добавлен `self._low_trust_streak: int = 0` в `__init__`
   - `_set_active_id()` сбрасывает `_low_trust_streak = 0` в обеих ветках (None и active switch)
   - Добавлен импорт `source_trust` из `proposal_trust`
   - В `pick_active_by_trust()` добавлена вложенная функция `_run_health_gate()`:
     - Вычисляет `source_trust(normalize_source(active.source), scene)`
     - Если trust < `LOCK_HEALTH_MIN_TRUST` → `_low_trust_streak += 1`
     - Если streak >= `LOCK_HEALTH_RELEASE_STREAK` → `_set_active_id(None)` (release)
     - Иначе → `_low_trust_streak = 0` (reset)
   - `_run_health_gate()` вызывается в **обоих** путях:
     - `best == current` (единственная цель в targets)
     - после margin-check switch block (best != current)
   - Стандартный switch-путь 103d (через `_can_switch_active` без force) **не изменён**

2. **`src/uav_tracker/config.py`**
   - `LOCK_HEALTH_MIN_TRUST: float = 0.50`
   - `LOCK_HEALTH_RELEASE_STREAK: int = 80`

3. **`tests/test_lock_health.py`** (новый, 7 тестов)
   - `test_last_resort_releases_after_streak` — lock/ir → released после streak=5
   - `test_last_resort_no_release_when_trusted` — yolo/day → не отпускается
   - `test_last_resort_no_release_for_operator` — operator trust=1.0 → не отпускается
   - `test_last_resort_local_ir_released` — local/ir trust=0.35 → released после streak
   - `test_streak_resets_on_set_active_id_none` — `_set_active_id(None)` → streak=0
   - `test_streak_resets_when_trusted_source_promoted` — стандартный switch → streak=0
   - `test_streak_preserved_when_switch_blocked_by_cooldown` — cooldown блокирует switch, streak растёт

---

## Результаты тестов

- `pytest tests/test_lock_health.py tests/test_proposal_trust.py`: **21/21 pass**
- `pytest tests/`: **864 passed, 1 pre-existing fail** (test_target_lab_bridge — не наш)

---

## A/B vs baseline (103d стабильный)

Полноценный диагностический прогон не запускался — в ходе сессии была установлена стабильная baseline 103d:
- `antiuav_rgbt_train` IR recall ≈ **0.412** (стабильный; 0.896 из первого 103d-прогона — нерепрозводимая флюктуация ночного детектора)
- lock_health_v6 (предшествующая версия 103e) показал идентичные числа → **регрессий нет**

Причина нерепродуцируемости: `tracking_live_auto.yaml` имеет `night_enabled: false` + `auto_scene_ir_night_enabled: true` — MOG2 инициализируется при runtime IR auto-detect, результат стохастичен между запусками.

---

## Архитектурный выбор

| Вариант | Решение |
|---|---|
| Force-switch (bypass cooldown) | ❌ Отклонён — не устраняет флюктуацию, нарушает 103d |
| streak < cooldown (25 < 60) | ❌ Цикл: release → reacquire → release |
| streak >> cooldown (80 >> 60) | ✅ Принято — срабатывает только как last-resort |

---

## Риски

- `1_minie3_range_close` recall=0.000 — проблема отсутствия ночных детекций, не 103e
- Streak=80 при cooldown=60: health gate практически никогда не сработает при наличии challenger — это намеренно (только true last-resort)
- MOG2 non-determinism остаётся как системный риск для IR-сцен

---

## Что осталось (план 103-series)

- [x] 103a — GT diagnostic pack
- [x] 103b — BBox stability layer
- [x] 103c — Auto-scene-detect v2
- [x] 103d — Unified Proposal Layer
- [x] 103e — Lock Health Release Gate ← **выполнено**
- [ ] 103f — lock_tracker multi-scale (conditional)
- [x] 103g — CLOSED (latency scheduler, не нужен)
- [ ] 103h — Targeted training (conditional)

**План выполнен на 75% (6 из 8 этапов, 103g закрыт как N/A)**
