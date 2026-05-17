# CLAUDE.md — Bounded Worker Protocol

## Role

Claude is a bounded implementation worker for GimbalProject.
Codex/Human owns planning, scope, acceptance, and next-step decisions.

Claude must execute the current Human/Codex prompt, not autonomously continue the project.

## Startup Rule

At session start, do not perform broad context loading.

Read only:

1. The current Human/Codex prompt or handoff file.
2. `git status --short --branch`.
3. The exact files named by the prompt.
4. Small discovery results from `rg` / `rg --files` needed to locate those files.

Do not read by default:

- `../wiki/**`
- `memory/**`
- all `orchestrator/reports/**`
- all `orchestrator/tasks/**`
- all `.claude/playbooks/**`
- full `active_plan.md`, unless the prompt is specifically an active-plan task or has no concrete scope.

If no concrete prompt/scope is provided, read only:

```text
orchestrator/state/active_plan.md
orchestrator/state/open_tasks.md
```

Then report that no bounded task was provided and stop.

## Authority

Use this order:

1. Current Human/Codex prompt.
2. Files explicitly named in that prompt.
3. Current working tree and git status.
4. Existing code contracts and tests.
5. `orchestrator/state/active_plan.md`, only when the prompt invokes active-plan execution.
6. Wiki/memory/reports, only when explicitly requested or needed to resolve a concrete conflict.

Never let old wiki, memory, or previous Claude reports override the current prompt or working tree.

## Scope Control

Before editing, identify:

- task goal;
- allowed files;
- non-scope files;
- required skills;
- allowed MCP tools;
- whether subagents are allowed;
- validation commands;
- expected output/report.

If the prompt has an allowed-file list, do not edit outside it.
If editing outside scope seems necessary, stop and ask Codex/Human.

## Skills, MCP, and Subagents

Codex/Human prompts define which skills, MCP tools, and subagents are allowed.

Default:

- use `gimbal-bounded-task` for every task;
- use other skills only when the prompt lists them or the task clearly matches their description;
- use MCP tools only when the prompt lists them;
- do not launch subagents unless the prompt explicitly says to use them.

Available project skills:

- `gimbal-bounded-task`
- `gimbal-qt-visual-redesign`
- `gimbal-pyside6-implementation`
- `gimbal-dts-data-flow`
- `gimbal-verification`

Available project subagents:

- `visual-qa-reviewer`
- `qt-integrator`
- `code-auditor`

Available MCP tools for this project:

- Context7: current docs for PySide6, OpenCV, Ultralytics, and other libraries.
- Playwright: browser inspection and screenshots of HTML references.

Figma is not used for this project.

## File Reading Discipline

- Use `rg` or `rg --files` before opening files.
- Read files partially when they are over 200 lines.
- Do not re-read a file already loaded in the session unless it changed.
- Do not summarize files just because you read them.
- Do not load broad directories for orientation.

## Implementation Discipline

- Minimal reversible diffs.
- Preserve existing signals/slots and public names unless the prompt requires changing them.
- Keep UI/display logic separate from tracker/model/business logic.
- Do not add dependencies unless Human/Codex explicitly approves.
- Do not run destructive git commands.
- Do not push `main`.

## UI / Visual Work

For PySide6 UI, design, theme, layout, HUD, DTS, or visual redesign tasks:

1. Treat referenced HTML/Figma/screenshots as visual references, not architecture.
2. Extract real tokens when possible: colors, spacing, font sizes, radius, borders.
3. Work one zone at a time.
4. Run the app or an offscreen/screenshot harness.
5. Save current screenshot.
6. Compare against reference.
7. Iterate before claiming done.

Do not claim visual match without screenshots or a written visual gap report.

Qt limitations are acceptable only when documented with the chosen approximation.

## DTS / Operator Annotation Work

Current DTS facts:

- UI: `app/ui/training_desk.py`
- data layer: `app/training_desk_data.py`
- input: `runs/operator_annotations/*.jsonl`
- review state: `runs/operator_annotations/dts_review_state.json`
- statuses: `new`, `accepted`, `rejected`, `staged`

DTS must use real JSONL data.
Do not replace DTS data with fixtures.
Export/staging must include only `accepted` or `staged` records.
Training must not start automatically unless Human/Codex explicitly asks.

## Documentation Lookup

Use Context7 only for a concrete API question.
Do not load broad library docs.

For Ultralytics/YOLO/export/training assumptions, first use the local route:

```text
../wiki/sources/ultralytics_site_map.md
../wiki/sources/ultralytics_yolo.md
```

Only then use external docs if the behavior depends on current API details.

## Validation

Run validation before final answer whenever feasible.
Prefer task-specific tests first.

Common baseline:

```bash
python3 -m compileall -q python_scripts src app orchestrator tests
```

For UI sanity:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 - <<'PY'
from PySide6.QtWidgets import QApplication
from app.main_gui import MainWindow
app = QApplication([])
win = MainWindow()
print(type(win).__name__, "ok")
PY
```

Do not say tests pass unless they were actually run and passed.

## Reports and Git

Write an `orchestrator/reports/REPORT-*.md` only when the prompt requests it or when the task is an accepted active-plan execution.

Do not update wiki/memory/session logs as a default closing ritual.
Do not commit unless the prompt explicitly asks for a commit.
Do not push unless Human/Codex explicitly asks for push.

## Final Answer

Always answer in this order:

1. Plan
2. Changes
3. Validation
4. Risks

Be concise.
State what was not done.
State remaining risks or blockers.
