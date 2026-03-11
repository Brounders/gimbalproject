# TASK: TASK-20260311-015-monolith-slicing-stage0

Task ID: TASK-20260311-015
Owner: Claude Mac
Priority: P2
Status: Accepted — 2026-03-11 (Codex Mac review). Report: orchestrator/reports/REPORT-20260311-015.md

## Goal
Подготовить stage-0 карту безопасной декомпозиции монолитов `app/main_gui.py` и `src/uav_tracker/pipeline.py` без фактического рефактора в этой задаче.

## Scope
- In scope:
  - создать документ-карту разбиения: целевые модули, границы ответственности, порядок шагов;
  - указать для каждого шага риски и rollback.
- Out of scope:
  - реальный перенос кода;
  - изменение runtime behavior.

## Files
- `orchestrator/state/monolith_slicing_stage0.md` (new)
- `orchestrator/reports/REPORT-20260311-015.md` (new)

## Validation
- Документ содержит:
  - текущие размеры модулей (LOC),
  - список extraction-candidates,
  - поэтапный порядок (минимум 3 фазы),
  - критерии безопасности на фазу.

## Acceptance Criteria
- [ ] Есть проверяемый, пошаговый и обратимый план декомпозиции.
- [ ] План не требует большого одномоментного рефактора.
- [ ] Ясно выделены low-risk first шаги.
