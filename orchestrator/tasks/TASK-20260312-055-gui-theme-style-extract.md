# TASK: TASK-20260312-055-gui-theme-style-extract

Task ID: TASK-20260312-055
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Вынести theme/style-related code из `app/main_gui.py` в dedicated UI helper module(s), сохранив текущий operator behavior и используя уже существующий `app/ui/theme.py` как source of truth для stylesheet.

## Scope
- In scope:
  - `app/main_gui.py`
  - `app/ui/theme.py`
  - новые helper module(s) in `app/ui/` if needed
- Out of scope:
  - new design / layout changes
  - worker logic refactor
  - tracking/runtime changes

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
  - `app/ui/theme.py`
- Context:
  - theme source was already formalized; now the goal is to reduce style wiring inside `main_gui.py`.

## Implementation Steps
1. Identify style/theme helper blocks in `main_gui.py`.
2. Move low-risk theme/style wiring into helper module(s) in `app/ui/`.
3. Keep `app/ui/theme.py` as stylesheet source of truth.
4. Preserve current startup and visual behavior.

## Acceptance Criteria
- [ ] `main_gui.py` no longer contains unnecessary theme/style helper blocks inline
- [ ] `app/ui/theme.py` remains the stylesheet source of truth
- [ ] GUI launch and compile continue to work without behavior change

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `QT_QPA_PLATFORM=offscreen PYTHONPATH=src ./tracker_env/bin/python - <<'PY'
from PySide6.QtWidgets import QApplication
from app.main_gui import MainWindow
app = QApplication([])
win = MainWindow()
print(type(win).__name__)
win.close()
PY`
- Expected result:
  - compile clean
  - GUI can construct MainWindow

## Risks
- Risk: style extraction accidentally changes widget appearance at startup
- Mitigation: move only low-risk style wiring and preserve theme source exactly
