# Wiki Schema — GimbalProject

## Purpose

Единая постоянная база знаний: доменные знания о проекте + внешние источники.
LLM поддерживает wiki; Bround читает и направляет.

**Сырые источники (immutable):**
- Доменные: `orchestrator/reports/`, `orchestrator/briefs/`, `orchestrator/state/`, `OPERATOR_BASELINE.md`
- Внешние: `memory/` — статьи, инструменты, исследования

**Wiki** (LLM-maintained): `wiki/` — этот каталог

**Schema** (этот файл): соглашения, форматы страниц, операции

---

## Directory Structure

```
wiki/
  SCHEMA.md          ← этот файл
  index.md           ← каталог всех страниц
  log.md             ← append-only хронологический лог

  concepts/          ← как что-то работает (механизмы, алгоритмы, политики, паттерны)
    detection_pipeline.md
    lock_policy.md
    quality_gates.md
    runtime_hardening.md
    training_strategy.md
    intelligence_explosion.md
    alignment_failure_modes.md
    llm_knowledge_base_pattern.md

  entities/          ← что что-то представляет собой (модели, конфиги, данные)
    models.md
    presets.md
    test_clips.md

  decisions/         ← зафиксированные решения и их обоснование
    model_decisions.md

  synthesis/         ← сквозной анализ и открытые вопросы
    current_state.md
    open_questions.md
    night_defect_history.md

  sources/           ← краткие сводки внешних источников
    ai_2027.md
    claude_memory_compiler.md
```

---

## Page Format

```markdown
# Title

> One-line summary (используется в index.md)

## Section
...content...

## Related
- [page](../concepts/page.md) — почему связано
```

---

## Operations

### Ingest — новый отчёт из orchestrator/
1. Прочитать отчёт.
2. Определить затронутые страницы вики (через index.md).
3. Обновить каждую страницу — исправить факты, добавить измерения, отметить противоречия.
4. Добавить запись в `log.md`: `## [DATE] ingest | REPORT-ID — one-line summary`.
5. Обновить `index.md` если созданы новые страницы.

### Ingest — новый внешний источник из memory/
1. Прочитать источник.
2. Написать страницу-сводку в `sources/`.
3. Написать или обновить концепт-страницы для ключевых идей.
4. Обновить `index.md`.
5. Добавить запись в `log.md`.

### Query
1. Прочитать `index.md`, найти релевантные страницы.
2. Прочитать их.
3. Синтезировать ответ со ссылками.
4. Если ответ ценный — сохранить как страницу synthesis/.

### Lint (периодически)
Проверить: противоречия между страницами, устаревшие факты, orphan-страницы,
открытые вопросы которые уже закрыты, важные концепты без страниц.

---

## Conventions

- **Даты**: ISO `YYYY-MM-DD`
- **AP-ссылки**: всегда полный ID, например `AP-025`
- **Числовые значения**: всегда с контекстом (какой клип, какой режим)
- **Противоречия**: `> ⚠️ CONTRADICTION:`
- **Устаревшие факты**: `> ~~stale as of AP-XXX~~`
- **Открытые вопросы**: `> ❓ OPEN:`
- **Перекрёстные ссылки**: markdown-ссылки `[text](../entities/models.md)`

---

## Authorship

LLM пишет и поддерживает wiki. Bround читает.
Bround: поставляет новые артефакты, задаёт вопросы, одобряет стратегию.
Claude: извлекает, синтезирует, поддерживает актуальность.
