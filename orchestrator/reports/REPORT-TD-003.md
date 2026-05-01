# REPORT TD-003: magic numbers → Config

**Date:** 2026-05-01
**Status:** ACCEPTED
**Commit:** 351f1c8

---

## Changes

| File | Constants added/used | Magic numbers replaced |
|------|---------------------|----------------------|
| `src/uav_tracker/config.py` | 16 added | — |
| `src/uav_tracker/tracking/target_manager.py` | 12 | 12 |
| `src/uav_tracker/pipeline.py` | 2 | 2 |
| `src/uav_tracker/tracking/lock_tracker.py` | 0 | 0 (нет повторяющихся чисел) |

---

## Constants Added to Config

| Constant | Value | Meaning |
|----------|-------|---------|
| `SELECT_ACTIVE_CONF_WEIGHT` | 1.2 | Вес conf в select_active() scoring |
| `SELECT_ACTIVE_STREAK_CAP` | 4.0 | Максимальный вклад hit_streak |
| `SELECT_ACTIVE_STREAK_WEIGHT` | 0.35 | Множитель hit_streak |
| `SELECT_ACTIVE_LOST_PENALTY` | 0.8 | Штраф за lost_frames / night penalty |
| `SELECT_ACTIVE_DRONE_WEIGHT` | 2.8 | Бонус drone_score для primary sources |
| `SELECT_ACTIVE_MIN_SPEED` | 1.0 | Мин. скорость для продвижения цели |
| `REACQUIRE_SPEED_DIST_CAP` | 90 | Макс. вклад скорости в reacquire radius |
| `REACQUIRE_SPEED_MULT` | 1.8 | Множитель скорости для reacquire radius |
| `REACQUIRE_LOST_MULT` | 12 | Множитель lost_frames для reacquire radius |
| `REACQUIRE_PRED_GATE_CAP` | 70 | Макс. вклад скорости в pred gate |
| `REACQUIRE_PRED_GATE_SPEED_MULT` | 2.0 | Множитель скорости для pred gate |
| `FOCUS_MAX_DIST_SPEED_CAP` | 70 | Макс. вклад скорости в focus max dist |
| `FOCUS_MAX_DIST_SPEED_MULT` | 1.6 | Множитель скорости для focus max dist |
| `ROI_OVERLAP_IOU_THRESH` | 0.35 | IoU порог подавления ROI детекций |
| `LOCK_SCORE_VALIDATE_MARGIN` | 0.12 | Запас к LOCK_TRACKER_MIN_SCORE при local validate |
| `LOCK_SCORE_VALIDATE_MIN` | 0.55 | Нижний порог при local validate |

---

## Tests

- Добавлен `tests/test_config_defaults.py` — класс `TestConfigDefaultValues`
- 16 assertions: каждая константа сверяется с исходным magic number
- pytest: все тесты зелёные

---

## Verification

```
PYTHONPATH=src compileall: OK
pytest: all passed
coverage --cov=src TOTAL: 55%  ✅ (порог ≥ 55%)
```

---

## Risks

- Нет: значения констант идентичны исходным magic numbers
- `SELECT_ACTIVE_LOST_PENALTY` переиспользован для night-source penalty (оба значения были 0.8 — намеренное совпадение)
- lock_tracker.py не тронут — нет очевидных повторяющихся числовых параметров
