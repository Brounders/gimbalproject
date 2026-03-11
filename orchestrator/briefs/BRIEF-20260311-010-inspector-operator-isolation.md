# BRIEF: BRIEF-20260311-010-inspector-operator-isolation

## Summary
- Human approved a narrow UI hardening fix: prevent `inspector_module` from reappearing in the operator layer due to persisted `ui/inspector_visible` settings.

## Scope
- In scope:
  - isolate `inspector_module` from normal operator startup flow;
  - ensure persisted visibility state does not override the operator-shell contract;
  - keep the fix local to `app/main_gui.py`.
- Out of scope:
  - redesign of diagnostics UX;
  - runtime or tracking logic changes.

## Success Criteria
- `inspector_module` stays hidden on normal startup regardless of prior settings.
- Offscreen smoke confirms `inspector_module.isVisible() == False`.
- Expert flow remains intact.
