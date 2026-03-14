# REPORT-20260314-089 — A08 TrackerPipeline Decomposition

Date: 2026-03-14
Branch: agent-team/2026-03-14-quick-wins
Status: Done — все 4 stage выполнены

---

## Что сделано

### Stage 1 — BudgetController (коммит d3fa404)
- Создан `src/uav_tracker/budget_controller.py`
- Извлечены: EMA нагрузки, level 0–max, effective_*_interval(), should_run_*()
- Удалены: `_update_budget_state()` + 6 `_effective_*` методов из pipeline
- Заменены: 10 переменных состояния → `self.budget`

### Stage 2 — TrackingStateMachine (коммит d31441d)
- Создан `src/uav_tracker/tracking_state_machine.py`
- SCAN/TRACK/LOST FSM с display-state hold для подавления visual flicker
- Удалены: `_update_tracking_state()`, `_get_display_tracking_state()`
- Заменены: 5 переменных → `self.tracking_sm`

### Stage 3 — (нет отдельного stage; ContinuityTracker был готов ранее)

### Stage 4 — DisplayStateTracker (коммит d1506a8)
- Создан `src/uav_tracker/display_state_tracker.py`
- update_confidence() — EMA с периодическим обновлением
- update_reticle() — EMA центра прицела с hold-frames
- update_smooth_bbox() — EMA bbox с size/pos разными alpha
- Удалены: `_instant_tracking_confidence()`, `_update_display_confidence()`,
  `_update_reticle_center()`, `_get_smooth_display_bbox()`
- Заменены: 7 переменных → `self.display_state`

---

## Итого (A08 полностью)

| Метрика | До | После |
|---------|-----|-------|
| Extracted classes | 0 | 4 (Budget, Continuity, TrackingSM, DisplayState) |
| Методы удалены из pipeline | — | ~18 |
| Переменные состояния удалены | — | ~22 |
| Новые файлы | — | 4 |

---

## Что проверено

- `python3 -m compileall -q src app python_scripts` — OK
- `python3 -m unittest discover -s tests -q` — 15/15 OK
- Smoke-import: `TrackerPipeline(Config()).budget.level == 0` ✓
- `TrackerPipeline(Config()).tracking_sm.state == 'SCAN'` ✓
- `TrackerPipeline(Config()).display_state` инстанциируется ✓

---

## Что осталось (не в этом plan)

| ID | Описание |
|----|----------|
| BRIEF-031 | AutoSceneAdapter — отдельный класс (сложно: мутирует cfg) |
| A10 | Тесты >30% |
| BRIEF-030 | Config nested groups (breaking API) |
| BRIEF-033 | Training strategy reset |

---

## Риски

- AutoSceneAdapter НЕ извлечён — он мутирует `self.cfg` напрямую.
  Экстракция требует либо callback-паттерн, либо изменение API Config.
  Оставлено на BRIEF-031.
- Тесты не покрывают BudgetController/ContinuityTracker/TrackingStateMachine/DisplayStateTracker.
  Риск регресса при дальнейших изменениях.
