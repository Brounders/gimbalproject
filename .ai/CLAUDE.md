# CLAUDE.md — AI Agent Reference

## Project Overview
UAV tracking system using YOLOv8 + night/IR detector + lock-policy FSM.
Dual runtime: Mac M1 (Ultralytics/MPS) and RPi5+Hailo (stub). PySide6 GUI.

## Tech Stack
- Python 3.11 | ultralytics (YOLOv8) | opencv-python | numpy | torch | PySide6

## Repository Structure
```
src/uav_tracker/     — core tracker (pipeline, config, detectors, tracking, runtime)
src/utils/           — geometry helpers (iou, etc.)
app/                 — main_gui.py (PySide6, ~1600 lines), main_cli.py, ui/
tests/               — 48 unittest cases (~15% coverage)
orchestrator/        — active_plan.md, reports/, briefs/
configs/             — regression_pack.csv, preset YAMLs
python_scripts/      — quality gate, training helpers
.ai/                 — agent references (this dir)
tracker_env/         — Python venv (do not commit)
```

## Development Rules for AI Agents

### File Access
- NEVER re-read a file already loaded in current context.
- Files >200 lines: use `offset` + `limit` params for partial reads.
- Use Grep/Glob BEFORE Read for discovery — locate before loading.
- Use Edit (patch diffs) not Write (full rewrite) for existing files.

### Library Docs
- Context7: always `resolve-library-id` → then `query-docs` with a specific topic.
- Never load broad/full docs — query only the exact API surface needed.
- Skip Context7 if the answer is already in context or stdlib.

### Scope
- Touch only files listed in the task scope. Nothing else.
- No dependency changes (requirements.txt, pyproject.toml) without human approval.
- No public API renames, file deletes, or module moves without approval.

## Agent Workflow
1. Read task description and identify exact files in scope.
2. Grep/Glob to confirm paths before reading.
3. Read only the relevant section (use offset/limit on large files).
4. Form a minimal diff — Edit for patches, Write only for new files.
5. Run smoke test: `source tracker_env/bin/activate && PYTHONPATH=src python3 -m unittest discover -s tests -q`
6. Commit: `[agent-team][module] short description`.
7. Write report to `orchestrator/reports/REPORT-<task>-<date>.md`.

## Output Policy

**Banned:**
- Prose summaries of code you just read (recap = noise).
- Emojis in any file or commit message.
- Full file rewrites when a patch is sufficient.
- Strategic architecture decisions — escalate to orchestrator.

**Allowed:**
- Load-bearing code snippets (bugs found, signatures changed).
- Absolute file paths.
- Numbered action lists.

## Agent Efficiency Techniques
- Parallelize independent Read/Grep calls in one message.
- Prefer `output_mode: files_with_matches` in Grep for discovery; use `content` only when line text is needed.
- Prefer `Glob` for finding files by name pattern over `find` via Bash.
- Chain `&&` in Bash for sequential dependent commands; parallelize independent ones.
- Commit after each logical change — small commits are easier to revert.
- If a task has >3 files in scope, list them all before starting edits.
