# TASK: TASK-20260311-001-pipeline-overlay-extract-stage1

## Goal
Локально уменьшить монолитность `src/uav_tracker/pipeline.py`: вынести функции/блоки визуального overlay в `src/uav_tracker/overlay.py` без изменения бизнес-логики трекинга и формата `FrameOutput`.

## Scope
- In scope:
  - перенос overlay-related helper-функций в отдельный модуль;
  - подключение нового модуля через импорт;
  - сохранение текущего внешнего поведения (CLI/GUI).
- Out of scope:
  - изменение lock policy,
  - изменение quality-gate,
  - UI redesign.

## Constraints
- Минимальный обратимый diff.
- Никаких новых зависимостей.
- Никаких изменений алгоритма трекинга.

## Inputs
- `src/uav_tracker/pipeline.py`
- `src/uav_tracker/overlay.py` (создать/доработать)

## Implementation Steps
1. Выделить из `pipeline.py` чистые overlay-функции (отрисовка HUD/рамок/карточки).
2. Перенести их в `overlay.py` с сохранением сигнатур и комментариев по контексту.
3. Подключить в `pipeline.py` через импорт, убрать дубли.
4. Проверить, что запуск CLI/GUI не ломается.

## Status
Accepted — 2026-03-11 (Codex Mac review). Report: orchestrator/reports/REPORT-20260311-001.md

## Acceptance Criteria
- [x] `pipeline.py` уменьшен, overlay-код вынесен в отдельный модуль.
- [x] Поведение runtime не изменено (компиляция и import chain чисты).
- [x] Проверки проходят: compile + import smoke.

## Validation
- `python3 -m compileall -q python_scripts src app`
- `./tracker_env/bin/python main_tracker.py --preset night_ir_lock_v2 --mode operator --source test_videos/night_ground_large_drones.mp4 --device mps --max-frames 120 --no-display`

## Risks
- Risk: неявная зависимость overlay от внутреннего состояния pipeline.
- Mitigation: переносить только чистые функции и сохранять сигнатуры без логических правок.
