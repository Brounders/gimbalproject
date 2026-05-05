# Active Plan

## Plan ID
- AP-OPERATOR-UI-SHELL-V2

## Status
- Completed

## Active Claude Tasks (execution allowed now)
- none

## Active RTX Tasks (execution allowed now)
- none

## Source Direction
Human rejected the prior structural 1:1 pass as looking like a workaround and
reported that some controls did not work. Human then required a managed
PySide6/Desktop transition plan and implementation toward a compact operator HUD:
maximum video space, compact top status, narrow left actions, target card, hidden
diagnostics drawer, preserved existing functionality.

## AP-OPERATOR-UI-SHELL-V2 — Operator UI Shell Foundation

### Цель

Replace decorative HUD imitation with a native PySide6 shell foundation built
from reusable components and real connected controls.

### Результат

| ID | Задача | Статус | Результат |
|----|--------|--------|-----------|
| UISH-001 | UI structure audit | ✅ DONE | MainWindow/layout/theme/video/state/action map reviewed |
| UISH-002 | Remove fake controls | ✅ DONE | QLabel action illusions replaced/removed |
| UISH-003 | Reusable components | ✅ DONE | IconButton, StatusBadge, MetricTile, BottomDrawer |
| UISH-004 | Compact left rail | ✅ DONE | 72px rail + source/record drawer |
| UISH-005 | Diagnostics drawer | ✅ DONE | Inspector moved from right card into bottom drawer |
| UISH-006 | Preserve actions | ✅ DONE | Start/stop/eval/DTS/expert/manual target/action buttons preserved |
| UISH-007 | Validation | ✅ DONE | UI smoke tests and preview generated |

### Итоговое решение

**PASS for UI shell foundation.**

No tracking/backend/model logic changed.

### Отчёт

- `orchestrator/reports/REPORT-OPERATOR-UI-SHELL-V2-20260505.md`

### Следующий шаг

Human visual review, then a bounded polish pass:

- refine spacing/typography/active states;
- improve collapsed drawer handle;
- optionally add a real video zoom feature only if runtime support is designed.
