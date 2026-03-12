# TASK: TASK-20260312-054-pipeline-orchestrator-thinning

Task ID: TASK-20260312-054
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
После extraction задач `052` и `053` истончить `src/uav_tracker/pipeline.py` до orchestration-first структуры, не меняя внешнее поведение.

## Scope
- In scope:
  - `src/uav_tracker/pipeline.py`
  - imports/wiring after extraction
  - small helper relocation if needed to keep module boundaries coherent
- Out of scope:
  - algorithm rewrite
  - `main_gui.py` refactor
  - new feature work

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
  - outputs of `TASK-20260312-052` and `TASK-20260312-053`
- Context:
  - this task is accepted only if `pipeline.py` becomes structurally smaller and clearer, not just shuffled.

## Implementation Steps
1. Remove now-extracted contracts/helpers from `pipeline.py`.
2. Reorder remaining content so orchestration flow is readable.
3. Preserve imports, signatures, and runtime behavior.
4. Add only minimal comments where structural intent is not obvious.

## Acceptance Criteria
- [ ] `pipeline.py` is materially smaller and orchestration-first
- [ ] no runtime/UI behavior changes are introduced intentionally
- [ ] compile/tests/smoke pass on the current local desktop flow

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
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --sources test_videos/cli_smoke_test.mp4 --max-frames 30 --preset default`
- Expected result:
  - current desktop/runtime flow remains callable and stable

## Risks
- Risk: structural thinning turns into accidental behavior rewrite
- Mitigation: accept only extraction/orchestration cleanup, not logic changes
