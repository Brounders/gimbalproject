# Monolith Slicing Stage-0 Map

## Purpose
Stage-0 карта декомпозиции монолитов `app/main_gui.py` и `src/uav_tracker/pipeline.py`.
Содержит только аудит и план — без фактического переноса кода.

---

## Current LOC

| Модуль | LOC | Статус |
|--------|-----|--------|
| `app/main_gui.py` | 1783 | Монолит — GUI + worker + бизнес-логика смешаны |
| `src/uav_tracker/pipeline.py` | 1162 | Монолит — TrackerPipeline + VideoSession + draw functions |
| `src/uav_tracker/tracking/target_manager.py` | 458 | Норма |
| `src/uav_tracker/evaluation.py` | 243 | Норма |
| `src/uav_tracker/profile_io.py` | 141 | Норма |

---

## pipeline.py — Extraction Candidates

| Кандидат | Функции | LOC est. | Риск |
|----------|---------|----------|------|
| `draw.py` | `draw_frame`, `_draw_target`, `_draw_active_reticle`, `_target_class_label` | ~140 | Низкий — pure functions, нет состояния |
| `runner.py` | `VideoSession`, `run_tracker` + helpers (`ImageSequenceCapture`, `parse_video_source`, `resolve_model_path`) | ~250 | Низкий — независимые классы |
| `TrackerPipeline` | Оставить в `pipeline.py` | ~770 | — |

**Итог pipeline.py после Stage-1 + Stage-2: ~770 LOC (было 1162)**

---

## main_gui.py — Extraction Candidates

| Кандидат | Классы/методы | LOC est. | Риск |
|----------|--------------|----------|------|
| `workers.py` | `TrackerWorker`, `EvaluationWorker` | ~160 | Низкий — QThread без прямых ссылок на виджеты |
| `ui/operator_panel.py` | `build_left_rail()`, `build_header()`, `build_bottom_console()` | ~120 | Средний — ссылки на self.* виджеты |
| `ui/expert_dialog.py` | `build_expert_dialog()` + его методы | ~140 | Средний — ссылки на self.* виджеты |
| `ui/stats_update.py` | `_update_stats()`, `_update_frame()` | ~120 | Средний — много state |
| `MainWindow` | Оставить тонкой оберткой | ~600-800 | — |

**Итог main_gui.py после полной декомпозиции: ~800 LOC (было 1783)**

---

## Phased Plan

### Phase 1 — Low Risk: pipeline draw extraction
**Target:** Создать `src/uav_tracker/draw.py`

**Шаги:**
1. `git mv` функций `draw_frame`, `_draw_target`, `_draw_active_reticle`, `_target_class_label` в новый `draw.py`
2. В `pipeline.py` добавить `from uav_tracker.draw import draw_frame`
3. Прогнать компиляцию + unit-тесты

**Критерии безопасности:**
- `compileall` чистый
- Все импорты `from uav_tracker.pipeline import draw_frame` обновлены (если есть)
- `PYTHONPATH=src python -c "from uav_tracker.pipeline import draw_frame"` работает для обратной совместимости (re-export)

**Rollback:** `git revert` одного коммита

---

### Phase 2 — Low Risk: pipeline runner extraction
**Target:** Создать `src/uav_tracker/runner.py`

**Шаги:**
1. Перенести `VideoSession`, `ImageSequenceCapture`, `run_tracker`, `parse_video_source`, `resolve_model_path` в `runner.py`
2. В `pipeline.py` добавить re-export: `from uav_tracker.runner import VideoSession, run_tracker`
3. Обновить импорты в `app/main_gui.py`, `app/main_cli.py`, `evaluation.py`
4. Прогнать компиляцию + unit-тесты + `--help` smoke

**Критерии безопасности:**
- `from uav_tracker.pipeline import VideoSession` работает (re-export)
- Evaluation.py import не сломан
- GUI запускается без crash

**Rollback:** `git revert` одного коммита

---

### Phase 3 — Medium Risk: GUI worker extraction
**Target:** Создать `app/workers.py`

**Шаги:**
1. Перенести `TrackerWorker(QThread)` и `EvaluationWorker(QThread)` в `app/workers.py`
2. В `main_gui.py`: `from app.workers import TrackerWorker, EvaluationWorker`
3. Убедиться, что Signal/Slot соединения работают через cross-module границу
4. Smoke-запуск GUI

**Критерии безопасности:**
- Нет новых PySide6 import-time ошибок
- GUI запускается и трекинг стартует без crash
- Тест `compileall app`

**Rollback:** `git revert` одного коммита

---

### Phase 4 — Higher Risk: MainWindow panel decomposition
**Target:** Разбить `build_*` методы на `ui/operator_panel.py`, `ui/expert_dialog.py`

> **Статус:** Out of scope для текущего цикла. Требует отдельной задачи.

**Предусловие перед Phase 4:**
- Phase 1-3 завершены и стабильны в production не менее 1 цикла
- Полный test coverage для GUI worker'ов

---

## Absolute Forbidden (никогда без явной задачи)

- Изменять `src/uav_tracker/tracking/target_manager.py` и lock-policy логику
- Переписывать `evaluation.py` в процессе рефактора pipeline
- Трогать `datasets/`, `runs/`, `tracker_env/`
- Менять публичный API `TrackerPipeline.process_frame()`

---

## Next Action

После принятия этого документа Codex Mac должен решить:
- Когда открыть Phase-1 task (pipeline draw extraction)
- Какой milestone является gate для Phase-2

*Created: 2026-03-11 | Owner: Claude Mac | Task: TASK-20260311-015*
