# TASK: TASK-20260311-014-quick-kpi-smoke

Task ID: TASK-20260311-014
Owner: Claude Mac
Priority: P1
Status: Accepted — 2026-03-11 (Codex Mac review). Report: orchestrator/reports/REPORT-20260311-014.md

## Goal
Добавить быстрый KPI smoke-прогон для трекинга (короткие клипы, фиксированный набор метрик), чтобы перед full benchmark быстро отлавливать регрессии.

## Scope
- In scope:
  - добавить скрипт `python_scripts/run_quick_kpi_smoke.py`;
  - вход: 2-3 источника, ограничение кадров, preset;
  - выход: компактный JSON/CSV summary (`avg_fps`, `active_id_changes_per_min`, `lock_switches_per_min`, `false_lock_rate` если доступно).
- Out of scope:
  - изменение quality-gate решения release/non-release;
  - изменение runtime tracking logic.

## Files
- `python_scripts/run_quick_kpi_smoke.py` (new)
- `python_scripts/README.md` (update index)

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --help`
- Dry-run smoke с одним коротким видео (если доступно локально).

## Acceptance Criteria
- [ ] Скрипт запускается и формирует summary без падений.
- [ ] Формат summary пригоден для сравнения baseline/candidate.
- [ ] Нет изменений runtime decision loop.
