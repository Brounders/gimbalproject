# Project Compass

## Mission
- Локальная desktop-программа для обнаружения и сопровождения БПЛА в `day / night / IR`.
- Будущий целевой перенос: `RPi5 + Hailo`.

## Product Boundary
- Основной продукт: локальное PySide6-приложение и локальный runtime.
- Временный operational слой: `RTX + GitHub + automation`.
- Временный слой не должен становиться архитектурным центром проекта.

## Current Truth
- Локальная структура и baseline governance уже приведены в рабочее состояние.
- `pipeline.py` прошел `stage-1 split`.
- `main_gui.py` прошел `stage-0 split`.
- Local quality enforcement и problem-pack gate уже существуют.
- RTX training conveyor доказан как рабочий operational smoke-run.

## Main Remaining Product Risk
- Главный незакрытый боевой дефект: large-target night behavior.
- Конкретно: `night_ground_large_drones`.
- Симптомы: высокий `false_lock_rate`, высокий `active_id_changes_per_min`, нестабильный reacquire/release ночью.

## Current Model Position
- Последняя curriculum-ветка `drone-bird-yolo` не стала baseline-кандидатом.
- Текущий вердикт по этой ветке: `reject_and_reset_training_strategy`.
- Новый training cycle не открывать без отдельного утвержденного плана.

## Current Working Priorities
1. Добить runtime quality на `large-target night`.
2. Держать baseline/candidate decision loop жестким и локально воспроизводимым.
3. Не открывать новый большой refactor до закрытия боевого runtime-дефекта.

## What Is Not The Priority Now
- Новый UI redesign.
- Новый большой architecture refactor.
- Hailo / RPi migration.
- Автоматизация RTX как центр проекта.
- Новый длинный training cycle без отдельного решения.

## Canonical State Files
- Главный execution context: `orchestrator/state/active_plan.md`
- История и reviewer snapshots: `orchestrator/state/project_state.md`
- Принятые инженерные решения: `ENGINEERING_DECISIONS.md`
- Текущая активная фаза: `CURRENT_PHASE.md`
