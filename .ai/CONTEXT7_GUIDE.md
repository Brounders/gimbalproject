# CONTEXT7_GUIDE.md — Library Documentation via Context7 MCP

## When to Use Context7

**Trigger words (RU):** `как использовать`, `документация`, `пример кода`, `API reference`, `обновить зависимость`
**Trigger words (EN):** `how to use`, `docs for`, `latest API`, `library reference`, `version-specific`, `sdk`

**Activate when:**
- Working with a library's API that is not already in context.
- Task scope in `active_plan.md` contains: `library`, `dependency`, `docs`, `api`, `integration`, `sdk`.
- Upgrading or integrating a new version of a dependency.
- Unsure about exact method signatures, parameter names, or deprecations.

**Skip when:**
- The answer is already in current context (files read, system prompt, memory).
- Using Python stdlib (no docs needed).
- The question is about project-internal code, not a library.

## How to Use

Always follow this two-step pattern — never skip step 1:

**Step 1:** `resolve-library-id` — find the canonical Context7 library ID.
```
Tool: mcp__plugin_context7_context7__resolve-library-id
Input: { "libraryName": "ultralytics" }
```

**Step 2:** `query-docs` — fetch docs for a specific topic only.
```
Tool: mcp__plugin_context7_context7__query-docs
Input: { "context7CompatibleLibraryId": "<id from step 1>", "topic": "ByteTrack tracker arguments" }
```

## Library IDs for This Project

Do NOT hardcode IDs — resolve them fresh each session (IDs can change with versions).
Libraries used in this project that may require Context7:

| Library | Resolve name to use |
|---------|-------------------|
| PySide6 | `"PySide6"` |
| ultralytics | `"ultralytics"` |
| numpy | `"numpy"` |
| opencv-python | `"opencv-python"` or `"cv2"` |
| torch | `"torch"` or `"pytorch"` |
| hailo | `"hailo"` or `"hailo-sdk"` (may not exist — check) |

## What NOT to Do

- Do NOT query broad topics like `"all methods"` or `"full API"` — this loads huge docs wastefully.
- Do NOT call `query-docs` without first calling `resolve-library-id` in the same session.
- Do NOT use Context7 for project-internal code (pipeline.py, config.py, etc.).
- Do NOT use Context7 when the same info is already loaded in context — re-querying is wasteful.
- Do NOT load docs for multiple libraries in parallel unless all are needed simultaneously.

## Example Workflow

Task: "Add error handling to UltralyticsBackend.track_frame() per latest ultralytics API."

1. `resolve-library-id` with `"ultralytics"` → get library ID, e.g. `/ultralytics/ultralytics`.
2. `query-docs` with that ID and `topic: "model.track return value and exceptions"`.
3. Apply the specific exception classes found to the try/except in `ultralytics_backend.py`.
