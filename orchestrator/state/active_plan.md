# Active Plan

## Plan ID
- AP-DTS-TRAINING-DESK-V1

## Status
- Completed

## Active Claude Tasks (execution allowed now)
- none

## Active RTX Tasks (execution allowed now)
- none

## Source Direction
Human accepted the Training Desk/admin concept and requested implementation in
one pass with a `DTS` button in the UI.  Codex implemented the first review
desk for operator annotation control without starting training automatically.

## AP-DTS-TRAINING-DESK-V1 — Data Training Station

### Цель

Добавить operator annotation admin layer: обзор, фильтры, preview, статусы,
принятие/отклонение/staging, чтобы ручная разметка проходила review перед
экспортом и обучением.

### Результат

| ID | Задача | Статус | Результат |
|----|--------|--------|-----------|
| DTS-001 | Data layer | ✅ DONE | `app/training_desk_data.py`, jsonl loader, review state |
| DTS-002 | Training Desk dialog | ✅ DONE | фильтры, таблица, preview, карточка записи |
| DTS-003 | Review controls | ✅ DONE | `Принять`, `Отклонить`, `В training pack` |
| DTS-004 | Main UI entry | ✅ DONE | кнопка `DTS` в topbar |
| DTS-005 | Tests/report/state | ✅ DONE | data-layer tests + report |

### Итоговое решение

**PASS for V1 admin layer.**

DTS пока не запускает обучение. Он создаёт контролируемый review buffer между
операторской разметкой и будущим training pack.

### Отчёт

- `orchestrator/reports/REPORT-DTS-TRAINING-DESK-20260505.md`

### Следующий шаг

Связать DTS с export/staging:

- экспортировать только accepted/staged records;
- показать путь к созданному training pack;
- добавить ручной training launcher только после визуальной проверки pack.
