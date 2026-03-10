# TASK: TASK-20260311-007-filesystem-inventory

Task ID: TASK-20260311-007
Owner: Claude
Priority: P1
Goal: Сформировать воспроизводимую инвентаризацию файловой системы проекта (структура + размеры + ключевые точки входа).
Files:
- `orchestrator/reports/REPORT-20260311-007.md` (new)
- `python_scripts/filesystem_inventory.py` (new)
- `python_scripts/README.md` (update)
Expected result:
- CLI-скрипт, который строит дерево (ограниченной глубины), топ тяжелых директорий и список критичных entrypoints.
- Отчет с фактами по текущему состоянию ФС проекта.
Validation:
- `python3 -m compileall -q python_scripts src app tests`
- `./tracker_env/bin/python python_scripts/filesystem_inventory.py --root . --max-depth 3 --top-n 25`
- В отчете приложены команды и ключевой вывод.
Constraints:
- Не изменять runtime-код.
- Не удалять и не перемещать данные.
- Не добавлять внешние зависимости.
Status: Done — 2026-03-11. Report: orchestrator/reports/REPORT-20260311-007.md
