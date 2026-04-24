---
source: raw/claude-memory-compiler/
url: https://github.com/coleam00/claude-memory-compiler
ingested: 2026-04-24
author: coleam00
---

# claude-memory-compiler

> Working implementation of Karpathy's LLM wiki pattern for Claude Code: conversations automatically compile into a searchable knowledge base via hooks + Claude Agent SDK.

## Core Idea

Instead of ingesting external articles, the raw data is your **own Claude Code conversations**.
When a session ends, hooks capture the transcript → background process extracts knowledge → appends to a daily log → compile.py turns daily logs into structured wiki articles.

```
Conversation → SessionEnd/PreCompact hooks → flush.py (extract)
    → daily/YYYY-MM-DD.md → compile.py → knowledge/concepts/, connections/, qa/
        → SessionStart injects index → next session "remembers" everything
```

## Architecture: The Compiler Analogy

| Layer | Directory | Analogy | Ownership |
|-------|-----------|---------|-----------|
| Raw source | `daily/` | Source code | Human (append-only) |
| Compiled | `knowledge/` | Executable | LLM (writes/maintains) |
| Schema | `AGENTS.md` | Compiler spec | Human + LLM evolve together |

## Hook System

Three hooks configured in `.claude/settings.json`:

| Hook | Event | What It Does | API Calls |
|------|-------|-------------|-----------|
| `session-start.py` | SessionStart | Injects `knowledge/index.md` + recent daily log as context | None |
| `session-end.py` | SessionEnd | Reads transcript → extracts context → spawns `flush.py` detached | None |
| `pre-compact.py` | PreCompact | Same as session-end; safety net for long sessions before compaction | None |

### Why PreCompact + SessionEnd?
Long sessions may trigger multiple auto-compactions. Without PreCompact, intermediate context is lost before SessionEnd fires.

### Background Process (flush.py)
- Spawned detached: `start_new_session=True` (Mac/Linux), `CREATE_NO_WINDOW` (Windows)
- Sets `CLAUDE_INVOKED_BY=memory_flush` env var (recursion guard — prevents hooks re-firing)
- Calls Claude Agent SDK: `query()` with `allowed_tools=[]`, `max_turns=2`
- Claude decides what's worth saving → appends structured bullets to `daily/YYYY-MM-DD.md`
- **End-of-day auto-compile**: If past 6 PM and daily log changed → spawns `compile.py` detached

### JSONL Transcript Parsing
```python
entry = json.loads(line)
msg = entry.get("message", {})
role = msg.get("role", "")   # "user" or "assistant"
content = msg.get("content", "")  # string or list of content blocks
```

## Key Scripts

### compile.py — The Compiler
- Uses `claude-agent-sdk` async `query()` with `allowed_tools=["Read","Write","Edit","Glob","Grep"]`
- `permission_mode="acceptEdits"` — auto-approves all file writes
- Gives Claude: AGENTS.md schema + current index + all existing articles + daily log
- Claude extracts 3-7 concepts per log, creates/updates articles, updates index + log
- Incremental: SHA-256 hashes in `state.json`, skips unchanged files

### query.py — Index-Guided Retrieval
- Loads entire KB into context (index + all articles)
- No RAG, no embeddings — LLM reads index, selects relevant articles, synthesizes answer
- `--file-back`: saves answer as `knowledge/qa/` article (compounding loop)

### lint.py — 7 Health Checks

| Check | Type | What It Catches |
|-------|------|----------------|
| Broken links | Structural | `[[wikilinks]]` to non-existent articles |
| Orphan pages | Structural | Zero inbound links |
| Orphan sources | Structural | Daily logs not yet compiled |
| Stale articles | Structural | Source log changed since compilation |
| Missing backlinks | Structural | A→B but B↛A |
| Sparse articles | Structural | Under 200 words |
| Contradictions | LLM | Conflicting claims across articles |

`--structural-only` skips the LLM check (free).

## Article Formats

### Concept Article (`knowledge/concepts/`)
YAML frontmatter: `title`, `aliases`, `tags`, `sources`, `created`, `updated`
Sections: Core explanation → Key Points → Details → Related Concepts → Sources

### Connection Article (`knowledge/connections/`)
For non-obvious relationships between 2+ concepts.
Frontmatter: `title`, `connects: [concept-x, concept-y]`, `sources`

### Q&A Article (`knowledge/qa/`)
Filed answers from query runs. The compounding loop: every question makes the KB smarter.

## Costs

| Operation | Cost |
|-----------|------|
| compile.py (per daily log) | $0.45–0.65 |
| flush.py (per session) | $0.02–0.05 |
| query.py (no file-back) | $0.15–0.25 |
| query.py (with --file-back) | $0.25–0.40 |
| lint.py (full) | $0.15–0.25 |
| lint.py (--structural-only) | $0.00 |

**No API key needed** — uses Claude Code credentials at `~/.claude/.credentials.json`.
Personal use of Claude Agent SDK is covered under Claude subscription (Max/Team/Enterprise).

## Why No RAG?

At personal scale (50–500 articles), the LLM reading a structured `index.md` outperforms cosine similarity.
- LLM understands what you're *really* asking
- Vector search finds *similar words*, not *relevant concepts*
- RAG becomes necessary only at ~2,000+ articles (index exceeds context window)

## Dependencies

```
claude-agent-sdk >= 0.1.29
python-dotenv >= 1.0.0
tzdata >= 2024.1
Python 3.12+, managed by uv
```

## State Tracking

- `scripts/state.json`: ingested logs (SHA-256 + timestamp + cost), query count, last lint, total cost
- `scripts/last-flush.json`: flush deduplication (session_id + timestamp, 60-second dedup window)

## Relation to Karpathy Pattern

This is a concrete implementation of [[concepts/llm_knowledge_base_pattern]] with one key adaptation:
- **Karpathy**: raw sources = web articles you clip
- **claude-memory-compiler**: raw sources = your own Claude Code conversations

The three-layer architecture (raw → wiki → schema) is identical.

## Related

- [llm_knowledge_base_pattern.md](../concepts/llm_knowledge_base_pattern.md) — the general pattern
- [ai_2027.md](ai_2027.md) — another source in the same wiki
