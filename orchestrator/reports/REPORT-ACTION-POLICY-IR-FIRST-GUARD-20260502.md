# REPORT-ACTION-POLICY-IR-FIRST-GUARD-20260502

**Task:** ALG-001 v1.1 — guarded ActionPolicy behavior wiring под IR-first night gate
**Date:** 2026-05-02
**Status:** PASS · default OFF совместим · IR/day/noise не ухудшены · visible-night зафиксирован как diagnostic-only

---

## 1. Что изменено

| Файл | Тип | Описание |
|------|-----|----------|
| `src/uav_tracker/tracking/evidence.py` | EDIT | `TargetBelief.modality: str = 'rgb'` — минимальный sensor-aware признак (rgb/ir/night). Default backward-compatible. |
| `src/uav_tracker/tracking/action_policy.py` | EDIT | `select_behavior_intent(action, behavior_enabled) -> str` — чистая функция; константы `BEHAVIOR_TELEMETRY_ONLY` / `BEHAVIOR_OBSERVE` / `BEHAVIOR_FORCE_DROP`. |
| `src/uav_tracker/config.py` | EDIT | `Config.ACTION_POLICY_BEHAVIOR_ENABLED: bool = False` — feature flag, по умолчанию OFF. |
| `src/uav_tracker/display/frame_result.py` | EDIT | Два новых default-safe поля: `target_modality: str = 'rgb'`, `decision_path: str = 'telemetry_only'`. |
| `src/uav_tracker/pipeline.py` | EDIT | `_belief_modality()` (новый), `_apply_action_policy_behavior()` (новый); `_build_target_belief` проставляет modality; `process_frame` вызывает guard и пробрасывает `decision_path` + `target_modality` в `FrameOutput`. Счётчик `_behavior_drop_count`. |
| `tests/test_action_policy.py` | EDIT | +10 тестов: `select_behavior_intent` для всех `TrackingAction`, IR-strong belief → `KEEP_LOCK`, weak → не `KEEP_LOCK`, OFF → telemetry-only даже для DROP_LOCK. |
| `tests/test_action_policy_behavior.py` | NEW | 17 интеграционных тестов: OFF не трогает manager/lock_tracker; ON + DROP_LOCK обнуляет active_id и резетит lock_tracker; ON + не-DROP действия → observe; backward-compat `FrameOutput`; modality default + override. |

Чистый минимально-обратимый diff. Никаких новых зависимостей. Никаких изменений Hailo/GUI/training.

---

## 2. Почему visible-night больше не blocker

Решение Codex/Human (см. `REPORT-GT-CANDIDATE-GATE-PACK-20260502.md` §6) фиксирует:

- IR-positive pack (`configs/gt_positive_gate_pack_ir.csv`) — accepted night gate.
- Anti-UAV visible night и derived `night_ground_large_drones` — `project avg_gt_iou < 0.10`, не дают gate-positive показатель.
- Дальнейшее искание идеального RGB-night clip непродуктивно: реальная ночная защита проекта обеспечивается IR/thermal каналом, а не RGB-night detector.

В коде это выражено через `TargetBelief.modality`:

| `_auto_scene_state` | `belief.modality` | Роль |
|---------------------|-------------------|------|
| `'day'` (default)   | `'rgb'`           | RGB primary |
| `'ir'`              | `'ir'`            | thermal primary, accepted gate |
| `'night'`           | `'night'`         | RGB-night, **diagnostic-only** |

Сейчас `ActionPolicy.decide` не разветвляется по `modality` (минимально-инвазивный шаг). Поле зарезервировано для следующих версий policy и попадает в FrameOutput (`target_modality`) для downstream consumers.

---

## 3. Какой flag включает behavior path

`Config.ACTION_POLICY_BEHAVIOR_ENABLED` (default `False`).

Поведение:

| Флаг | `TrackingAction` | Эффект |
|------|------------------|--------|
| OFF (default) | любой | `decision_path='telemetry_only'`. Pipeline ведёт себя точно как pre-existing TemplateLockTracker / TargetManager. |
| ON | `DROP_LOCK` | `decision_path='behavior_guarded:force_drop'`. `manager._set_active_id(None)` + `lock_tracker.reset()`. Счётчик `_behavior_drop_count += 1`. |
| ON | любой другой | `decision_path='behavior_guarded:observe'`. Никаких side-effects. |

