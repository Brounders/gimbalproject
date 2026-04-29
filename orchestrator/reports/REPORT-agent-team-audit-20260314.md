# СВОДНЫЙ ОТЧЁТ АУДИТА — Agent Team, 2026-03-14

Вердикт: ОДОБРЕНО С ЗАМЕЧАНИЯМИ (85% production-ready)

## P0 — КРИТИЧНО

| ID | Проблема | Файл | Рекомендация |
|----|----------|------|--------------|
| A01 | Race condition в TrackerWorker — флаги без синхронизации между QThread и основным потоком | app/main_gui.py:74-75, 104, 107 | QMutex или threading.Event |
| A02 | print() вместо logging — diagnostic output неуправляем | pipeline.py:1003, 1032, 1045, 1052-1066 | import logging, заменить все print() |

## P1 — ВАЖНО

| ID | Проблема | Файл |
|----|----------|------|
| A03 | Циклический импорт обходится через конец файла | pipeline.py:973 |
| A04 | HailoBackend — только заглушка | runtime/hailo_backend.py:17-27 |
| A05 | _iou() дублируется в 3 местах | pipeline.py:139, target_manager.py:387, roi_assist.py:59 |
| A06 | Нет docstrings на TrackerPipeline (600+ строк) | pipeline.py |
| A07 | Нет Фильтра Калмана — EMA + линейная экстраполяция | target_manager.py:259-273 |

## P2 — ТЕХДОЛГ

| ID | Проблема | Масштаб |
|----|----------|---------|
| A08 | TrackerPipeline нарушает SRP: 5+ concerns, 60+ методов | Крупный рефакторинг |
| A09 | Config — 145 параметров без группировки | Средний |
| A10 | Покрытие тестами ~5% | Высокий приоритет |
| A11 | Нет try/except в UltralyticsBackend | Маленький |
| A12 | Magic numbers в детекторах | Маленький |

## Рекомендуемый порядок

- Быстрые wins (1 день): A02 → A05 → A11
- Стабильность (2-3 дня): A01 → A12 → A06
- Архитектура (планирование): A03 → A04 → A10
- Рефакторинг (отдельный brief): A08 → A09
