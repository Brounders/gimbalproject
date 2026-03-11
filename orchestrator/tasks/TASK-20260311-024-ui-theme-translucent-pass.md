# TASK: TASK-20260311-024-ui-theme-translucent-pass

Task ID: TASK-20260311-024
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Обновить визуальную тему приложения под заданную палитру и современный минималистичный desktop style с умеренной полупрозрачностью и подсветкой активных элементов.

## Scope
- In scope:
  - обновить `APP_STYLESHEET` и связанные style helpers;
  - использовать палитру: `#23272B`, `#2B3136`, `#31383E`, `#3E474F`, `#E6EBEF`, `#AAB4BE`;
  - ввести умеренные translucent surfaces через `rgba(...)` там, где это не ломает читаемость;
  - добавить понятную подсветку активных кнопок и состояний;
  - избегать neon, gaming HUD, heavy glassmorphism.
- Out of scope:
  - новый стек темизации;
  - внешний asset pipeline;
  - полный component framework extraction.

## Files
- `app/main_gui.py`
- `app/ui/*` (если для style helper потребуется локальное выделение)

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- Ручная визуальная проверка в запущенном GUI.

## Acceptance Criteria
- [ ] Интерфейс визуально следует целевой палитре и иерархии.
- [ ] Активные кнопки и статусы читаемы и подсвечены.
- [ ] Полупрозрачность не ухудшает читаемость поверх видео.
