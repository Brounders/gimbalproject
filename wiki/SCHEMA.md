# Wiki Schema

## Purpose

Persistent domain knowledge base. LLM maintains; human reads and directs.

**Raw sources**: `raw/` — immutable originals (articles, papers, etc.)
**Wiki**: `wiki/` — LLM-maintained markdown pages
**Schema**: this file

## Directory Structure

```
wiki/
  SCHEMA.md       ← this file
  index.md        ← catalog of all pages
  log.md          ← append-only operation log

  sources/        ← one page per ingested source (summary + key claims)
  concepts/       ← how things work (mechanisms, models, frameworks)
  entities/       ← what things are (people, orgs, technologies)
  synthesis/      ← cross-cutting analysis and open questions
```

## Operations

### Ingest (when new file appears in raw/)
1. Read the source.
2. Check `index.md` for related existing pages.
3. Write a summary page in `sources/`.
4. Write or update concept/entity pages for key ideas introduced.
5. Update `index.md`.
6. Append to `log.md`: `## [DATE] ingest | raw/filename — one-line summary`.

### Query
1. Read `index.md` to find relevant pages.
2. Read those pages.
3. Synthesize answer with citations.
4. If the answer is reusable, save it as a synthesis page.
5. Append to `log.md`.

### Lint (periodic)
Check for: contradictions, stale claims, orphan pages, missing cross-references.

## Conventions

- Dates: ISO `YYYY-MM-DD`
- Contradictions: `> ⚠️ CONTRADICTION:`
- Open questions: `> ❓ OPEN:`
- Stale facts: `> ~~stale~~`
- Cross-links: relative markdown links
