# Active Plan

## Plan ID
- AP-OPERATOR-SEEDED-LOCK-UI-V1

## Status
- Completed

## Active Claude Tasks (execution allowed now)
- none

## Active RTX Tasks (execution allowed now)
- none

## Source Direction
Human reported that manual clicking did not help on clips where the drone is
visually obvious but the detector does not see it.  Codex therefore changed
the goal from "select existing detection" to "operator-seeded template lock":
clicking the drone creates an operator-confirmed target and seeds the visual
lock path without requiring YOLO detection.

## AP-OPERATOR-SEEDED-LOCK-UI-V1 — Manual Click → Operator-Seeded Lock

### Цель

Подключить ручной выбор цели к PySide6 UI и сделать так, чтобы клик оператора
запускал удержание через `TemplateLockTracker`, даже если detector не видит
дрон.

### Результат

| ID | Задача | Статус | Результат |
|----|--------|--------|-----------|
| OPSEED-001 | UI coordinate mapping | ✅ DONE | `app/ui/video_mapping.py`, tests for KeepAspectRatio letterbox mapping |
| OPSEED-002 | VideoStage click signal | ✅ DONE | left click emits frame coordinates only inside displayed frame |
| OPSEED-003 | Worker request bridge | ✅ DONE | thread-safe latest-click queue, converts to `OperatorTargetOverride` |
| OPSEED-004 | GUI config/wiring | ✅ DONE | GUI sessions enable `OPERATOR_OVERRIDE_ENABLED`; click goes to worker |
| OPSEED-005 | Operator-seeded template lock | ✅ DONE | operator override force-enters focus mode and seeds template from bbox |
| OPSEED-006 | Telemetry/report/state | ✅ DONE | operator status/count/bbox forwarded and reported |

### Итоговое решение

**Backend + UI wiring PASS.**

Ручной клик теперь не зависит от наличия YOLO detection в выбранной области:
pipeline создаёт `operator` target, переводит tracker в focus-mode и
инициализирует `TemplateLockTracker` выбранной областью.

### Отчёт

- `orchestrator/reports/REPORT-OPERATOR-SEEDED-LOCK-UI-20260503.md`

### Следующий шаг

Human/Codex GUI smoke: вручную проверить клип, где detector не видит визуально
заметный дрон, и оценить реальную устойчивость template lock после клика.
