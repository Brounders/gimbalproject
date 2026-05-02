# REPORT-ALGO-EVIDENCE-V1-20260501

**Task:** TASK-20260501-ALG001-EVIDENCE-POLICY-V1
**Date:** 2026-05-01
**Status:** Implemented · all validation green · awaiting review

---

## 1. Цель

Ввести архитектурный слой v1 detection-first трекинга:
`proposal sources → evidence fusion → target belief → action policy`,
не меняя текущее runtime-поведение и не ломая night gate.

## 2. Что изменено

| Файл | Тип | Описание |
|------|-----|----------|
| `src/uav_tracker/tracking/evidence.py` | NEW | `TargetEvidence`, `TargetBelief`, `compute_total_score`, `SOURCE_RELIABILITY` |
| `src/uav_tracker/tracking/action_policy.py` | NEW | `TrackingAction` enum, `ActionPolicy` |
| `src/uav_tracker/pipeline.py` | EDIT | импорт нового слоя; `ActionPolicy` инстанс; helper `_build_target_belief()`; вызов `decide()` после `select_active`; пробрасывание трёх telemetry-полей в `FrameOutput` |
| `src/uav_tracker/display/frame_result.py` | EDIT | три новых поля с дефолтами: `target_reliability`, `target_p_present`, `tracking_action` |
| `tests/test_tracking_evidence.py` | NEW | 8 тестов: clamp, ranking, defaults |
| `tests/test_action_policy.py` | NEW | 8 тестов: GLOBAL_RESCAN/KEEP_LOCK/LOCAL_VALIDATE/EXPAND_ROI/DROP_LOCK/REDETECT/детерминированность |

## 3. Что НЕ изменено

- `TargetManager`, `LockTracker`, `NightDetector`, `MotionROIProposer`, `BudgetController` — без правок.
- `TemplateLockTracker` сохранён.
- Native ByteTrack/BoT-SORT не подключался.
- Никаких изменений `LOCK_TRACKER_MIN_SCORE`, `LOCK_CONFIRM_FRAMES`, `LOCK_LOST_GRACE`, `DRONE_LOCK_SCORE_MIN` и других runtime thresholds.
- Никаких новых ключей в `Config` (пороги полиси заданы как поля dataclass `ActionPolicy` и не задеваются preset’ами).
- Поведение `_sync_lock_tracker()` оставлено как есть (gated template update отложен — требует gate подтверждения).
- GUI не менялся.
- Никаких новых зависимостей.

## 4. Новые сущности

### `TargetEvidence`
- `source`, `bbox`, `track_id`, `cls_id`, `conf`
- score components в [0,1]: `detector_score`, `motion_score`, `appearance_score`, `trajectory_score`, `scale_score`
- `source_reliability` (через `SOURCE_RELIABILITY`: `yolo=1.00`, `local=0.85`, `roi=0.70`, `lock=0.50`, `night=0.40`)
- computed `total_score` — взвешенная сумма (`0.40·detector + 0.20·appearance + 0.15·trajectory + 0.15·motion + 0.10·scale`), масштабируемая `source_reliability`, clamp в [0,1].

### `TargetBelief`
- `active_id`, `bbox`, `last_good_bbox`, `velocity`, `scale`
- `p_present`, `p_same_target`, `reliability`, `lost_age`, `source`
- factory `TargetBelief.empty()` для случая без активной цели.

### `TrackingAction`
- enum: `KEEP_LOCK`, `LOCAL_VALIDATE`, `EXPAND_ROI`, `GLOBAL_RESCAN`, `REDETECT`, `DROP_LOCK`.

### `ActionPolicy`
- детерминированные пороги (поля dataclass), без ML и случайности.
- defaults: `keep_reliability_min=0.60`, `keep_lost_age_max=2`, `validate_reliability_min=0.30`, `validate_lock_score_max=0.55`, `expand_lost_age_max=8`, `rescan_lost_age_min=9`, `drop_reliability_max=0.10`, `drop_lost_age_min=12`.

