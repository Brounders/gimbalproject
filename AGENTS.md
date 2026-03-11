# Repository Codex Rules

## Goal
- Keep work predictable and fast across IDE, Cloud delegation, and CI review.

## Working Mode Discipline
- IDE: quick edits, small refactors, short debugging loops.
- Cloud delegation: long-running and heavy multi-step tasks.
- CLI/Actions: repeatable automation and quality gates.
- Do not build the workflow around pixel/UI automation for normal engineering tasks.

## Safety and Scope
- Keep changes minimal and targeted.
- Do not use destructive git commands unless explicitly requested.
- Do not modify `tracker_env/`, `datasets/`, or `runs/` unless the task explicitly requires it.
- Do not add dependencies unless needed for the requested change.

## Human Plan Approval Gate (Mandatory)
- If Human provides direction as `План: ...`, Codex must first produce a detailed plan presentation (expanded scope, steps, validation, risks, priorities).
- Codex must wait for explicit Human confirmation before any delivery to `main`.
- Until confirmation, no `git push origin main` and no implicit merge-to-main actions are allowed.

## Validation Commands
- `lint`: `python3 -m compileall -q python_scripts src app`
- `test`: `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \\( -name \"test_*.py\" -o -name \"*_test.py\" \\) | grep -q .; then pytest -q; else echo \"No pytest suite configured\"; fi'`
- `build`: `bash -lc 'if [ -f ui_web/package.json ]; then cd ui_web && npm run build; else echo \"No ui_web build target\"; fi'`

## Response Format (Required)
- Always answer in this order:
  1. Plan
  2. Changes
  3. Validation
  4. Risks
