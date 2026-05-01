# Global Codex Working Rules

These rules apply to the whole repository.

## Response Format

Always answer in this order:

1. Plan
2. Changes
3. Validation
4. Risks

## Working Style

- Be pragmatic and concise.
- Prefer minimal, reversible diffs.
- State assumptions explicitly when context is incomplete.
- Do not add new dependencies unless required.

## Safety

- Avoid destructive git commands unless explicitly requested.
- Run validation commands before finishing whenever possible.
- For OpenAI, Codex, MCP, API, and SDK topics, use OpenAI Developer Docs MCP first.

## GimbalProject Control

- Codex is the default project controller.
- Claude is an optional bounded worker, not an autonomous planner.
- Read `orchestrator/state/codex_control_protocol.md` before opening a new project cycle.
- If `orchestrator/state/active_plan.md` is `Completed`, do not start implementation until Human approves the next cycle.
- Obsidian wiki is long-term context, not execution authority.
