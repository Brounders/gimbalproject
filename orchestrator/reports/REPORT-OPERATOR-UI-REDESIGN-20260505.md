# REPORT-OPERATOR-UI-REDESIGN-20260505

## Статус

Accepted / implemented by Codex Mac.

## Цель

Перенести текущий PySide6 operator UI ближе к предоставленному HTML-референсу
`Gimbal Operator UI.html`, не меняя tracking/runtime функциональность.

## Изменения

- `app/ui/theme.py`
  - steel-blue видео-first палитра;
  - glass/HUD панели;
  - компактный topbar;
  - облегчённый dock;
  - более компактная right telemetry typography;
  - стили таблиц/DTS в той же системе.
- `app/ui/layout_builders.py`
  - topbar labels приведены к более техничному виду;
  - left/right rails стали уже, чтобы видео занимало больше места;
  - dock стал плотнее.
- `app/main_gui.py`
  - отступы главного shell уменьшены/перебалансированы под full-screen HUD feel.

## Scope

Только графика и layout constants. Не трогались:

- `src/uav_tracker/*`;
- worker lifecycle;
- tracking pipeline;
- operator-assisted tracking logic;
- DTS data/export logic.

## Preview

- `runs/ui_previews/operator_ui_redesign_preview.png`

## Validation

- targeted UI/data tests passed;
- PySide offscreen preview generated;
- full validation pending in session close.

## Риски

HTML-референс использует web-only эффекты (`backdrop-filter`, CSS animation,
radial backgrounds). В PySide6/QSS они приближены через palette, gradients,
glass colors, spacing, typography and geometry. Полная 1:1 композиция потребует
отдельного structural redesign с floating rail/HUD overlays.
