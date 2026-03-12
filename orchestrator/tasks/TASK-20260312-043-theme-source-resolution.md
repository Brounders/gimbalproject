# TASK: TASK-20260312-043-theme-source-resolution

Task ID: TASK-20260312-043
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Сделать источник темы UI явным и поддерживаемым: устранить ситуацию, в которой `app/ui/theme.py` отсутствует как исходник, а фактическая тема живет неофициально в `app/main_gui.py`.

## Scope
- In scope:
  - `app/main_gui.py`
  - `app/ui/`
  - локальная UI theme/documentation contract
- Out of scope:
  - визуальный redesign;
  - изменения tracking/runtime logic;
  - перенос большого объема UI-кода по всему проекту.

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `app/main_gui.py`
  - `app/ui/`
  - `PROJECT_ARCHITECTURE.md`
  - `RUNBOOK.md`
- Context:
  - `theme.py` source отсутствует;
  - тема должна иметь один честный source of truth.

## Implementation Steps
1. Определить, что является каноническим source of truth для `APP_STYLESHEET`.
2. Либо создать официальный `app/ui/theme.py` и перевести `main_gui.py` на импорт, либо явно закрепить inline-theme как канонический вариант и убрать ложные ожидания отдельного theme module.
3. Обновить документацию и локальные imports так, чтобы файловая система и реальный код больше не расходились.

## Acceptance Criteria
- [ ] Источник UI theme выражен явным исходным файлом/контрактом, а не только `.pyc` или скрытым inline-блоком
- [ ] `MainWindow` по-прежнему создается без crash и с тем же визуальным baseline
- [ ] Нет ложных ссылок на несуществующий `app/ui/theme.py`

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `QT_QPA_PLATFORM=offscreen PYTHONPATH=src ./tracker_env/bin/python - <<'PY'\nfrom PySide6.QtWidgets import QApplication\nfrom app.main_gui import MainWindow\napp = QApplication([])\nwin = MainWindow()\nprint(type(win).__name__)\nwin.close()\napp.quit()\nPY`
- Expected result:
  - compileall passes
  - GUI smoke instantiates `MainWindow`

## Risks
- Risk: unintentionally changing visual theme behavior while only trying to formalize source
- Mitigation: preserve `APP_STYLESHEET` semantics and validate offscreen GUI construction
