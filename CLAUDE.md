# CLAUDE ROLE — Implementation Lead

## Роль

Claude реализует задачи, созданные orchestrator-слоем.

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

## Agent Team — правила безопасности (для командных сессий)

> Этот блок актуален ТОЛЬКО при работе в режиме agent team.
> Основная сессия Claude Code его игнорирует — он не влияет на обычную работу.

### Изоляция через git

1. Agent team **ВСЕГДА** работает на отдельной ветке `agent-team/<дата>-<описание>`.
2. **ЗАПРЕЩЕНО** работать на `main`, `master` или рабочей ветке основной сессии.
3. **ЗАПРЕЩЕНО** делать merge/rebase/push в основную ветку. Только Bround решает, что мержить.
4. Первое действие при старте — `git checkout -b agent-team/...` от актуального HEAD.

### Обратимость

5. Коммит после **каждого** логического изменения. Формат: `[agent-team][модуль] описание`.
6. **ЗАПРЕЩЕНО** удалять файлы, переименовывать модули, менять публичные API без одобрения Bround.
7. **ЗАПРЕЩЕНО** менять зависимости (requirements.txt, pyproject.toml) без одобрения Bround.

### Совместимость с основной сессией

8. **НЕ трогать** файлы вне scope текущей задачи.
9. Файлы `agents/`, `QUICKSTART.md` — инфраструктура команды, не код проекта.
10. Файлы `orchestrator/`, `.claude/playbooks/` — принадлежат основной сессии, **НЕ ТРОГАТЬ**.

### Роли команды

- **Менеджер** — координация, планирование. Инструкции: `agents/manager.md`
- **Инженер** — единственный кто пишет код. Инструкции: `agents/engineer.md`
- **Аудитор** — read-only ревью. Инструкции: `agents/auditor.md`

### Аварийный выход

Закрыть терминал → `git checkout main` → всё как было.
Ветку удалить: `git branch -D agent-team/...`
