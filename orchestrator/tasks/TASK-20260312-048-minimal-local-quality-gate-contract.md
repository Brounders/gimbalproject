# TASK: TASK-20260312-048-minimal-local-quality-gate-contract

Task ID: TASK-20260312-048
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Сделать локальный `quick smoke -> benchmark -> quality-gate` контур однозначным, чтобы baseline/candidate решения принимались по понятному и воспроизводимому порядку.

## Scope
- In scope:
  - `RUNBOOK.md`
  - `PROJECT_ARCHITECTURE.md`
  - `python_scripts/run_quick_kpi_smoke.py`
  - `python_scripts/run_offline_benchmark.py`
  - `python_scripts/run_quality_gate.py`
  - при необходимости `OPERATOR_BASELINE.md`
- Out of scope:
  - изменение tracking runtime behavior
  - promotion новой модели
  - расширение GitHub/RTX automation как основного контура

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `RUNBOOK.md`
  - `PROJECT_ARCHITECTURE.md`
  - `OPERATOR_BASELINE.md`
  - `python_scripts/run_quick_kpi_smoke.py`
  - `python_scripts/run_offline_benchmark.py`
  - `python_scripts/run_quality_gate.py`
- Context:
  - после audit и conveyor cycles baseline/candidate decision flow остается слишком неявным;
  - финальный продукт локальный, значит quality discipline должна быть понятна локально, а не через временный web/RTX workflow.

## Implementation Steps
1. Зафиксировать канонический локальный порядок: `quick smoke -> benchmark -> quality-gate -> decision`.
2. Выравнять docs/script contracts так, чтобы baseline, candidate и operator decision были обозначены без двусмысленности.
3. Обновить локальную документацию под этот единый contract.

## Acceptance Criteria
- [ ] Есть один однозначный локальный quality-gate flow для baseline/candidate decision
- [ ] Документация больше не оставляет двусмысленности, что запускать и в каком порядке
- [ ] Script contracts и docs не противоречат друг другу

## Validation
- Commands:
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --help`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_offline_benchmark.py --help`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quality_gate.py --help`
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
- Expected result:
  - локальный decision flow documented and coherent
  - scripts remain callable

## Risks
- Risk: документация станет красивой, но не совпадет с фактическими командами и артефактами
- Mitigation: acceptance считать выполненной только при реальной проверке help/contract команд
