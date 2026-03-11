# TASK: TASK-20260311-018-target-presentation-state-stabilization

Task ID: TASK-20260311-018
Owner: Claude Mac
Priority: P1
Status: Accepted — 2026-03-11 (Codex Mac review). Report: orchestrator/reports/REPORT-20260311-018.md

## Goal
Снизить визуальную дерготню и остаточные несоответствия в отображении target presentation и state transitions (`SCAN/TRACK/LOST`) без широкого изменения decision loop.

## Scope
- In scope:
  - локально стабилизировать визуальное представление цели (рамка/карточка/overlay-state);
  - уменьшить резкие визуальные переключения отображаемого состояния;
  - синхронизировать UI-представление с каноническими состояниями ядра там, где сейчас есть остаточный шум.
- Out of scope:
  - крупный рефактор TargetManager;
  - смена алгоритма lock-policy целиком;
  - изменение training model behavior.

## Files
- `src/uav_tracker/pipeline.py`
- `src/uav_tracker/overlay.py`
- `app/main_gui.py` (только если требуется корректировка state presentation)

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- Если возможно: короткий локальный smoke run на одном test video.
- Сравнение до/после на уровне отсутствия явных лишних визуальных переходов.

## Acceptance Criteria
- [ ] Визуальное отображение цели ведет себя более плавно и предсказуемо.
- [ ] Нет новых агрессивных state flicker в UI.
- [ ] Decision loop не переписан wholesale.