## 5. Как pipeline теперь принимает решение

В `process_frame()` после `manager.select_active()` и до `_sync_lock_tracker()`:

1. `_build_target_belief(lock_score)` собирает `TargetBelief` из активной цели (`source`, `conf`, `drone_score`, `hit_streak`, `lost_frames`, `vx/vy`, `lock_score`).
2. `action_policy.decide(belief, lock_score, needs_recovery=lock_tracker.needs_recovery)` возвращает `TrackingAction`.
3. `belief` и `action` сохраняются в `self._last_belief` / `self._last_action` и пробрасываются в `FrameOutput` как `target_reliability`, `target_p_present`, `tracking_action`.

**Ключевое:** decision telemetry-only — никакие ветки `if/else` в `process_frame()` не реагируют на `action`. Текущее поведение полностью сохранено.

Reliability формула:
```
reliability = lost_decay · (
    0.40·source_rel + 0.20·conf + 0.15·drone_score + 0.15·streak_factor + 0.10·lock_score
)
streak_factor = min(1, hit_streak / LOCK_CONFIRM_FRAMES)
lost_decay    = max(0, 1 - lost_frames / YOLO_LOST_MAX)
```

## 6. Validation

| Команда | Результат |
|---------|-----------|
| `pytest tests/test_tracking_evidence.py tests/test_action_policy.py -q` | 16 passed |
| `pytest tests/test_ultralytics_tracking_eval.py -q` | 5 passed |
| `pytest tests -q` | **466 passed** |
| `compileall python_scripts src app orchestrator tests` | OK |
| `orchestrator/scripts/check_orchestration_state.py` | `orchestrator_state_check=OK`; active=0, open=0, completed=69 |

## 7. Gate result

Quality gate **не запускался**: behavior не изменён, runtime thresholds не тронуты. Запуск gate не входит в acceptance этой задачи (он требуется только при behavior change).

## 8. Риски

- **Низкий — поведенческий регресс.** Telemetry-only добавление: исключений в `process_frame()` нет, существующие тесты (446) остались зелёными.
- **Низкий — backward compatibility FrameOutput.** Новые поля имеют defaults, существующие call-сайты не сломались.
- **Средний — drift heuristics в `_build_target_belief()`.** Формула reliability эвристическая; пороги `ActionPolicy` подобраны без эмпирической валидации. Это допустимо, пока решение telemetry-only, но **запрещено превращать `tracking_action` в управляющий сигнал без gate**.
- **Низкий — circular imports.** Helper построения belief живёт в `pipeline.py`; `evidence.py` не импортирует ни pipeline, ни target_manager.

## 9. Что осталось на следующий task

1. **Behavior wiring** — привязать `TrackingAction` к ветвлениям `process_frame()` (например, `KEEP_LOCK` → пропуск `LOCAL_VALIDATE`; `EXPAND_ROI` → расширение `_build_focus_roi()`). Должно идти под gate.
2. **Gated template update** — обновлять `lock_tracker.sync_from_bbox` только если `belief.reliability >= threshold`. Требует gate.
3. **Эмпирическая калибровка порогов `ActionPolicy`** — на ночных и IR клипах; может потребовать запись `tracking_action` в overlay/CSV для анализа.
4. **`focus_roi.py`** — выделение `_build_focus_roi()` в отдельный модуль; в этой задаче не сделано, чтобы не раздувать diff.
5. **Evidence fusion на стороне `TargetManager`** — сейчас `TargetEvidence` определена, но не строится в pipeline; следующий шаг — собирать evidence из YOLO/ROI/LOCK/NIGHT детекций и использовать для `select_active`.
6. **Codex reports** — `REPORT-MODERNITY-GAP-20260501.md` и `REPORT-BYTETRACK-EVAL-20260501.md` присутствуют в main workspace после интеграции; они остаются источниками для следующего behavior task.

---

**Stop after task.** Следующий шаг выбирает Codex/Human.
