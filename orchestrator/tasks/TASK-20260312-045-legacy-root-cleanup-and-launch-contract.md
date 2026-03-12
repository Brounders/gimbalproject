# TASK: TASK-20260312-045-legacy-root-cleanup-and-launch-contract

Task ID: TASK-20260312-045
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Сделать корень проекта и локальные entrypoints понятными для desktop-продукта: сохранить канонические точки запуска, а legacy-root scripts безопасно вывести из основного operator/developer workflow.

## Scope
- In scope:
  - root files: `main_tracker.py`, `tracker_gui.py`, `benchmark.py`, `real_tracker.py`, `train_script.py`
  - `legacy/`
  - `RUNBOOK.md`
  - `PROJECT_ARCHITECTURE.md`
- Out of scope:
  - удаление работающих канонических entrypoints;
  - runtime logic changes;
  - cleanup `datasets/`, `runs/`, `tracker_env/`.

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - root scripts in repository root
  - `legacy/`
  - `RUNBOOK.md`
  - `PROJECT_ARCHITECTURE.md`
- Context:
  - финальный продукт — локальная программа;
  - корень проекта не должен вводить в заблуждение legacy/training мусором.

## Implementation Steps
1. Разделить root scripts на канонические entrypoints и legacy-only artifacts.
2. Безопасно архивировать или явно пометить legacy-root scripts так, чтобы они не воспринимались как production paths.
3. Обновить документацию локального запуска и launch contract.

## Acceptance Criteria
- [ ] Канонические локальные entrypoints однозначно определены
- [ ] Legacy-root scripts больше не выглядят как рабочие production launch paths
- [ ] `main_tracker.py` и `tracker_gui.py` остаются совместимыми точками запуска

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `python3 main_tracker.py --help`
  - `QT_QPA_PLATFORM=offscreen PYTHONPATH=src ./tracker_env/bin/python - <<'PY'\nfrom PySide6.QtWidgets import QApplication\nfrom app.main_gui import MainWindow\napp = QApplication([])\nwin = MainWindow()\nprint('gui_ok')\nwin.close()\napp.quit()\nPY`
- Expected result:
  - канонический CLI и GUI entrypoint остаются рабочими

## Risks
- Risk: слишком агрессивная cleanup-операция может сломать привычные пользовательские команды
- Mitigation: сохранить `main_tracker.py` и `tracker_gui.py` как совместимые wrappers; legacy только архивировать/помечать
