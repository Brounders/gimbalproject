# TASK: TASK-20260311-028-operator-baseline-consistency-fix

Task ID: TASK-20260311-028
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Довести `OPERATOR_BASELINE.md` до состояния фактического источника истины без расхождений с текущими preset-файлами и canonical operator mapping.

## Scope
- In scope:
  - исправить таблицу `Preset → Config mapping` в `OPERATOR_BASELINE.md`;
  - синхронизировать значения с `configs/default.yaml`, `configs/night.yaml`, `configs/antiuav_thermal.yaml`, `configs/small_target.yaml`;
  - проверить как минимум `conf_thresh`, `imgsz`, `night_enabled`;
  - убедиться, что документ не содержит приблизительных значений там, где в конфиге уже есть точные.
- Out of scope:
  - изменение runtime logic;
  - новый smoke/benchmark прогон;
  - изменение самих preset-файлов.

## Files
- `OPERATOR_BASELINE.md`

## Validation
- Ручная сверка документа с:
  - `configs/default.yaml`
  - `configs/night.yaml`
  - `configs/antiuav_thermal.yaml`
  - `configs/small_target.yaml`
- `python3 -m compileall -q python_scripts src app orchestrator tests`

## Acceptance Criteria
- [ ] `OPERATOR_BASELINE.md` больше не противоречит текущим preset YAML.
- [ ] В baseline-документе нет приблизительных параметров там, где доступны точные значения.
- [ ] Документ остается коротким и пригодным как инженерная опорная точка.
