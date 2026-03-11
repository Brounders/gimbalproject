# TASK: TASK-20260311-025-inspector-expert-isolation

Task ID: TASK-20260311-025
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Полностью убрать `inspector_module` из operator-layer и гарантировать, что он не появляется повторно из сохраненных UI-настроек.

## Scope
- In scope:
  - убрать восстановление `ui/inspector_visible` в обычном operator flow;
  - гарантировать, что `inspector_module` остается скрытым в основном окне;
  - если диагностика нужна, доступ к ней должен идти только через expert-only path, а не через persisted operator layout state.
- Out of scope:
  - новый редизайн diagnostics;
  - изменения tracking/runtime logic.

## Files
- `app/main_gui.py`

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `QT_QPA_PLATFORM=offscreen PYTHONPATH=src ./tracker_env/bin/python - <<'PY'`
- `from PySide6.QtWidgets import QApplication`
- `from app.main_gui import MainWindow`
- `app = QApplication([]); win = MainWindow(); print(win.inspector_module.isVisible()); win.close(); app.quit()`
- `PY`

## Acceptance Criteria
- [ ] `inspector_module` не восстанавливается в operator-layer из сохраненных настроек.
- [ ] После старта окна в обычном режиме `inspector_module.isVisible()` == `False`.
- [ ] Expert-контур не ломается.
