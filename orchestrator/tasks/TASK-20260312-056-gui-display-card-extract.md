# TASK: TASK-20260312-056-gui-display-card-extract

Task ID: TASK-20260312-056
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Вынести display-card/HUD helper logic из `app/main_gui.py` в dedicated UI helper module(s), не меняя operator behavior и не трогая source-of-truth tracking state.

## Scope
- In scope:
  - `app/main_gui.py`
  - target info / status badge / HUD display helper code
  - новые helper module(s) in `app/ui/` if needed
- Out of scope:
  - tracking logic changes
  - signal/worker protocol redesign
  - new visual redesign

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
  - current target card / status rendering helpers
- Context:
  - operator display should remain visually and behaviorally stable.

## Implementation Steps
1. Identify display formatting/helper blocks for target card and HUD state.
2. Move pure display helpers into dedicated module(s).
3. Keep `main_gui.py` responsible only for orchestration and widget lifecycle.
4. Preserve current display outputs.

## Acceptance Criteria
- [ ] display-card/HUD helper code is no longer unnecessarily embedded in `main_gui.py`
- [ ] no tracking/business logic moved into the extracted module(s)
- [ ] GUI launch and current operator display remain callable

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
  - `PYTHONPATH=src ./tracker_env/bin/python main_tracker.py --help`
- Expected result:
  - compile clean
  - GUI constructs
  - CLI remains callable

## Risks
- Risk: helper extraction crosses into source-of-truth state handling
- Mitigation: extract formatting/render helpers only, keep state ownership in the main window
