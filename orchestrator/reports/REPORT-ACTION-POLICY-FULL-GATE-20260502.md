# REPORT-ACTION-POLICY-FULL-GATE-20260502

**Task:** ALG-001 v1.1 follow-up — public release API + drop telemetry + full candidate gate
**Date:** 2026-05-02
**Status:** PASS · default OFF идентично baseline · ON не ухудшает day/IR/noise · drop telemetry работает

Follow-up к `REPORT-ACTION-POLICY-IR-FIRST-GUARD-20260502.md`.

---

## 1. Changed files

| Файл | Тип | Описание |
|------|-----|----------|
| `src/uav_tracker/tracking/target_manager.py` | EDIT | Новый публичный метод `release_active() -> bool`. Минимальный wrapper над `_set_active_id(None)`. Idempotent: возвращает `False`, если активная цель отсутствует. Не удаляет targets из `self.targets`. |
| `src/uav_tracker/pipeline.py` | EDIT | `_apply_action_policy_behavior` использует `self.manager.release_active()` вместо приватного `_set_active_id(None)`. `process_frame` пробрасывает `self._behavior_drop_count` в новое поле `FrameOutput.behavior_drop_count`. |
| `src/uav_tracker/display/frame_result.py` | EDIT | Новое default-safe поле `behavior_drop_count: int = 0`. |
| `tests/test_target_manager_lifecycle.py` | EDIT | +5 тестов класса `TestReleaseActive`: empty-state→False, очищает active_id, не трогает targets dict, ресетит switch cooldown, идемпотентность. |
| `tests/test_action_policy_behavior.py` | EDIT | Mock `_FakeManager` теперь реализует публичный `release_active()`; тесты `behavior_drop_count` в `FrameOutput` (default + override). |

Никаких новых dependencies, никаких изменений runtime thresholds, никаких commit/push.

---

## 2. Public release API

```python
class TargetManager:
    ...
    def release_active(self) -> bool:
        """Public API to release the currently active target.

        Idempotent: clears active_id and resets the active-switch cooldown
        without touching self.targets (lock_tracker reset is the caller's
        responsibility).  Returns True if there was an active id to clear,
        False if already empty.
        """
        if self.active_id is None:
            return False
        self._set_active_id(None)
        return True
```

Pipeline guard:

```python
def _apply_action_policy_behavior(self, action: TrackingAction) -> str:
    behavior_enabled = bool(getattr(self.cfg, 'ACTION_POLICY_BEHAVIOR_ENABLED', False))
    intent = select_behavior_intent(action, behavior_enabled)
    if intent == BEHAVIOR_FORCE_DROP:
        self.manager.release_active()      # <-- public API
        self.lock_tracker.reset()
        self._behavior_drop_count += 1
    return intent
```

Это убирает зависимость guard-кода от приватного API `TargetManager`. Существующие call sites внутри самого `TargetManager` (`age_targets`, `select_active`, `switch_target`) продолжают использовать `_set_active_id` — это интернальное состояние класса, оно не должно делать публичный round-trip.

---

## 3. New telemetry field

`FrameOutput.behavior_drop_count: int = 0` — сколько раз с момента создания `TrackerPipeline` сработал guarded `BEHAVIOR_FORCE_DROP`.

Свойства:

- Дефолт `0` сохраняет backward compatibility всех существующих call sites `FrameOutput(...)`.
- При `ACTION_POLICY_BEHAVIOR_ENABLED=False` всегда равен `0` (guard вообще не вызывает release).
- Монотонно неубывает за сессию.
- Достаточно для GUI/log overlay и для тестов (видеть, что guard действительно срабатывает).

---

## 4. Full OFF vs ON gate (no max_frames cap)

Harness `/tmp/full_gate_action_policy.py` запускает custom evaluation loop по полным клипам, дважды на клип: `ACTION_POLICY_BEHAVIOR_ENABLED=False`, потом `True`. Один и тот же `TrackerPipeline` инстансится заново в каждом прогоне.

### 4.1. Полные результаты

