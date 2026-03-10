# TASK: TASK-20260311-005-lock-events-analyzer

Task ID: TASK-20260311-005
Owner: Claude
Priority: P2
Status: Open

## Goal
Добавить утилиту анализа lock-event логов, чтобы быстро выявлять всплески `switch/id-change/lost` между сессиями и прикладывать числовой summary к ревью.

## Files
- `python_scripts/analyze_lock_events.py` (new)
- `python_scripts/README.md` (update index)
- `tests/test_analyze_lock_events.py` (new, minimal)

## Expected result
- CLI принимает путь к `*.jsonl` lock-логам (один или несколько),
- выдает summary по ключевым полям (`events count`, `switches_per_min`, `lost_count`, `reacquired_count`),
- умеет сохранять JSON/CSV отчет,
- работает без изменения runtime-кода.

## Validation
- `python3 -m compileall -q python_scripts src app tests`
- `PYTHONPATH=src ./tracker_env/bin/python -m unittest -q tests.test_analyze_lock_events`
- `./tracker_env/bin/python python_scripts/analyze_lock_events.py --help`

## Constraints
- Без новых зависимостей.
- Не менять runtime-алгоритмы трекинга.
- Логика только аналитическая (post-run tooling).
