# TASK: TASK-20260312-046-dependency-lock-and-bootstrap

Task ID: TASK-20260312-046
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Создать явный локальный dependency/bootstrap contract для desktop-продукта, чтобы запуск проекта на новой машине не зависел от неявного состояния `tracker_env`.

## Scope
- In scope:
  - `requirements.txt` или другой минимальный dependency contract без новых runtime dependencies
  - `RUNBOOK.md`
  - при необходимости `PROJECT_ARCHITECTURE.md`
  - bootstrap instructions для локального Mac desktop-контура
- Out of scope:
  - изменение `tracker_env/`
  - изменение runtime behavior
  - training/automation redesign

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
  - current import/use footprint in `python_scripts/`, `src/`, `app/`
- Context:
  - финальный продукт — локальная программа;
  - dependency contract должен быть понятен без привязки к временной training-инфраструктуре.

## Implementation Steps
1. Зафиксировать минимальный локальный dependency contract для runtime/evaluation desktop-контура.
2. Обновить локальный bootstrap flow в `RUNBOOK.md` с точными шагами установки и проверки.
3. Убедиться, что validation commands и канонические entrypoints остаются работоспособными.

## Acceptance Criteria
- [ ] В репозитории есть явный dependency contract для локального запуска
- [ ] `RUNBOOK.md` содержит короткий и однозначный bootstrap flow
- [ ] Изменение не ломает compile/test/help smoke

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \\( -name "test_*.py" -o -name "*_test.py" \\) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `PYTHONPATH=src ./tracker_env/bin/python main_tracker.py --help`
- Expected result:
  - dependency/bootstrap contract documented
  - validation commands still pass

## Risks
- Risk: contract будет слишком широким и закрепит временные training зависимости как обязательные
- Mitigation: держать scope минимальным и явно отметить local desktop baseline
