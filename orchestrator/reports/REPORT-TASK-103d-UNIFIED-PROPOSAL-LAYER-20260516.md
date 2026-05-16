# REPORT — TASK-103d: Unified Proposal Layer

**Date:** 2026-05-16  
**Commit:** `00eeac2`  
**Status:** ✅ PASS

---

## Что сделано

1. **`src/uav_tracker/tracking/proposal_trust.py`** (новый файл)
   - `Proposal` dataclass: target_id, bbox, source, conf, drone_score, hit_streak, lost_frames, trust, geo_score, total_score
   - `SCENE_TRUST` таблица из 17 пар (source, scene) → float, откалибрована по F5-данным:
     - night/ir=0.92, yolo/ir=0.30, lock/ir=0.38, operator/any=1.00
     - yolo/day=0.85, night/day=0.15
     - night/night=0.90, yolo/night=0.70
   - `DEFAULT_TRUST=0.50` для неизвестных пар
   - `build_proposals(targets, scene, normalize_fn)` → список `Proposal`, отсортированный по `total_score` desc

2. **`src/uav_tracker/tracking/target_manager.py`**
   - Добавлен метод `pick_active_by_trust(scene='day')`
   - Защита от осцилляции: `TRUST_SWITCH_MARGIN` (по умолчанию 0.25 = 25% преимущество требуется)
   - Уважает `ACTIVE_STRICT_LOCK_SWITCH` и `is_focus_mode()`

3. **`src/uav_tracker/pipeline.py`**
   - После `select_active()` добавлен вызов `pick_active_by_trust(scene=_auto_scene_state)`

4. **`src/uav_tracker/config.py`**
   - `TRUST_SWITCH_MARGIN: float = 0.25`

5. **`tests/test_proposal_trust.py`** (14 тестов)

---

## Результаты тестов

- `pytest tests/test_proposal_trust.py`: **14/14 pass**
- `pytest tests/`: **857 passed, 1 pre-existing fail** (test_target_lab_bridge — не наш)

---

## A/B vs baseline (diag_pack_v1_20260516_155830)

| Clip | Scene | Baseline | 103d | Delta |
|---|---|---|---|---|
| antiuav_rgbt_train_20190925 | IR | 0.412 | **0.896** | **+0.484** ✅ |
| 2023-11-23 14-56-24 | UNKNOWN | 0.000 | **0.164** | +0.164 ✅ |
| f2_13_IR_dji_mavic_2 | IR | 0.677 | **0.685** | +0.008 ✅ |
| 5_minie3_range_far | IR | 0.875 | **0.879** | +0.004 ✅ |
| 7_minie5_range_all_cut_blur | EO | 0.599 | 0.599 | 0 |
| IR_DRONE_025 | IR | 0.987 | 0.987 | 0 |
| 1_minie3_range_close | IR | 0.000 | 0.000 | 0 (hard clip) |

**Регрессий нет.** Основное улучшение — RGBT infrared clip: night-source правильно повышается до активного на IR-сцене (trust=0.92 vs yolo trust=0.30).

---

## Риски

- `1_minie3_range_close` — recall=0.000, 471/477 кадров off-target. Проблема не в proposal layer (night trust=0.92 correct), а в отсутствии детекций ночным детектором на этом клипе. Нужен TASK-103e (verification gate) или улучшение night detector.
- `f2_13_IR_dji_mavic_2` — p99=269ms (высокая латентность). Не связано с 103d.

---

## Что осталось (план 103-series)

- [x] 103a — GT diagnostic pack
- [x] 103b — BBox stability layer
- [x] 103c — Auto-scene-detect v2
- [x] 103d — Unified Proposal Layer ← **выполнено**
- [ ] 103e — Verification gate (SEARCH→CANDIDATE→VERIFY→TRACK→WEAK→LOST_HOLD)
- [ ] 103f — lock_tracker multi-scale (conditional)
- [x] 103g — CLOSED (latency scheduler, не нужен)
- [ ] 103h — Targeted training (conditional)

**План выполнен на 62.5% (5 из 8 этапов, 103g закрыт как N/A)**
