# TASK: TASK-20260311-008-filesystem-classification

Task ID: TASK-20260311-008
Owner: Claude
Priority: P1
Goal: Классифицировать файлы/директории проекта по архитектурным ролям и критичности для runtime.
Files:
- `orchestrator/reports/REPORT-20260311-008.md` (new)
- `orchestrator/state/filesystem_classification.md` (new)
Expected result:
- Матрица классификации: `core`, `runtime-entry`, `training-tools`, `datasets-artifacts`, `legacy`, `candidate-cleanup`.
- Для каждого класса: риск, владелец, допустимые операции.
Validation:
- Ссылки на фактические пути и размеры из TASK-007.
- Проверка, что все runtime entrypoints (`main_tracker.py`, `tracker_gui.py`, `app/*`, `src/*`) отнесены к non-removable.
Constraints:
- Без правок runtime-кода.
- Без удаления/перемещения каталогов.
- Только аналитические артефакты.
Status: Done — 2026-03-11. Report: orchestrator/reports/REPORT-20260311-008.md
