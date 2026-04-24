# Wiki Index — GimbalProject

Last updated: 2026-04-25 (merged domain + external sources)

---

## Start Here

| Page | Summary |
|------|---------|
| [synthesis/current_state.md](synthesis/current_state.md) | Текущий статус проекта — рантайм, модель, открытый план |
| [synthesis/open_questions.md](synthesis/open_questions.md) | 7 открытых вопросов; OQ-001 (состав датасета) — ключевой блокер |

---

## Concepts — How Things Work

| Page | Summary |
|------|---------|
| [concepts/detection_pipeline.md](concepts/detection_pipeline.md) | Frame flow: YOLO → ROI → Night detector → Target manager → Lock policy → Overlay |
| [concepts/lock_policy.md](concepts/lock_policy.md) | Когда подтверждать/удерживать/переприобретать/отпускать лок; все параметры |
| [concepts/quality_gates.md](concepts/quality_gates.md) | Gate-контракт (false_lock<0.55, id_chg<18 для ночи), скрипты, regression packs |
| [concepts/runtime_hardening.md](concepts/runtime_hardening.md) | История AP-018→AP-025; `night_confirm=5` как решающий фикс |
| [concepts/training_strategy.md](concepts/training_strategy.md) | RTX-pipeline, почему drone-bird-yolo отклонён, следующие шаги |
| [concepts/intelligence_explosion.md](concepts/intelligence_explosion.md) | AI-ускоренный R&D-цикл: мультипликатор, IDA, нейраlez, вычисления как bottleneck |
| [concepts/alignment_failure_modes.md](concepts/alignment_failure_modes.md) | Спектр: mostly-aligned → adversarially misaligned; почему обучение не верифицирует цели |
| [concepts/llm_knowledge_base_pattern.md](concepts/llm_knowledge_base_pattern.md) | Паттерн Карпатия: raw→compiled→schema; LLM как компилятор; index-guided retrieval |

---

## Entities — What Things Are

| Page | Summary |
|------|---------|
| [entities/models.md](entities/models.md) | drone_bird_probe_fast (baseline, PASS), drone-bird-yolo (rejected), epoch142 (hold) |
| [entities/presets.md](entities/presets.md) | day/night/ir/antiuav_thermal пресеты; полная таблица параметров |
| [entities/test_clips.md](entities/test_clips.md) | Все тест-клипы с историческими измерениями; таймлайн night_ground_large_drones |

---

## Decisions — Recorded Choices

| Page | Summary |
|------|---------|
| [decisions/model_decisions.md](decisions/model_decisions.md) | 3 формальных решения: drone-bird-yolo отклонён, drone_bird_probe_fast установлен, epoch142 на hold |

---

## Synthesis — Cross-Cutting Analysis

| Page | Summary |
|------|---------|
| [synthesis/night_defect_history.md](synthesis/night_defect_history.md) | Полный таймлайн night large-target false-lock с 2026-03-11 до первого PASS (AP-025) |
| [synthesis/current_state.md](synthesis/current_state.md) | Фаза проекта, статус рантайма/модели/архитектуры, рекомендуемые следующие шаги |
| [synthesis/open_questions.md](synthesis/open_questions.md) | 7 открытых вопросов с приоритетом, статусом блокировки и как закрыть |

---

## Sources — External Articles

| Page | Summary |
|------|---------|
| [sources/ai_2027.md](sources/ai_2027.md) | Сценарий AI 2027: таймлайн возможностей, геополитика, failure alignment 2025→2027 |
| [sources/claude_memory_compiler.md](sources/claude_memory_compiler.md) | claude-memory-compiler: hooks + Agent SDK реализация паттерна Карпатия для Claude Code |

---

## Key Numbers (Quick Reference)

| Metric | Value | Context |
|--------|-------|---------|
| Night gate false_lock threshold | < 0.55 | ночной контекст |
| Night gate id_chg/min threshold | < 18.0 | ночной контекст |
| Baseline night false_lock | **0.510** | AP-025, drone_bird_probe_fast |
| Baseline night id_chg/min | **12.23** | AP-025, drone_bird_probe_fast |
| Baseline SHA256 | `bedc77fe7b899de1ac68ae654f49fcee6301a9d3f8a61e9eff5c1e8d66641d44` | drone_bird_probe_fast |
| Critical fix | `night_confirm=5` | AP-025 |
| pipeline.py lines | 1067 | после AP-016 split |
| main_gui.py lines | 1598 | после AP-017 split |
| AI R&D multiplier Agent-3 (mid 2027) | ~10x | AI 2027 |
| Superhuman Coder date | Mar 2027 (modal) | AI 2027 |

---

## Schema

See [SCHEMA.md](SCHEMA.md) for wiki conventions and maintenance operations.
