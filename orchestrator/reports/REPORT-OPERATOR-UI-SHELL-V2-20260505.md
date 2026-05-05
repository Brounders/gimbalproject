# REPORT-OPERATOR-UI-SHELL-V2-20260505

## Статус

Accepted.

## Цель

Исправить неудачный 1:1-redesign pass и перейти от декоративной имитации HUD к
управляемому PySide6 operator shell:

- все элементы, выглядящие как действия, должны быть реальными кнопками;
- видео должно оставаться главным рабочим пространством;
- source/record controls должны быть доступны, но не занимать экран постоянно;
- диагностика должна уйти в нижний drawer;
- tracking/backend/runtime logic не меняется.

## Изменения

- `app/ui/components.py`
  - добавлены reusable widgets:
    - `IconButton`;
    - `StatusBadge`;
    - `MetricTile`;
    - `BottomDrawer`.

- `app/ui/layout_builders.py`
  - topbar облегчен: убраны target action buttons из верхней строки;
  - левый rail стал компактным 72px shell;
  - фейковые `QLabel`-кнопки `REC/LOCK/NT/ZOOM` заменены на реальные
    `QPushButton`;
  - `ZOOM` удален из operator shell, потому что реального zoom в main video
    runtime сейчас нет;
  - source/record/evaluation controls перенесены в раскрываемый left drawer;
  - right panel оставлен только под target/runtime карточки;
  - diagnostics перенесена в `BottomDrawer`, collapsed by default.

- `app/main_gui.py`
  - добавлены toggle helpers:
    - `_toggle_left_drawer()`;
    - `_toggle_bottom_drawer()`;
    - `_toggle_record_enabled()`;
    - `_sync_record_shortcuts()`;
  - rail source button раскрывает source drawer;
  - rail REC button управляет существующим `record_check`;
  - bottom drawer button раскрывает diagnostics;
  - все существующие slots для start/stop/eval/DTS/expert/manual target сохранены.

- `app/job_state_machine.py`
  - добавлена поддержка enable/disable для новых rail-кнопок без изменения
    worker lifecycle.

- `app/ui/theme.py`
  - добавлены QSS styles для shell components:
    - `RailIconBtn`;
    - `RailIconBtnRec`;
    - `RailHint`;
    - `MetricTile`;
    - `BottomDrawer`;
    - `DrawerToggleBtn`;
    - `DrawerScroll`.

- `tests/test_operator_ui_shell.py`
  - smoke-тесты на real buttons, left/bottom drawer и REC toggle.

## Сохраненный функционал

- source selection: camera/video/stream;
- output recording controls;
- evaluation;
- start/stop;
- operator modes: auto/day/night/ir через прежние handlers;
- Expert dialog;
- DTS Training Desk;
- fullscreen;
- next target;
- operator confirm/release;
- click/drag manual target selection через `VideoStage`;
- target/runtime telemetry updates через существующий `stats_renderer`;
- diagnostics/events/evaluation summaries.

## Артефакты

- Collapsed preview:
  `runs/ui_previews/operator_ui_shell_v2_preview.png`
- Expanded preview:
  `runs/ui_previews/operator_ui_shell_v2_expanded_preview.png`

## Решение

PASS for UI shell foundation.

Это не финальный художественный polish. Это исправление архитектурной ошибки
прошлого pass: теперь shell имеет реальные компоненты, рабочие кнопки и более
здоровое разделение operator surface / diagnostics.

## Риски

- Визуальная доводка всё ещё нужна: spacing, typography, hover/active states и
  responsive behavior можно улучшать отдельными малыми pass.
- `Expert` остаётся отдельным dialog; перенос его вкладок внутрь drawer лучше
  делать отдельной задачей.
- В main video viewport реального zoom нет; поэтому zoom не рисуется в operator
  shell, чтобы не создавать ложную кнопку.
- QSS не повторяет web `backdrop-filter`; дизайн остается native PySide6.
