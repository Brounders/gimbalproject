# REPORT-OPERATOR-OVERRIDE-BACKEND-20260503

## Статус

Accepted / implemented by Codex Mac.

## Цель

Сделать первую рабочую backend-итерацию ручного выбора цели оператором без
GUI wiring: операторская команда должна попадать в pipeline как явный command,
без побочных изменений в текущем UI и без включения по умолчанию.

## Изменения

- `OperatorTargetOverride`:
  - поддерживает click → clipped bbox;
  - поддерживает bbox → clipped bbox;
  - invalid/zero-area bbox отклоняется.
- `DetectionSource.OPERATOR`:
  - добавлен как `operator`;
  - считается primary source;
  - получает `SOURCE_RELIABILITY=1.00`.
- `TargetManager.apply_operator_override()`:
  - предпочитает существующий target внутри/пересекающий выбранную область;
  - иначе создаёт auxiliary target;
  - force-select active target;
  - помечает цель как operator-confirmed: `source=operator`, `conf=1.0`,
    `drone_score=1.0`, `hit_streak>=LOCK_CONFIRM_FRAMES`.
- `TrackerPipeline.request_operator_target()`:
  - ставит команду в очередь до следующего кадра;
  - применение guarded через `Config.OPERATOR_OVERRIDE_ENABLED`;
  - при успешном применении сбрасывает `TemplateLockTracker`, чтобы следующий
    `_sync_lock_tracker()` привязал шаблон к выбранной оператором области.
- `FrameOutput`:
  - `operator_override_status`;
  - `operator_override_count`;
  - `operator_override_bbox`.

## Scope

Сделано только backend-ядро. GUI-клик, hotkeys, визуальный режим выбора и
координатный mapping из виджета в frame coordinates не входят в эту итерацию.

## Validation

- `pytest tests/test_operator_override.py -q`
- related tracking/action/pipeline helper tests
- full test suite pending in final validation of the session.

## Решение

Backend foundation готов. Следующий цикл должен подключить PySide6 UI input к
`TrackerPipeline.request_operator_target()` и отдельно проверить coordinate
mapping на разных масштабах отображения видео.
