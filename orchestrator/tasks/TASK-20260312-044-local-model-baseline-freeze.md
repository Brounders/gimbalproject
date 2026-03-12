# TASK: TASK-20260312-044-local-model-baseline-freeze

Task ID: TASK-20260312-044
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Зафиксировать стабильный локальный baseline model path для desktop-программы и убрать зависимость operator preset-конфигов от эфемерных путей внутри `runs/`.

## Scope
- In scope:
  - `configs/*.yaml`
  - локальный baseline model contract
  - `models/` или другой стабильный локальный path проекта
  - документация запуска/обновления baseline модели
- Out of scope:
  - новый training cycle;
  - promotion новой candidate-модели;
  - web/RTX artifact pipeline redesign.

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `configs/default.yaml`
  - `configs/night.yaml`
  - `configs/small_target.yaml`
  - `configs/antiuav_thermal.yaml`
  - `RUNBOOK.md`
  - `PROJECT_ARCHITECTURE.md`
- Context:
  - текущие preset-модельные пути завязаны на `runs/.../best.pt`;
  - финальный продукт — локальная программа, а не временный training workspace.

## Implementation Steps
1. Определить стабильный локальный baseline path/contract для production desktop запуска.
2. Обновить preset-конфиги так, чтобы они ссылались на этот стабильный локальный baseline, а не на training output в `runs/`.
3. Документировать, как baseline обновляется локально без зависимости от временного training workspace.

## Acceptance Criteria
- [ ] Канонические operator presets больше не используют `runs/.../best.pt` как production model path
- [ ] Локальный baseline path однозначно задокументирован
- [ ] Изменение не ломает CLI/GUI запуск при наличии baseline-модели на ожидаемом локальном пути

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `rg -n \"model_path:\" configs`
  - `python3 main_tracker.py --help`
- Expected result:
  - configs point to stable local baseline contract
  - CLI help still works

## Risks
- Risk: baseline path будет формально стабильным, но фактически отсутствовать на машине
- Mitigation: зафиксировать понятный local contract и обновить runbook с шагом baseline refresh