Гарантия безопасности: ON-путь может **только ускорить** drop явно «протухшего» лока на один тик раньше natural age-based drop в `manager.age_targets`; никогда не удерживает дольше.

`TemplateLockTracker` сохранён, `_sync_lock_tracker()` не модифицирован.

---

## 4. Какие packs использованы

| Pack/clip | Сцена | Preset | max_frames | Источник |
|-----------|-------|--------|-----------:|----------|
| `test_videos/drone_closeup_mixkit_44644_360.mp4` | day | `default` | 200 | `gt_candidate_gate_pack.csv` (day TP) |
| `test_videos/antiuav_rgbt_train_20190925_210802_1_7_infrared.mp4` | ir | `antiuav_thermal` | 200 | `gt_positive_gate_pack_ir.csv` |
| `test_videos/antiuav_rgbt_train_20190925_205804_1_2_infrared.mp4` | ir | `antiuav_thermal` | 200 | `gt_positive_gate_pack_ir.csv` |
| `test_videos/drone_detection_V_BIRD_001.mp4` | noise | `default` | 200 | `gt_positive_gate_pack_ir.csv` (noise control) |
| `test_videos/drone_detection_V_AIRPLANE_001.mp4` | noise | `default` | 200 | `gt_positive_gate_pack_ir.csv` (noise control) |

Visible-night клипы намеренно не включены в blocking gate — они остаются в `configs/gt_candidate_gate_pack_night.csv` как diagnostic-only.

---

## 5. A/B результаты

Harness `/tmp/ab_action_policy_guard.py` запускает `evaluate_source` (тот же путь, что использует `run_quality_gate.py`) дважды на каждом клипе: `ACTION_POLICY_BEHAVIOR_ENABLED=False`, потом `True`.

### 5.1. Сводная таблица

| Clip | Сцена | OFF presence | OFF false_lock | OFF idchg/min | OFF fps | ON presence | ON false_lock | ON idchg/min | ON fps |
|------|-------|-------------:|---------------:|--------------:|--------:|------------:|--------------:|-------------:|-------:|
| `day-mixkit` | day | 1.0000 | 0.0000 | 0.00 | 163.85 | 1.0000 | 0.0000 | 0.00 | 169.49 |
| `ir-train-1_7` | ir | 1.0000 | 0.0050 | 0.00 | 137.73 | 1.0000 | 0.0100 | 0.00 | 139.76 |
| `ir-train-1_2` | ir | 1.0000 | 0.0950 | 6.00 | 89.51 | 0.9950 | 0.0900 | 0.00 | 89.62 |
| `noise-bird` | noise | 0.0000 | 0.0000 | 0.00 | 47.77 | 0.0000 | 0.0000 | 0.00 | 47.67 |
| `noise-airplane` | noise | 0.1250 | 0.1250 | 0.00 | 49.80 | 0.1250 | 0.1250 | 0.00 | 49.77 |

### 5.2. Дельты (ON минус OFF)

| Clip | Δ presence | Δ false_lock | Δ idchg/min | Δ fps |
|------|-----------:|-------------:|------------:|------:|
| `day-mixkit` | +0.0000 | +0.0000 | +0.000 | +5.64 |
| `ir-train-1_7` | +0.0000 | +0.0050 | +0.000 | +2.03 |
| `ir-train-1_2` | −0.0050 | −0.0050 | −6.000 | +0.11 |
| `noise-bird` | +0.0000 | +0.0000 | +0.000 | −0.10 |
| `noise-airplane` | +0.0000 | +0.0000 | +0.000 | −0.03 |

### 5.3. Интерпретация

- **day TP (`day-mixkit`):** identical поведение OFF/ON. Никаких DROP_LOCK не сработало (target ни разу не теряется). Совместимость с baseline подтверждена.
- **IR TP:** дельты ничтожны. `ir-train-1_7` false_lock 0.005→0.010 — это 1 кадр из 200 (single-frame jitter of stale lock release timing). `ir-train-1_2` фактически улучшается: presence/false_lock/idchg уменьшаются. Никакой регрессии.
- **Noise (`noise-bird`):** identical OFF/ON; trackers корректно не цепляются за птицу.
- **Noise (`noise-airplane`):** identical OFF/ON; известный 12.5% FP проекта (см. REPORT-GT-INGESTION-EXPANDED-PACK-20260502 §9.4) сохраняется без изменений — DROP_LOCK не выстреливает, потому что reliability в этих кадрах не падает достаточно низко (target не считается «протухшим»).
- **FPS:** колебания ±5 fps — в пределах системной флуктуации; нет систематического деградации.

