# TASK: TASK-20260311-027-operator-baseline-freeze

Task ID: TASK-20260311-027
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Зафиксировать текущий операторский baseline в одном коротком документе на основе реального smoke-прогона, чтобы дальнейшие изменения сравнивались с понятной опорной точкой.

## Scope
- In scope:
  - создать `OPERATOR_BASELINE.md`;
  - зафиксировать канонические режимы `Auto / Day / Night / IR`;
  - зафиксировать, какой preset стоит за каждым режимом;
  - зафиксировать текущий smoke snapshot из `orchestrator/state/operator_smoke_20260311.md` и краткие KPI;
  - перечислить слабые сцены текущего baseline.
- Out of scope:
  - изменение runtime logic;
  - запуск нового benchmark/quality-gate цикла.

## Files
- `OPERATOR_BASELINE.md` (new)

## Validation
- Проверка, что документ ссылается на существующие артефакты/пресеты/режимы.

## Acceptance Criteria
- [ ] Есть один понятный baseline-документ для оператора и инженерного сравнения.
- [ ] В документе нет противоречий с текущими canonical modes в коде.
- [ ] Зафиксированы текущие слабые сцены baseline.
