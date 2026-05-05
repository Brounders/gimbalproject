# Active Plan

## Plan ID
- AP-OPERATOR-UI-1TO1-REDESIGN-V1

## Status
- Completed

## Active Claude Tasks (execution allowed now)
- none

## Active RTX Tasks (execution allowed now)
- none

## Source Direction
Human rejected the prior visual-only pass as insufficient and required a
structural 1:1-style redesign based on:

- `/Users/bround/Downloads/UI/Gimbal Operator UI.html`
- `/Users/bround/Downloads/UI/tweaks-panel.jsx`

Constraint: preserve all already implemented operator functionality.

## AP-OPERATOR-UI-1TO1-REDESIGN-V1 — Structural Operator HUD Redesign

### Цель

Перестроить PySide6 operator UI from form-like layout into a HUD composition:
full-bleed video base layer with floating topbar, left rail, right telemetry cards
and bottom dock.

### Результат

| ID | Задача | Статус | Результат |
|----|--------|--------|-----------|
| UI1TO1-001 | Reference audit | ✅ DONE | HTML composition mapped to PySide6 widgets |
| UI1TO1-002 | Overlay shell | ✅ DONE | `QGridLayout` one-cell overlay in `MainWindow` |
| UI1TO1-003 | Topbar redesign | ✅ DONE | compact brand/modes/status/actions line |
| UI1TO1-004 | Left rail redesign | ✅ DONE | narrow rail + source/data drawer |
| UI1TO1-005 | Right HUD cards | ✅ DONE | target/runtime cards placed below topbar |
| UI1TO1-006 | Bottom dock | ✅ DONE | centered floating control dock |
| UI1TO1-007 | Preview/validation | ✅ DONE | offscreen preview generated |

### Итоговое решение

**PASS for structural UI redesign.**

Tracking/runtime/model logic unchanged.

### Отчёт

- `orchestrator/reports/REPORT-OPERATOR-UI-1TO1-REDESIGN-20260505.md`

### Следующий шаг

Human visual review. If accepted, next bounded cycle can add interactive drawer
collapse/expand behavior for the left source panel without touching tracking
logic.