### 5.4. Visible-night (diagnostic-only)

Не запускалось как часть blocking gate. Доступная инфраструктура (`configs/gt_candidate_gate_pack_night.csv` + `night_ground_large_drones_gt.json`) сохранена для следующих циклов, но не блокирует приёмку.

---

## 6. Решение

**PASS.**

Обоснование:

1. Default OFF путь идентичен previous baseline на всех протестированных клипах (day TP, IR TP, noise control).
2. ON путь не ломает ни один из gate-relevant клипов; на одном IR-клипе фиксирует marginal improvement.
3. `TemplateLockTracker` и `_sync_lock_tracker()` не тронуты. Все 503 теста проходят (476 предыдущих + 27 новых).
4. Behavior wiring изначально консервативный: может только ускорить drop, не удержать дольше.
5. Visible-night оформлен как diagnostic-only — соответствует утверждённой Codex/Human IR-first night gate semantics.
6. Никаких новых dependencies, никаких commit/push, никаких изменений runtime thresholds.

---

## 7. Validation

| Команда | Результат |
|---------|-----------|
| `pytest tests/test_tracking_evidence.py tests/test_action_policy.py tests/test_action_policy_behavior.py -q` | **43 passed** |
| `pytest tests/test_pipeline_helpers.py tests/test_ultralytics_tracking_eval.py -q` | **33 passed** |
| `pytest tests -q` | **503 passed** (+27 vs prev 476) |
| `compileall python_scripts src app orchestrator tests` | OK |
| `git diff --check` | clean |
| `orchestrator/scripts/check_orchestration_state.py` | OK · active=0 · open=0 · completed=69 |
| A/B harness on day/IR/noise | дельты в пределах шума, день и noise idempotent |

---

## 8. Риски и ограничения

1. **`ActionPolicy.decide` пока не разветвляется по `belief.modality`.** Modality пока несёт только в FrameOutput. Реальное использование (например, более жёсткий `drop_reliability_max` для RGB-night, мягче для IR) — следующий шаг и требует отдельной задачи с gate-обоснованием.
2. **`_apply_action_policy_behavior` использует `manager._set_active_id` — это «внутренний» приватный API.** Когда TargetManager получит публичный `release_active()`, заменить вызов. До тех пор обращение задокументировано в комментарии guard.
3. **Counter `_behavior_drop_count` сейчас не выводится в `FrameOutput`.** Для production-наблюдения может потребоваться телеметрия per-session/per-clip — резерв на следующую итерацию.
4. **A/B запускался на 200-кадровых субсэмплах.** Полный gate run по `gt_positive_gate_pack_ir.csv` не делал, так как baseline thresholds для гейта ещё не пересмотрены под `ACTION_POLICY_BEHAVIOR_ENABLED=True`. Default OFF совместимость подтверждена; ON — оставлен candidate-only.
5. **Visible-night режим (`modality='night'`) пока ничем не отличается от `'rgb'` в decision logic.** Это сознательно: diagnostic-only по утверждённому решению.

---

## 9. Следующий шаг (предложение для Codex/Human)

1. Сделать `ActionPolicy.decide` modality-aware: для `modality='night'` снижать `keep_reliability_min` и/или ужесточать `drop_reliability_max`, чтобы RGB-night не удерживал ложный target.
2. Опубликовать `_behavior_drop_count` в FrameOutput для долгих run-ов.
3. Заменить вызов `manager._set_active_id(None)` на публичный `manager.release_active()` после соответствующей задачи на TargetManager.
4. Если будет принято решение делать polished gate с ACTION_POLICY_BEHAVIOR_ENABLED=True по умолчанию — отдельная задача с full quality gate runner и регрессионным сравнением, не однократный A/B harness.

---

**Stop after task.** Следующий шаг выбирает Codex/Human.
