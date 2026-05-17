# Статус automation/state

Дата статуса: 2026-05-17

JSON-файлы в этой папке — историческое состояние automation и RTX/Mac training
flow за март 2026. Это полезное evidence, но не текущий источник права на
исполнение.

## Текущее решение

- Статус: `HISTORICAL_NEEDS_REVIEW`.
- Текущий источник исполнения: `orchestrator/state/active_plan.md`.
- Текущий источник задач: `orchestrator/state/open_tasks.md` и
  `orchestrator/state/completed_tasks.md`.
- Текущий источник training truth: `orchestrator/state/open_training.md` и
  accepted training reports.

## Основания

- В файлах есть Windows paths вида `C:\Users\PC\...`.
- Timestamps относятся к 2026-03-12 и 2026-03-13.
- Текущее состояние detector/training за 2026-05 ведется через orchestrator
  reports; YOLO26 smoke явно помечен как invalid/stopped.

## Правила до review

- Не обновлять эти JSON как источник текущей training truth.
- Не удалять и не архивировать их до proof и owner decision в TASK-20260517-111.
- Если какой-то скрипт еще читает эти файлы, эту зависимость нужно
  задокументировать до любого move/delete.

## Какое решение нужно

TASK-20260517-111 должен классифицировать эту папку как:

1. active automation state с обновленной schema и актуальными paths;
2. historical evidence, перенесенное в archive/docs;
3. deprecated state, оставленный только для migration scripts.
