# TASK: TASK-20260312-033-dataset-scene-profile-fix

Task ID: TASK-20260312-033
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Исправить логику определения `scene_profile` в dataset registry так, чтобы `drone-bird-yolo` не классифицировался как `ir` из-за ложного совпадения в имени.

## Scope
- In scope:
  - код определения `scene_profile` в conveyor tooling;
  - unit-level or script-level validation на нескольких dataset name/path примерах.
- Out of scope:
  - любые runtime tracking изменения;
  - пересмотр budgets или training policy;
  - исправление dataset content.

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
  - `drone-bird-yolo` сейчас ошибочно получает `scene_profile=ir`

## Implementation Steps
1. Найти и локально исправить heuristic/classifier для `scene_profile`.
2. Проверить, что `bird` больше не вызывает ложный `ir`.
3. Повторно прогнать `scan` на synthetic or real dataset names и зафиксировать корректный результат.

## Acceptance Criteria
- [ ] `drone-bird-yolo` после `scan` получает корректный `scene_profile`
- [ ] `mendeley_ir` или другой действительно IR dataset не ломается
- [ ] Изменение ограничено conveyor tooling

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `python3 python_scripts/training_conveyor.py scan --dataset-root ... --state-dir ...`
- Expected result:
  - conveyor scan passes
  - corrected `scene_profile` appears in registry

## Risks
- Risk: сломать scene routing для реальных IR datasets
- Mitigation: проверить минимум на 2 разных dataset patterns
