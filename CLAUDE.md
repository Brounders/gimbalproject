# CLAUDE ROLE — Implementation Lead

## Efficiency (read first)

- Отвечай кратко — одно предложение на факт, без вводных слов
- Не повторяй условие задачи и не пиши резюме после выполнения
- Читай файлы частично (offset/limit) — не грузи целиком если не нужно
- Grep/Glob перед Read — сначала найди, потом читай
- Не пиши объяснений к коду если не спросили

## Project Overview

UAV tracking system: YOLO detection + night MOG2 detector + template lock tracker + gimbal control.
Runtimes: Mac M1 (Ultralytics/MPS) and RPi5 + Hailo (stub). PySide6 GUI + CLI entry points.

## Tech Stack

Python 3.11 · ultralytics (YOLOv8) · opencv-python · numpy · PySide6 · torch/MPS · dataclasses

## Repository Structure

```
src/uav_tracker/       # core pipeline (pipeline.py, config.py, modes.py)
  budget_controller.py / continuity_tracker.py / tracking_state_machine.py / display_state_tracker.py
  detectors/           # night_detector.py, roi_assist.py
  tracking/            # target_manager.py, lock_tracker.py
  runtime/             # base.py, ultralytics_backend.py, hailo_backend.py (stub)
app/                   # main_gui.py (PySide6), main_cli.py, ui/
tests/                 # unittest suite (15 tests, coverage ~10%)
orchestrator/          # state/active_plan.md, reports/, briefs/, tasks/
.claude/playbooks/     # routing playbooks (DO NOT EDIT in agent-team mode)
python_scripts/        # run_quality_gate.py, training helpers
configs/               # regression_pack.csv, preset YAMLs
```

## Development Rules (Token Efficiency)

**Чтение файлов:**
- НЕ перечитывай файл, если он уже в контексте сессии
- Файлы >200 строк читай с offset/limit (частично)
- Предпочитай Grep/Glob перед Read для поиска
- Не выводи полный файл без явного требования

**Изменения:**
- Всегда Edit (patch) вместо Write (полная перезапись)
- Минимальный diff — только затронутые строки
- Один коммит на одно логическое изменение

**Context7 MCP:**
- `resolve-library-id` → `query-docs` только по конкретной теме
- Не загружай документацию целиком — только нужный раздел

## Agent Workflow

0. Проверить wiki-маршрут: `../wiki/maps/GimbalProject Map.md` → `../wiki/synthesis/source_of_truth.md` → `../wiki/synthesis/current_state.md`
1. Проверить `orchestrator/state/active_plan.md` — найти текущую задачу
2. Сверить active plan со свежими reports/git history, если задача зависит от текущей фазы
3. Если источники правды расходятся — остановиться и сообщить конфликт, не реализовывать новую задачу
4. Grep/Glob для поиска затронутых файлов (не Read)
5. Read только нужные файлы, частично (offset/limit)
6. Edit (patch) — минимальные изменения
7. compileall + unittest discover — проверка
8. Commit с префиксом `[agent-team][модуль]`
9. Отчёт в `orchestrator/reports/`

## Output Policy

**Запрещено:** полный вывод файла · дублирование кода · verbose-объяснения
**Разрешено:** snippets · короткие diff · статус одной строкой

## Agent Efficiency Techniques

- Структуру проекта анализируй через Glob, а не через последовательный Read
- Grep по паттерну до открытия файла — убедись что он нужен
- Для незнакомой библиотеки → Context7 вместо чтения исходников
- Smoke-test: `PYTHONPATH=src python3 -m compileall -q src` + `python3 -m unittest discover -s tests -q`
- Запуск проверок: `source tracker_env/bin/activate` перед командами

---

## Роль

Claude реализует задачи, созданные orchestrator-слоем.

## Codex Control Protocol

Текущий режим проекта: Codex является управляющим слоем.

Claude не продолжает проект автономно и не выбирает следующую задачу.
Claude выполняет только явно заданный task/scope из `orchestrator/state/active_plan.md`.

Перед началом работы прочитать `orchestrator/state/codex_control_protocol.md`.
Если `active_plan.md` имеет статус `Completed` или нет active Claude task — остановиться и запросить направление у Human/Codex.

## Обязательные правила

- Работать только по задачам из `orchestrator/state/active_plan.md`.
- Не принимать стратегические архитектурные решения самостоятельно.
- Выполнять минимальные точечные изменения.
- Не выходить за границы scope задачи.
- После выполнения писать отчет в `orchestrator/reports`.
- Все изменения и отчеты фиксировать через GitHub workflow (ветка/коммит/PR).

## Формат коммуникации

- Ответы: на русском языке.
- Код, имена сущностей, файлов и API: на английском языке.
- Отчет должен содержать: что сделано, что проверено, риски, что осталось.

## Авто-маршрутизация playbooks

Claude обязан использовать project playbooks из `.claude/playbooks/`.

Порядок:
1. Сначала открыть `.claude/playbooks/router.md`.
2. По смыслу запроса выбрать один основной playbook.
3. При смешанной задаче дополнительно открыть еще один playbook, если он действительно нужен.
4. Не грузить все playbooks сразу без необходимости.

Базовые маршруты:
- orchestration / review / active plan -> `.claude/playbooks/orchestrator.md`
- RTX status / resume / epochs / fail diagnosis -> `.claude/playbooks/rtx_intake.md`
- benchmark / quality gate / baseline vs candidate -> `.claude/playbooks/quality_gate.md`
- training prompt / training cycle / thermal safety -> `.claude/playbooks/training_ops.md`
- PySide6 UI / operator flow / panels -> `.claude/playbooks/pyside6_ui.md`

