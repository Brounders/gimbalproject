# TASK: TASK-20260311-006-profile-preset-validator

Task ID: TASK-20260311-006
Owner: Claude
Priority: P2
Status: Accepted — 2026-03-11 (Codex Mac review). Report: orchestrator/reports/REPORT-20260311-006.md

## Goal
Добавить валидатор пресетов/профилей YAML, чтобы до запуска обнаруживать неверные ключи и значения, влияющие на стабильность операторского контура.

## Files
- `python_scripts/validate_profile_presets.py` (new)
- `python_scripts/README.md` (update)
- `tests/test_validate_profile_presets.py` (new, minimal)

## Expected result
- CLI сканирует `configs/*.yaml`,
- проверяет ключи против маппинга `src/uav_tracker/profile_io.py`,
- выводит список unknown/missing/invalid entries,
- возвращает non-zero exit code при ошибках,
- не вносит изменений в runtime behavior.

## Validation
- `python3 -m compileall -q python_scripts src app tests`
- `PYTHONPATH=src ./tracker_env/bin/python -m unittest -q tests.test_validate_profile_presets`
- `./tracker_env/bin/python python_scripts/validate_profile_presets.py --configs-dir configs`

## Constraints
- Без сторонних библиотек.
- Без правок decision-loop и core tracker pipeline.
- Проверки должны быть детерминированными.
