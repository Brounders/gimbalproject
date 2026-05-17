# REPORT — TASK-20260516-103: Act5 Universal Selector & Reacquire — FINAL

**Date:** 2026-05-16  
**Status:** ✅ CLOSED (103a–103e выполнены; 103f conditional — ждёт директивы)

---

## Итог серии 103

| Этап | Задача | Статус | Ключевой результат |
|---|---|---|---|
| 103a | GT diagnostic pack | ✅ DONE | 14-клиповый minipack, baseline metrics |
| 103b | BBox stability layer | ✅ DONE | Стабилизация bbox между кадрами |
| 103c | Auto-scene-detect v2 | ✅ DONE | IR/EO/night автодетект по frame content |
| 103d | Unified Proposal Layer | ✅ DONE | SCENE_TRUST таблица, pick_active_by_trust |
| 103e | Lock Health Release Gate | ✅ DONE | _low_trust_streak, last-resort release |
| 103f | lock_tracker multi-scale | ⏸ CONDITIONAL | Scope не задан; нужна директива |
| 103g | Latency scheduler | ✅ CLOSED N/A | Не нужен |
| 103h | Targeted training | ⏸ CONDITIONAL | После решения по 103f/100 |

---

## A/B Gate — 103e vs 103d stable baseline

| Clip | Scene | 103d stable | 103e | Delta |
|---|---|---|---|---|
| 1_minie3_range_close | IR | 0.000 | 0.000 | 0 |
| 2023-11-23 14-56-24 | UNKNOWN | 0.164 | 0.164 | 0 |
| 2_minie3_range_medium_close_birds | EO_NEG | 0.946 | 0.946 | 0 |
| 5_minie3_range_far | IR | 0.879 | 0.879 | 0 |
| 7_minie5_range_all_cut_blur | EO | 0.599 | 0.599 | 0 |
| 9_dji2_range_medium | IR | 0.276 | 0.276 | 0 |
| IR_AIRPLANE_003 | IR_NEG | 0.000 | 0.000 | 0 |
| IR_AIRPLANE_014 | IR_NEG | 0.000 | 0.000 | 0 |
| IR_DRONE_025 | IR | 0.987 | 0.987 | 0 |
| V_BIRD_030 | NEG | 0.000 | 0.000 | 0 |
| antiuav_rgbt_20190925 | IR | 0.000 | 0.000 | 0 |
| antiuav_rgbt_train | IR | 0.412 | 0.412 | 0 |
| f1_3_EO_dji_mavic_2_occlusion_far | EO | 0.000 | 0.000 | 0 |
| f2_13_IR_dji_mavic_2 | IR | 0.685 | 0.685 | 0 |

**Регрессий нет. 103e — чистый safety valve без побочных эффектов.**

> Примечание: 103d baseline = 0.412 (стабильный). Значение 0.896 из первого 103d прогона — нерепродуцируемая флюктуация MOG2-инициализации при IR auto-scene.

---

## Анализ оставшихся слабых мест

### Off-target (lock захватывает фон)
| Clip | Off-target frames | Потенциальный fix |
|---|---|---|
| 1_minie3_range_close | 471/477 | 103f multi-scale или улучшение детектора |
| antiuav_rgbt_20190925 | 933/933 | 103f или 103h (ночной детектор) |
| antiuav_rgbt_train | 515/874 | 103f или 103h |
| 2023-11-23 14-56-24 | 1262/1669 | Сцена UNKNOWN — нет GT-сцены |

### Missed detection (YOLO/ночной детектор не видит)
| Clip | Missed frames | Потенциальный fix |
|---|---|---|
| 9_dji2_range_medium | 521/757 | 103h targeted training |
| 7_minie5_range_all_cut_blur | 437/1172 | 103h или augmentation |
| f1_3_EO_dji_mavic_2_occlusion_far | 314/379 | Окклюзия — сложно без данных |

---

## Рекомендация

**103f (lock_tracker multi-scale)** релевантна для off-target группы но:
- Требует детального анализа lock_tracker.py
- Эффект ограничен IR-клипами с ночным детектором
- Без scope — реализовывать нельзя

**Следующий шаг:** TASK-20260516-100 (candidate-training return gate) — диагностика достаточно зрелая для решения о сборе DTS-данных или сравнении YOLO26.

---

## Принятые отчёты серии 103

- `REPORT-TASK-103d-UNIFIED-PROPOSAL-LAYER-20260516.md`
- `REPORT-TASK-103e-LOCK-HEALTH-GATE-20260516.md`
- `REPORT-TASK-103-ACT5-FINAL-20260516.md` ← этот
