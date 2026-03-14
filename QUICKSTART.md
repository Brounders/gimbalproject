# Быстрый старт — Agent Teams для GimbalProject

## Схема защиты

```
┌────────────────────────────────────────────────────────┐
│                    main (защищён)                       │
│  ● pre-commit hook блокирует коммиты agent team        │
│  ● агенты НЕ имеют права мержить                       │
│  ● snapshot-тег создаётся перед каждой сессией          │
├────────────────────────────────────────────────────────┤
│              team/задача (рабочая ветка)                │
│  ● вся работа агентов здесь                            │
│  ● Bround ревьюит и мержит вручную                     │
│  ● ИЛИ удаляет ветку = полный откат                    │
└────────────────────────────────────────────────────────┘
```

## Установка (один раз)

```bash
cd ~/Documents/Projects/GimbalProject

# Скопируй скачанные файлы в корень проекта, затем:
bash setup-agent-team.sh
```

## Ежедневный цикл

### Запуск

```bash
# Терминал 2 (отдельный от текущей сессии!)
cd ~/Documents/Projects/GimbalProject
./scripts/team-start.sh refactor-tracking    # создаст ветку team/refactor-tracking
claude                                        # запустить Claude Code
```

Промпт:

```
Создай agent team для задачи: refactor-tracking.

Команда:
1. Менеджер (ты, лид) — прочитай agents/manager.md. Coordination-only (Shift+Tab).
2. Инженер — прочитай agents/engineer.md. Реализация.
3. Аудитор — прочитай agents/auditor.md. Read-only ревью.

Все: прочитай CLAUDE.md. Убедись что мы на ветке team/refactor-tracking.
Задача: [ОПИСАНИЕ]
```

### Остановка (сохранить результат)

```bash
./scripts/team-stop.sh refactor-tracking
# Ветка сохранена. Можно ревьюить:
git diff main..team/refactor-tracking
# Принять:
git merge team/refactor-tracking
# Или отклонить:
git branch -D team/refactor-tracking
```

### Аварийный откат (всё отменить)

```bash
./scripts/team-stop.sh refactor-tracking --discard
# Ветка удалена, main не тронут, stash восстановлен
```

## Совместимость с текущей сессией

| Действие | Текущая сессия | Agent Team |
|---|---|---|
| Ветка | main (или текущая) | team/* |
| Код | можно редактировать | только на своей ветке |
| Конфликты | нет — разные ветки | нет — разные ветки |
| Отключение | не нужно | закрыть терминал |

Текущая сессия и agent team работают параллельно на разных ветках.
Единственное правило: **не редактируй одни и те же файлы** одновременно.

## Отключение Agent Teams навсегда

```bash
# Удалить флаг
rm .claude/settings.json
# Удалить инфраструктуру (код проекта не затронут)
rm -rf agents/ scripts/team-*.sh scripts/hooks/
# Удалить hook
rm .git/hooks/pre-commit
```

Всё. Проект работает как раньше. Ни один файл src/ не затронут.
