# REPORT-TASK-112-SAFETY-HARDENING-PLAN-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted locally

## Scope

TASK-20260517-112 требовала safety hardening plan:

- определить unit-test scope для `NightSmallTargetDetector`;
- определить offscreen PySide6/QML CI sanity;
- определить pipeline smoke-test proposal;
- не менять runtime behavior без отдельного approval.

## Findings

- `NightSmallTargetDetector` расположен в
  `src/uav_tracker/detectors/night_detector.py` и сейчас используется pipeline и
  detector-evidence scripts.
- У detector сложное stateful поведение: candidate counters, grid collision
  handling, active sticky selection, warmup, hotspot/peak paths.
- Прямого dedicated unit-test файла для этого detector сейчас нет.
- В CI есть compileall, pytest и `ui_web` build, но нет отдельного guarded
  offscreen QML smoke step.

## Changes

- Добавлен `docs/PROJECT_SAFETY_HARDENING_PLAN.md`.
- Orchestrator state обновлен: TASK-20260517-112 закрыта, TASK-20260517-113
  стала активной.

## Non-Changes

- Runtime detector code не менялся.
- UI implementation code не менялся.
- CI workflow не менялся.
- Training не запускался.
- Физическая реструктуризация не выполнялась.

## Next Step

Переход к TASK-20260517-113:

1. подготовить physical restructure proposal;
2. не перемещать файлы в этом шаге;
3. описать migration order для `python_scripts/`, configs, docs/archive и tests;
4. определить rollback/validation gates перед любым будущим move.
