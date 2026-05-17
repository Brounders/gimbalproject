# Статус ui_web

Дата статуса: 2026-05-17

`ui_web/` — это React/Vite проект. Он может собираться как отдельный web UI, но
текущий аудит не подтвердил, что он связан с активным operator runtime.

## Текущее решение

- Статус: `UNKNOWN_NEEDS_TRACE`.
- Runtime authority: отсутствует.
- Operator authority: отсутствует.
- Текущий primary operator UI остается QML desktop flow.

## Основания

- `package.json` содержит Vite scripts: `dev`, `build`, `preview`.
- Аудит нашел build/CI след, но не нашел документированный owner и runtime
  integration path.
- Нет принятого решения, что `ui_web/` заменяет QML или PySide6.

## Правила до owner decision

- Не считать `ui_web/` источником operator truth.
- Не удалять, не переносить и не переписывать его на этапе stabilization intake.
- Его можно инспектировать или собирать для evidence, но product changes требуют
  отдельного решения владельца.

## Какое решение нужно

TASK-20260517-111/113 должны определить, чем является `ui_web/`:

1. экспериментальная web console;
2. замороженная историческая работа;
3. кандидат на архив после proof, что от него ничего активного не зависит;
4. будущий UI только при наличии явного integration plan и тестов.