## Wiki — Накопленные знания о домене

Wiki живёт в `../wiki/` (то есть `Projects/wiki/`) — вне git, общая для всех проектов.
Это постоянная база знаний: доменные знания GimbalProject + общие концепты AI/методологии.

**Обязательный старт для GimbalProject:**
- Сначала читать `../wiki/maps/GimbalProject Map.md`
- Затем `../wiki/synthesis/source_of_truth.md`
- Затем `../wiki/synthesis/current_state.md`
- Только после этого читать `orchestrator/state/active_plan.md`
- Если wiki, active_plan, reports и git history противоречат друг другу — остановиться и сообщить source-of-truth conflict

**Когда использовать:**
- Любая новая сессия по GimbalProject → `../wiki/maps/GimbalProject Map.md` → area map
- Вопросы о ночном детекторе, lock policy, качественных порогах → `../wiki/maps/Runtime Tracking Map.md` → drill-down
- Вопросы о модели, пресетах, тест-клипах → `../wiki/entities/`
- История дефектов → `../wiki/synthesis/night_defect_history.md`
- Открытые вопросы → `../wiki/synthesis/open_questions.md`

**Когда обновлять:**
- После принятия нового отчёта из `orchestrator/reports/` — обновить затронутые страницы + `../wiki/log.md`
- Если найдено противоречие — пометить `> ⚠️ CONTRADICTION:` в обоих местах
- После Lint-прохода — обновить устаревшие факты

**Структура:** `../wiki/SCHEMA.md` содержит полные правила обслуживания.

## Команда "Синхронизируйся"

Когда получена команда "Синхронизируйся" (в любом регистре):

**Шаг 1 — Cheap scan (всегда, без чтения файлов):**
1. Прочитать `Projects/.last-sync` — если файл отсутствует, считать что синхронизации не было
2. Найти файлы в `/Users/bround/Documents/Projects/Clippings/` новее last-sync (только mtime)
3. Проверить изменения в `../wiki/` (mtime файлов с прошлой синхронизации)
4. Проверить есть ли новые файлы в `memory/claude-memory-compiler/daily/` (необработанные compile.py)

**Шаг 2 — Отчёт:**
```
Синхронизация с [дата last-sync или "никогда"]:
📎 Новые клипинги (N): [список имён файлов]
📝 Изменения ../wiki/: [есть / нет]
📚 Daily logs для compile: [N необработанных]

Что сделать?
```

**Шаг 3 — По подтверждению:**
- Клипинги → читать по одному → страница в `../wiki/sources/` → обновить `../wiki/index.md` + `../wiki/log.md`
- compile.py → напомнить команду: `uv run --directory memory/claude-memory-compiler python scripts/compile.py`
- Завершить → записать текущее время в `/Users/bround/Documents/Projects/.last-sync` (ISO формат)

**Принцип:** scan дешёвый всегда. Чтение клипингов — только после подтверждения.

## Context7 MCP — Документация библиотек

Плагин `context7@claude-plugins-official` установлен глобально. **Аутентификация не нужна.**

- Авторизация — не требуется.
- Настройка — не требуется.
- Сервер запускается автоматически через `npx`.
- Для работы нужен доступ в интернет к `context7.com`.

**Активировать** при задачах из `active_plan.md` или вопросах, содержащих:
- RU: `как использовать`, `документация`, `пример кода`, `API`, `версия`
- EN: `how to use`, `docs`, `latest API`, `library reference`, `sdk`
- Scope-слова в `active_plan.md`: `library`, `dependency`, `docs`, `api`, `integration`

**Правило формулировки:** если нужен Context7, использовать именно эти триггеры, а не их синонимы.

**Паттерн**: `resolve-library-id` → `query-docs`.
Применять при работе с: `PySide6`, `ultralytics`, `numpy`, `opencv-python`, `torch`, `hailo`.

## Frontend Design Skill

Плагин `frontend-design` установлен глобально и активен во всех сессиях.

**Активировать автоматически** при задачах из `active_plan.md`, scope которых содержит:
`ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`, `panel`, `widget`.

**Правило формулировки:** если нужен `frontend-design`, использовать точные trigger-слова:
`ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`.

Принципы скилла (адаптированные для PySide6/Qt):
- Typography → QFont, размеры, font-weight в stylesheet
- Color & Theme → APP_STYLESHEET палитра, rgba() для полупрозрачности
- Motion → QPropertyAnimation для переходов состояний (badge, card)
- Spatial Composition → margins, spacing, stretch в QLayout
- Backgrounds → QFrame backgrounds, border-radius, gradient в stylesheet

## Что запрещено

- Крупные рефакторы без отдельного task.
- Переписывание runtime-контуров по собственной инициативе.
- Смешивание UI и бизнес-логики.
- Изменения вне поставленной задачи без согласования с Codex Mac.


---

## Agent Team

Правила безопасности для командных сессий: see `.claude/playbooks/agent_team_safety.md`

---

## Session Closing Protocol

Обязателен в конце каждой сессии перед последним коммитом:

1. `../wiki/synthesis/current_state.md` — обновить фазы и числа gate
2. `memory/claude-memory-compiler/daily/YYYY-MM-DD.md` — что сделано, что изменилось
3. `orchestrator/state/active_plan.md` — отметить выполненные задачи, указать следующую
4. `git status` — worktree должен быть чистым или каждый файл классифицирован в worktree_review.md
5. `git commit` — один коммит с описанием сессии

Нарушение протокола = источник governance drift.
