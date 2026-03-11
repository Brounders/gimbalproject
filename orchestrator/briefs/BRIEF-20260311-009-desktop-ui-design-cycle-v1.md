# BRIEF: BRIEF-20260311-009-desktop-ui-design-cycle-v1

## Context
Human approved a dedicated desktop UI design cycle for the existing PySide6 application.
The target is a modernized operator-facing shell without changing the technology stack and without moving business logic into the UI layer.

## Objective
Bring the existing GUI closer to the requested composition and visual language:
- HeaderBar / LeftControlRail / MainVideoStage / BottomConsole,
- target info card in the video stage,
- cleaner operator flow,
- translucent layered styling,
- no broad runtime rewrite.

## Success Metrics
- HeaderBar contains the requested operator controls and removes duplicate diagnostics from the base surface.
- LeftControlRail is focused on operator actions only.
- MainVideoStage shows only minimal operational overlays and a dedicated target info card.
- BottomConsole becomes the only always-visible event log surface.
- Visual styling matches the requested palette and minimalism without neon/game-HUD aesthetics.

## Boundaries
- Must do:
  - stay in PySide6;
  - keep UI/business/runtime boundaries explicit;
  - use minimal, staged, reversible changes.
- Must not do:
  - migrate to QML/Web;
  - perform a broad runtime rewrite;
  - reintroduce visible diagnostics into the operator layer.

## Deliverables
- 3 active Claude tasks for this design cycle.
- Updated `active_plan`, `open_tasks`, `project_state`.
