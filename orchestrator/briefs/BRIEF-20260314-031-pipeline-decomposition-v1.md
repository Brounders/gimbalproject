# BRIEF-20260314-031 — TrackerPipeline Decomposition (A08)

## Проблема
`TrackerPipeline` (~600 строк в pipeline.py) нарушает SRP: 5+ concerns,
48 методов, 60+ переменных состояния. Сложность понимания и сопровождения растёт.

## Concerns для выделения
1. **Budget controller** — `_budget_level`, `_update_budget_state`, `_effective_*`
2. **Continuity metrics** — `_continuity_*`, `_update_continuity_metrics`
3. **Auto scene detection** — `_auto_scene_*`, `_adapt_auto_scene`
4. **Display / HUD state** — `_smooth_bbox`, `_reticle_*`, `_display_*`
5. **Lock event tracking** — `_update_lock_events`, `lock_event_counts`

## Подход
Stage-by-stage extraction — по одному concern за раз.
Каждый stage: выделить в отдельный класс → передать как dependency в `TrackerPipeline`.

Порядок (по убыванию риска):
1. BudgetController — чистая логика без state dependencies на другие concerns
2. ContinuityTracker — только метрики, не влияет на tracking decisions
3. AutoSceneAdapter — влияет на cfg, нужна осторожность
4. DisplayState — только render-side state

## Ограничения
- НЕ трогать `process_frame` публичный интерфейс.
- НЕ менять TargetManager, LockTracker, runtime backends.
- Каждый stage — отдельный коммит с smoke-test.
- Выполнять ПОСЛЕ A10 (тесты >30%) или одновременно с осторожностью.

## Объём
КРУПНЫЙ — 3-4 сессии. Высокий риск регрессии без тестов.

## Риск
ВЫСОКИЙ без тестового покрытия. Требует координации с Human.
