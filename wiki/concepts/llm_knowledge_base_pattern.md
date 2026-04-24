---
title: LLM Knowledge Base Pattern (Karpathy)
aliases: [karpathy wiki pattern, llm wiki, knowledge compiler]
tags: [meta, knowledge-management, architecture]
sources: [raw/claude-memory-compiler/README.md, raw/claude-memory-compiler/AGENTS.md]
created: 2026-04-24
updated: 2026-04-24
---

# LLM Knowledge Base Pattern

A pattern for building a persistent, self-maintaining knowledge base where an LLM acts as both compiler and retrieval engine. Described by Andrej Karpathy; implemented as [claude-memory-compiler](../sources/claude_memory_compiler.md).

## Key Points

- **Three-layer architecture**: raw sources (human-owned, append-only) → compiled wiki articles (LLM-owned) → schema/AGENTS.md (jointly evolved)
- **LLM as compiler**: the model reads raw input and writes structured articles — same input/output loop as a traditional compiler
- **Index-guided retrieval**: at personal scale (50–500 articles), LLM reads a structured `index.md` and reasons over it — outperforms vector similarity because the model understands intent, not just word overlap
- **RAG becomes necessary only at ~2,000+ articles** when the index no longer fits in context
- **Compounding loop**: every query that writes back to the KB (`--file-back`) makes the next query smarter

## Details

### Three Layers

| Layer | Directory | Analogy | Who Owns |
|-------|-----------|---------|----------|
| Raw source | `daily/` or `raw/` | Source code | Human (append-only) |
| Compiled wiki | `knowledge/` | Executable | LLM (writes/maintains) |
| Schema | `AGENTS.md` | Compiler spec | Human + LLM evolve together |

The key invariant: humans never edit compiled articles directly — they edit raw sources and re-run the compiler. This keeps the wiki consistent and the compilation traceable.

### Why Not RAG?

Vector search finds *similar words*; LLM reading an index finds *relevant concepts*. At personal scale the index fits in context and the LLM's understanding of the question domain dominates. RAG only wins when the knowledge base is too large for the index to fit in context.

### Operations

- **ingest** (`compile.py`): Read raw source → extract 3-7 concepts → create/update articles → update index → update log
- **query** (`query.py`): Load index → LLM selects relevant articles → synthesize answer; optionally write answer back as QA article
- **lint** (`lint.py`): 7 structural checks (broken links, orphan pages, stale articles, missing backlinks, sparse articles) + 1 LLM check (contradictions)

### Incremental Compilation

SHA-256 hashes in `state.json` enable incremental recompilation — only changed raw files trigger a new compile pass. This keeps cost bounded at $0.45–0.65 per daily log.

## Related Concepts

- [claude_memory_compiler](../sources/claude_memory_compiler.md) — concrete implementation for Claude Code conversations
- [alignment_failure_modes](alignment_failure_modes.md) — example of a concept article produced by this pattern applied to AI 2027
- [intelligence_explosion](intelligence_explosion.md) — another example concept article

## Sources

- `raw/claude-memory-compiler/README.md` — quick-start and architecture overview
- `raw/claude-memory-compiler/AGENTS.md` — full technical spec: article formats, operations, hook system, costs