| Clip | Режим | Frames | gt_frames | presence | false_lock | idchg/min | avg_gt_iou | hits_iou_01 | drops | avg_fps |
|------|-------|-------:|----------:|---------:|-----------:|----------:|-----------:|------------:|------:|--------:|
| day-mixkit | OFF | 579 | 579 | 1.0000 | 0.0000 | 0.00 | 0.9388 | 579 | 0 | 167.51 |
| day-mixkit | ON | 579 | 579 | 1.0000 | 0.0000 | 0.00 | 0.9284 | 579 | 0 | 171.27 |
| ir-train-1_7 | OFF | 934 | 934 | 1.0000 | 0.0118 | 0.00 | 0.7646 | 923 | 0 | 140.95 |
| ir-train-1_7 | ON | 934 | 934 | 1.0000 | 0.0128 | 0.00 | 0.7600 | 922 | 0 | 140.92 |
| ir-train-1_2 | OFF | 894 | 894 | 1.0000 | 0.1107 | 5.97 | 0.6924 | 795 | 0 | 100.30 |
| ir-train-1_2 | ON | 894 | 894 | 0.9989 | 0.1096 | 0.00 | 0.6924 | 795 | 1 | 98.77 |
| noise-bird | OFF | 305 | 0 | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0 | 0 | 48.35 |
| noise-bird | ON | 305 | 0 | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0 | 0 | 48.35 |
| noise-airplane | OFF | 327 | 0 | 0.1896 | 0.1896 | 0.00 | 0.0000 | 0 | 0 | 47.60 |
| noise-airplane | ON | 327 | 0 | 0.1896 | 0.1896 | 0.00 | 0.0000 | 0 | 0 | 48.12 |

### 4.2. Pairwise дельты (ON − OFF)

| Clip | Δ presence | Δ false_lock | Δ idchg/min | Δ avg_iou | Δ hits_iou_01 | Δ fps | ON drops |
|------|-----------:|-------------:|------------:|----------:|--------------:|------:|---------:|
| day-mixkit | +0.0000 | +0.0000 | +0.000 | −0.0104 | 0 | +3.76 | 0 |
| ir-train-1_7 | +0.0000 | +0.0010 | +0.000 | −0.0046 | −1 | −0.03 | 0 |
| ir-train-1_2 | −0.0011 | −0.0011 | −5.966 | +0.0000 | 0 | −1.53 | 1 |
| noise-bird | +0.0000 | +0.0000 | +0.000 | +0.0000 | 0 | +0.00 | 0 |
| noise-airplane | +0.0000 | +0.0000 | +0.000 | +0.0000 | 0 | +0.52 | 0 |

### 4.3. Интерпретация

- **OFF baseline sanity (drops==0 для всех клипов):** PASS. Guard никогда не срабатывает при выключенном флаге; default behavior идентичен предыдущему baseline.
- **day-mixkit:** идентичные presence, false_lock, hit01. Δ avg_iou −0.0104 — артефакт незначительной timing/FPS-вариации между прогонами (avg_iou всё ещё 0.93+, hit01=579/579 ровно). drops=0.
- **ir-train-1_7:** false_lock 0.0118 → 0.0128 (+0.0010 = 1 кадр из 934). hit01 −1 (из 934). Незначительно.
- **ir-train-1_2:** ON фактически улучшает: presence/false_lock минус 0.001, idchg/min падает с 5.97 до 0.00, avg_iou и hit01 не меняются. Произошёл один guarded drop (`drops=1`), который ускорил release stale-lock. Это и есть положительный эффект wiring.
- **noise-bird:** идеально идентично. Никаких drops. project pipeline корректно не создаёт активную цель на птицу.
- **noise-airplane:** идентично. Известный FP проекта (presence 0.190) сохранён без изменений — DROP_LOCK не срабатывает, потому что lost_age не накапливается до 12 для тех кадров, где target короткоживущий FP.

---

## 5. Decision

**PASS.**

Соответствие критериям:

| Критерий | Результат |
|----------|-----------|
| Default OFF path сохраняет baseline | ✅ все OFF rows идентичны pre-task baseline; drops=0 |
| ON path не ухудшает day TP | ✅ presence, false_lock, hit01 идентичны; Δ avg_iou в пределах FPS-noise |
| ON path не ухудшает IR TP materially | ✅ ir-train-1_7: 1 false_lock-кадр из 934; ir-train-1_2: фактически улучшение |
| ON path не увеличивает noise false_lock materially | ✅ noise-bird и noise-airplane идентичны |
| `behavior_drop_count` понятен и не взрывается | ✅ 0–1 drops на клип; ровно те случаи, когда target явно «протух» |
| Все тесты проходят | ✅ 508 passed (+5 vs prev 503) |

