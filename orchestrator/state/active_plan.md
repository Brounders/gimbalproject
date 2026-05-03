# Active Plan

## Plan ID
- AP-OPERATOR-ASSISTED-TRACKING-V2

## Status
- Completed

## Active Claude Tasks (execution allowed now)
- none

## Active RTX Tasks (execution allowed now)
- none

## Source Direction
Human requested all six modernization ideas in one pass and asked how manual
operator selection can also help train the detector model. Codex implemented
V2 as operator-assisted tracking plus operator annotation logging.

## AP-OPERATOR-ASSISTED-TRACKING-V2 — Operator-Assisted Tracking + Annotation

### Цель

Усилить ручной выбор цели так, чтобы оператор мог не только кликнуть точку, но
и выделить bbox, подтвердить/сбросить цель, а pipeline мог удерживать
operator target через visual/template path без обязательного detector lock.

### Результат

| ID | Задача | Статус | Результат |
|----|--------|--------|-----------|
| OPV2-001 | Drag-to-select bbox | ✅ DONE | `VideoStage` emits click or bbox; mapping tested |
| OPV2-002 | Auto seed refinement | ✅ DONE | contrast blob refinement with safe fallback |
| OPV2-003 | Operator hold policy | ✅ DONE | `OPERATOR_HOLD_GRACE_FRAMES`; confirm active as operator |
| OPV2-004 | Multi-template lock | ✅ DONE | bounded template bank in `TemplateLockTracker` |
| OPV2-005 | Operator lock-first path | ✅ DONE | active `operator` source uses `OPERATOR-LOCK` path |
| OPV2-006 | Confirm / release controls | ✅ DONE | UI and worker commands for confirm/release |
| OPV2-007 | Annotation logging for training | ✅ DONE | `runs/operator_annotations/*.jsonl` operator bbox events |

### Итоговое решение

**PASS for code/test validation.**

Ручной выбор теперь является operator-assisted mode, а не простой подсказкой
detector. Успешные operator bbox события сохраняются как будущий материал для
конвертации в YOLO labels.

### Отчёт

- `orchestrator/reports/REPORT-OPERATOR-ASSISTED-TRACKING-V2-20260503.md`

### Следующий шаг

Полевой GUI smoke и затем отдельный цикл:

- конвертер `operator_annotations.jsonl` → YOLO labels;
- отбор кадров по operator events;
- mini fine-tune/eval на провальных клипах.
