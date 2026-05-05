# REPORT-OPERATOR-UI-1TO1-REDESIGN-20260505

## Статус

Accepted.

## Цель

Сделать не косметический QSS-pass, а структурный PySide6 HUD-pass под
`/Users/bround/Downloads/UI/Gimbal Operator UI.html`: полноэкранная видеосцена
как базовый слой, плавающая верхняя панель, левый rail, правые HUD-карточки и
нижний dock. Весь уже реализованный операторский функционал должен остаться на
месте.

## Изменения

- `app/main_gui.py`
  - root layout заменён с вертикальной формы на one-cell overlay HUD через
    `QGridLayout`;
  - `VideoStage` стал базовым слоем;
  - `TopBar`, `LeftRailStack`, `RightHudPanel`, `Dock` размещаются поверх видео;
  - старое системное меню скрыто, чтобы не ломать fullscreen/HUD reference;
  - меню-кнопка topbar подключена к существующей справке;
  - старый дублирующий top-right target overlay скрыт: целевая телеметрия теперь
    отображается в правой HUD-карточке.

- `app/ui/layout_builders.py`
  - topbar перестроен ближе к reference: compact brand mark, IR/EO/NV/AUTO
    segment, status, source, REC, Expert, DTS, fullscreen, NT, confirm/release;
  - левый блок стал `LeftRailStack`: узкий вертикальный rail + drawer source/data;
  - правый блок стал `RightHudPanel`: target card + runtime card + diagnostics
    below topbar;
  - dock расширен как нижняя плавающая панель.

- `app/ui/theme.py`
  - добавлены HUD/QSS tokens для `BrandMark`, `TopIconBtn`, `RailDock`,
    `RailDrawer`, `RailGlyph*`, `RailZoom*`, `RightHudPanel`;
  - video stage сделан full-bleed/dark без карточной рамки;
  - панели приведены к steel-blue glass/HUD reference.

## Сохранённый функционал

- source selection: camera/video/stream;
- output recording controls;
- evaluation run;
- start/stop;
- scenario + runtime quick modes;
- Expert dialog;
- DTS Training Desk;
- fullscreen;
- next target;
- operator confirm/release;
- manual click/drag target selection through `VideoStage`;
- existing worker/pipeline/tracking logic.

## Артефакты

- Preview: `runs/ui_previews/operator_ui_1to1_preview.png`

## Решение

PASS for structural UI redesign.

Tracking/runtime/model logic intentionally unchanged.

## Риски

- Это максимально близкий перенос HTML-композиции в PySide6/QSS, но не
  пиксельный web-CSS clone: Qt не повторяет `backdrop-filter`, web animations и
  часть CSS layering 1:1.
- Левая source/data drawer оставлена видимой ради сохранения всего текущего
  функционала. В HTML-reference rail уже, но тогда часть desktop controls нужно
  прятать за отдельным drawer interaction.
- На маленьких экранах ниже текущего minimum size layout не оптимизировался.