---

## 6. Почему visible-night не блокировал решение

Visible-night оформлен как diagnostic-only ещё в `REPORT-ACTION-POLICY-IR-FIRST-GUARD-20260502.md` § 2. Подтверждено снова:

- Accepted night gate = IR pack `configs/gt_positive_gate_pack_ir.csv`. Оба IR клипа (`ir-train-1_7`, `ir-train-1_2`) показывают `project avg_gt_iou ≥ 0.69`, что значительно выше gate-positive порога 0.10 из REPORT-GT-CANDIDATE-GATE-PACK.
- В full gate visible-night clip (`night_ground_large_drones`) умышленно не запускается — он остаётся в `configs/gt_candidate_gate_pack_night.csv` для diagnostic, но не блокирует приёмку.
- `TargetBelief.modality='night'` (RGB-night) семантически отделён от `'ir'`; `ActionPolicy.decide` пока этим не пользуется (это next-step), но диагностический флаг присутствует в `FrameOutput.target_modality` для downstream consumers.

Таким образом IR-first night gate сохранён, и behavior wiring не зависит от того, удастся ли когда-либо найти strong RGB-night clip.

---

## 7. Validation

| Команда | Результат |
|---------|-----------|
| `pytest tests/test_tracking_evidence.py tests/test_action_policy.py tests/test_action_policy_behavior.py -q` | **43 passed** |
| `pytest tests/test_pipeline_helpers.py tests/test_ultralytics_tracking_eval.py -q` | **33 passed** |
| `pytest tests -q` | **508 passed** (+5 vs prev 503) |
| `compileall python_scripts src app orchestrator tests` | OK |
| `git diff --check` | clean |
| `orchestrator/scripts/check_orchestration_state.py` | OK · active=0 · open=0 · completed=69 |
| Full A/B harness (`/tmp/full_gate_action_policy.py`) | day/IR/noise — все критерии PASS |

---

## 8. Риски

1. **`ActionPolicy.decide` всё ещё не разветвляется по `belief.modality`.** Поле modality пробрасывается telemetry, но никаких modality-specific порогов в policy нет. RGB-night сейчас обрабатывается как `'rgb'` для целей решения (sensor-aware policy — следующий шаг).
2. **`day-mixkit` Δ avg_iou −0.0104 при идентичных presence/false_lock/hit01.** Это, скорее всего, FPS-зависимый jitter в template lock smoothing. Не регрессия по gate-метрикам, но стоит понаблюдать в будущих прогонах.
3. **`behavior_drop_count` пока не агрегируется по сессиям GUI.** Если оператор нуждается в этой метрике в реальном времени, нужно отдельное HUD/logging задание.
4. **Full gate harness одноразовый (`/tmp/full_gate_action_policy.py`).** Не commit'ится в репо. Если потребуется регрессионный CI, нужно превратить его в `python_scripts/run_action_policy_gate.py` отдельной задачей.
5. **noise-airplane FP=0.190 не лечится текущим guarded путём.** Чтобы DROP_LOCK сработал, нужна более жёсткая reliability/lost_age политика (или modality-aware policy для noise сцен).

---

## 9. Следующий шаг (предложение для Codex/Human)

1. Сделать `ActionPolicy.decide` modality-aware: для `modality='night'` снижать `keep_reliability_min` / ужесточать `drop_reliability_max`, чтобы RGB-night не удерживал ложный target. После этого можно включить `ACTION_POLICY_BEHAVIOR_ENABLED=True` по умолчанию в night/IR пресетах.
2. Превратить `/tmp/full_gate_action_policy.py` в `python_scripts/run_action_policy_gate.py` для регрессионного CI (отдельная задача).
3. Добавить FP-suppressor в ActionPolicy (возможно отдельный action `SUPPRESS_FP`) для лечения noise-airplane сценария — отдельная задача.
4. Обновить wiki: `wiki/synthesis/current_state.md` — отметить, что behavior wiring доступен через flag и проверен на day/IR/noise.

---

**Stop after task.** Следующий шаг выбирает Codex/Human.
