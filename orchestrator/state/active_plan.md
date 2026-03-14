# Active Plan

## Plan ID
- AP-20260314-027

## Source Direction
- Human approved full tech-debt closure (excluding Hailo) on 2026-03-14.
- Scope: все аудитные задачи A01-A09, A12, day gate fix, новая training стратегия.
- A10 (тесты >30%) — условный: выполнить только после уверенности в успехе.
- Hailo (A04) — исключён явно.

## Status
- In Progress

## Phase 1 — Стабилизация (текущая)
- [x] A02: print() → logging в run_tracker (agent-team ветка)
- [x] A05: _iou() → utils/geometry.py (agent-team ветка)
- [x] A11: try/except в UltralyticsBackend (agent-team ветка)
- [x] baseline.pt установлен (drone_bird_probe_fast, 2026-03-14)
- [ ] A01: Race condition — threading.Event в TrackerWorker и EvaluationWorker
- [ ] A03: Circular import — перенести overlay import в начало pipeline.py
- [ ] A12: Magic numbers → Config (NIGHT_MOG2_HISTORY, NIGHT_MOG2_VAR_THRESH, NIGHT_GRID_CELL)

## Phase 2 — Day Gate Diagnosis
- [ ] Диагностика: почему false_lock=1.000 на day клипах для всех моделей
- [ ] Исправление структурной проблемы day gate

## Phase 3 — Документация
- [ ] A06: Docstrings на TrackerPipeline и публичных методах

## Phase 4 — Архитектура (отдельные briefs)
- [ ] A09: Config 122 полей → nested groups (отдельный brief, ломает публичный API)
- [ ] A08: TrackerPipeline decomposition SRP (отдельный brief, после A10 или параллельно с осторожностью)

## Phase 5 — Алгоритмика
- [x] A07: Kalman vs EMA — решение принято: ОСТАВИТЬ EMA (BRIEF-20260314-032)
      Обоснование: все провалы gate были на уровне детектора, не prediction.
      Калман не измерим через текущий gate и рискует регрессией на ночи.

## Phase 6 — Training стратегия
- [x] Корневая причина задокументирована: drone-bird-yolo не имеет night visible-light данных
- [x] Brief написан: BRIEF-20260314-033 — шаги до следующего обучения
- [ ] Шаг 1: Аудит датасета — отдельный Plan (следующая сессия)
- [ ] Шаг 4-5: Новый training brief после аудита

## Phase 7 — Тесты (условная)
- [ ] A10: Покрытие тестами >30% — только после уверенности в успехе

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [ ] Все фазы 1-6 завершены и приняты
- [ ] Каждая фаза задокументирована отчётом в orchestrator/reports
- [ ] Smoke-test проходит после каждой фазы
