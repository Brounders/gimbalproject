# TASK: TASK-20260312-057-gui-nonworker-plumbing-thinning

Task ID: TASK-20260312-057
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
После extraction задач `055` и `056` истончить `app/main_gui.py` до orchestration-first структуры, вынеся low-risk non-worker UI plumbing without changing behavior.

## Scope
- In scope:
  - `app/main_gui.py`
  - helper module(s) in `app/ui/`
  - low-risk UI plumbing not tied to worker/tracking internals
- Out of scope:
  - worker lifecycle redesign
  - runtime/tracking logic changes
  - UI redesign

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
  - outputs of `TASK-20260312-055` and `TASK-20260312-056`
- Context:
  - `main_gui.py` should remain the window orchestrator, not a bucket for every helper.

## Implementation Steps
1. Remove now-extracted helper code from `main_gui.py`.
2. Reorder remaining window code so signal wiring / worker lifecycle / layout orchestration are clearer.
3. Keep comments minimal and only where structure is non-obvious.
4. Preserve current operator behavior.

## Acceptance Criteria
- [ ] `main_gui.py` is materially smaller and orchestration-first
- [ ] worker lifecycle and signal flow remain stable
- [ ] compile/tests/GUI smoke pass

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - `QT_QPA_PLATFORM=offscreen PYTHONPATH=src ./tracker_env/bin/python - <<'PY'
from PySide6.QtWidgets import QApplication
from app.main_gui import MainWindow
app = QApplication([])
win = MainWindow()
print(type(win).__name__)
win.close()
PY`
- Expected result:
  - current desktop flow remains callable and stable

## Risks
- Risk: stage-0 thinning accidentally turns into behavior refactor
- Mitigation: keep extraction low-risk and avoid touching worker/tracking semantics
