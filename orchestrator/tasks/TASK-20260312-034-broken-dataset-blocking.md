# TASK: TASK-20260312-034-broken-dataset-blocking

Task ID: TASK-20260312-034
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Сделать dataset registry устойчивым к неполным dataset-каталогам: такие наборы не должны попадать в `ready/queued`, а должны явно блокироваться с понятным статусом и причиной.

## Scope
- In scope:
  - критерии готовности dataset в conveyor tooling;
  - статус/notes для broken datasets;
  - повторный `scan` с обновлением registry.
- Out of scope:
  - починка самих dataset content;
  - изменения training runner;
  - удаление dataset folders.

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `python_scripts/training_conveyor.py`
  - `automation/state/dataset_registry.json`
- Context:
  - `drone_bird_mendeley_ir_mix_v1` выглядит неполным (`image_files=0`, `label_files=3`), но помечен как `ready_for_training=true`

## Implementation Steps
1. Уточнить readiness criteria для dataset catalog.
2. Маркировать broken datasets как blocked и записывать причину в registry.
3. Проверить, что `next-chunk` больше не выбирает broken datasets.

## Acceptance Criteria
- [ ] Неполный dataset больше не получает `ready_for_training=true`
- [ ] Registry отражает blocking reason
- [ ] `next-chunk` не выбирает такой dataset

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `python3 python_scripts/training_conveyor.py scan --dataset-root ... --state-dir ...`
  - `python3 python_scripts/training_conveyor.py next-chunk ...`
- Expected result:
  - scan passes
  - broken dataset gets blocked status
  - chunk selection skips it

## Risks
- Risk: слишком жесткие readiness criteria заблокируют валидные datasets
- Mitigation: оставить критерии минимальными и проверяемыми
