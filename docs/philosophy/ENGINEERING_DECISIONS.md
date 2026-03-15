# Engineering Decisions

## Product Decisions
- Финальный продукт — локальная desktop-программа.
- `RTX + GitHub + automation` — временный operational слой, а не ядро продукта.

## Process Decisions
- Любое сообщение Human в форме `План: ...` сначала раскрывается в подробный план.
- До явного подтверждения Human запрещена выгрузка в `main`.
- В каждый момент времени должен быть только один активный инженерный цикл.

## Architecture Decisions
- UI не содержит бизнес-логику.
- Runtime/business logic не зависит от слоя отображения.
- `pipeline.py` и `main_gui.py` декомпозируются поэтапно, без переписывания системы с нуля.
- Большие refactor-циклы открываются только после reviewer acceptance предыдущей фазы.

## Baseline / Model Decisions
- Канонический локальный baseline path: `models/baseline.pt`
- Baseline устанавливается через `python_scripts/install_baseline.py`
- Candidate-модель может стать baseline только после локального `quality-gate`
- Решение по candidate только одно из:
  - `promote`
  - `hold_and_tune`
  - `reject`

## Quality Decisions
- `day`, `night`, `ir` — отдельные quality contexts
- Problem-pack является обязательным коротким барьером для hard runtime fixes
- Нельзя принимать модель или runtime-change только по train metrics или по одному aggregate числу

## Training Decisions
- Новый training cycle не открывать автоматически после завершения предыдущего
- Сначала runtime-quality / model decision
- Потом только отдельный утвержденный training plan
- Бинарные артефакты не коммитятся в `main`

## Context Management Decisions
- Источником “живой памяти” проекта должны быть короткие канонические файлы, а не бесконечный чат
- Для новых сессий первыми читаются:
  - `PROJECT_COMPASS.md`
  - `CURRENT_PHASE.md`
  - `ENGINEERING_DECISIONS.md`
