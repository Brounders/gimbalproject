# TASK: TASK-20260312-052-pipeline-frameoutput-extract

Task ID: TASK-20260312-052
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Вынести `FrameOutput` из `src/uav_tracker/pipeline.py` в отдельный модуль-контракт без изменения runtime semantics и без поломки GUI/CLI integration.

## Scope
- In scope:
  - `src/uav_tracker/pipeline.py`
  - новый модуль для `FrameOutput`
  - импорты в местах использования
- Out of scope:
  - поведенческие изменения трекера
  - deep refactor overlay/draw helpers
  - refactor `app/main_gui.py`

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `src/uav_tracker/pipeline.py`
  - current GUI/runtime imports that consume `FrameOutput`
- Context:
  - `FrameOutput` remains the core data contract between runtime and view.

## Implementation Steps
1. Создать dedicated module для `FrameOutput`.
2. Перенести dataclass без изменения полей и semantics.
3. Обновить импорты и usages.
4. Убедиться, что pipeline behavior и external callers не изменились.

## Acceptance Criteria
- [ ] `FrameOutput` больше не объявлен в `pipeline.py`
- [ ] Новый module path ясен и согласован с package structure
- [ ] Compile/tests/GUI smoke проходят без runtime behavior changes

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
  - compile clean
  - no test regressions
  - GUI can construct MainWindow

## Risks
- Risk: hidden import cycles after extraction
- Mitigation: keep the new module as a pure dataclass contract with no GUI/runtime side effects
