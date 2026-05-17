---
name: gimbal-pyside6-implementation
description: Use for implementing GimbalProject desktop UI in PySide6: MainWindow, app/ui widgets, layout_builders, theme.py, video_stage, cards, signal/slot wiring, and safe UI refactors.
---

# Gimbal PySide6 Implementation

## Scope

Typical files:

- `app/main_gui.py`
- `app/ui/layout_builders.py`
- `app/ui/theme.py`
- `app/ui/video_stage.py`
- `app/ui/cards.py`
- `app/ui/training_desk.py`
- new small files under `app/ui/` when extraction reduces risk.

## Rules

- Preserve existing widget attributes used by other modules.
- Preserve `_wire_actions()` contracts unless the task explicitly changes them.
- Preserve `VideoStage` click and bbox mapping.
- Keep tracker/model/runtime logic out of widgets.
- Keep expert-only controls out of the normal operator path when possible.
- Prefer small helper widgets over one giant rewrite.

## Mandatory Checks

Before editing, search for references to renamed/moved attributes:

- `rg "_rp_|_tc_|dts_btn|start_btn|stop_btn|eval_btn|operator_confirm_btn|operator_release_btn|video_stage" app tests`

For UI sanity, run when possible:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 - <<'PY'
from PySide6.QtWidgets import QApplication
from app.main_gui import MainWindow
app = QApplication([])
win = MainWindow()
print(type(win).__name__, "ok")
PY
```

If this fails, fix or report the exact failure.
