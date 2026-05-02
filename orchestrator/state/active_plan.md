# Active Plan

## Plan ID
- AP-OPERATOR-OVERRIDE-BACKEND-V1

## Status
- Completed

## Active Claude Tasks (execution allowed now)
- none

## Active RTX Tasks (execution allowed now)
- none

## Source Direction
Human approved a one-pass implementation of the backend foundation for manual
operator target selection.  Scope was intentionally limited to command/data
contract, TargetManager/Pipeline wiring, feature flag, telemetry, tests, and
reporting.  PySide6 UI wiring is a later cycle.

## AP-OPERATOR-OVERRIDE-BACKEND-V1 — Manual Target Selection Backend

### Цель

Позволить будущему UI передать в pipeline операторскую метку цели
(click или bbox), чтобы tracker мог сбросить ошибочную active target и начать
вести operator-confirmed область.

### Результат

| ID | Задача | Статус | Результат |
|----|--------|--------|-----------|
| OPOR-001 | OperatorTargetOverride command | ✅ DONE | click/bbox command with clipped frame bbox |
| OPOR-002 | TargetManager operator-confirmed target | ✅ DONE | prefer existing overlapping target, otherwise create auxiliary target |
| OPOR-003 | TrackerPipeline guarded queue | ✅ DONE | `request_operator_target()` + `OPERATOR_OVERRIDE_ENABLED` guard |
| OPOR-004 | FrameOutput telemetry | ✅ DONE | status/count/bbox fields added default-safe |
| OPOR-005 | Tests/report/state | ✅ DONE | `tests/test_operator_override.py` + implementation report |

### Итоговое решение

**Backend PASS.**

Ручной выбор цели теперь имеет проверяемый backend-контракт, но остаётся
выключенным по умолчанию через `Config.OPERATOR_OVERRIDE_ENABLED=False`.

### Отчёт

- `orchestrator/reports/REPORT-OPERATOR-OVERRIDE-BACKEND-20260503.md`

### Следующий шаг

Выбрать новый цикл после Human approval:

- подключить PySide6 UI click/drag к `TrackerPipeline.request_operator_target()`;
- проверить coordinate mapping из widget coordinates в frame coordinates;
- добавить визуальную индикацию operator-selected/operator-confirmed target.
