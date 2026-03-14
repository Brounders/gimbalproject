# REPORT: IR Runtime Hardening v2 — track_state_lost_frames sweep

Date: 2026-03-14
Status: Done — null result, runtime lever exhausted
Type: YAML tuning + evidence. No training changes.

---

## Гипотеза

IR hardening v1 (lock policy layer) не дал эффекта. Выдвинута гипотеза:
root cause — YOLO детекции нестабильны → трек уходит в LOST → SCAN → новый ID (track reset).
Единственный runtime lever: увеличить `track_state_lost_frames`, чтобы трек держался дольше
и reacquire происходил до его терминации.

Если детекционные пропуски <= N кадров → увеличение до N уберёт track resets.

---

## Тест 1: track_state_lost_frames = 12 (default=8)

| Clip | false_lock | id_chg/min | vs baseline |
|------|-----------|------------|-------------|
| Demo_IR_DRONE_146 | 0.840 | **63.26** | без изменений |
| IR_DRONE_001 | 0.784 | 5.98 | без изменений |
| IR_BIRD_001 | 0.090 | 0.00 | без изменений |

Gate report: `runs/evaluations/quality_gate/ir_lost_frames_12quality_gate_antiuav_thermal.json`

---

## Тест 2: track_state_lost_frames = 16 (default=8)

| Clip | false_lock | id_chg/min | vs baseline |
|------|-----------|------------|-------------|
| Demo_IR_DRONE_146 | 0.840 | **63.26** | без изменений |
| IR_DRONE_001 | 0.784 | 5.98 | без изменений |
| IR_BIRD_001 | 0.090 | 0.00 | без изменений |

Gate report: `runs/evaluations/quality_gate/ir_lost_frames_16quality_gate_antiuav_thermal.json`

---

## Root Cause — Окончательный вывод

`track_state_lost_frames=16` при 22fps = ~0.73 сек паузы без обнаружения.
id_chg=63.26/min = ~1.05 смены ID в секунду → детекционные пропуски происходят быстрее
(трек успевает перейти в LOST и SCAN быстрее, чем восстановление).

**Вывод: детекционные пропуски на Demo_IR_DRONE_146 длиннее 16 кадров (~0.73 сек).**
YOLO модель фундаментально нестабильна на этом IR-клипе при conf_thresh=0.12.

Все runtime levers испытаны и исчерпаны:
- Lock policy layer (v1): 0 эффекта
- Track persistence (v2): 0 эффекта при lost_frames=8→12→16

---

## Решение

`track_state_lost_frames` удалён из antiuav_thermal.yaml (значения тестировались,
остался только комментарий для governance-документации).

**Единственный путь к улучшению IR id_chg: IR-специализированная модель.**

---

## Итог по IR runtime levers

| Lever | Тест | Результат |
|-------|------|-----------|
| active_id_switch_cooldown_frames | 30→60 (v1) | 0 эффекта |
| track_state_acquire_frames | 3→4 (v1) | 0 эффекта |
| lock_mode_acquire_frames | 2→3 (v1) | 0 эффекта |
| active_id_switch_allow_if_lost_frames | 6→12 (v1) | 0 эффекта |
| track_state_lost_frames | 8→12 (v2) | 0 эффекта |
| track_state_lost_frames | 8→16 (v2) | 0 эффекта |

**Runtime lever space исчерпан. Следующий шаг — обучение ir_model.pt.**
