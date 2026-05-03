# REPORT-OPERATOR-SEEDED-LOCK-UI-20260503

## Статус

Accepted / implemented by Codex Mac.

## Цель

Подключить ручной выбор цели к PySide6 UI и исправить ключевую проблему:
если YOLO не видит визуально заметный дрон, клик оператора должен не только
выбирать existing detection, а создавать operator-confirmed target и сразу
засевать `TemplateLockTracker`.

## Изменения

- UI click wiring:
  - `VideoStage.operator_target_requested(int, int)` emits frame coordinates;
  - `app/ui/video_mapping.py` maps QLabel coordinates to original frame
    coordinates under `Qt.KeepAspectRatio`;
  - clicks in letterbox margins are ignored.
- Worker contract:
  - `TrackerWorker.request_operator_target(x, y)` stores the latest operator
    click thread-safely;
  - worker converts it to `OperatorTargetOverride.from_click()` and queues it
    into `TrackerPipeline`.
- Main GUI:
  - connects video-stage click signal to worker request;
  - enables `Config.OPERATOR_OVERRIDE_ENABLED=True` for GUI sessions;
  - logs operator selection requests.
- Operator-seeded lock:
  - `TargetManager.apply_operator_override()` now force-enters focus mode;
  - pipeline seeds `TemplateLockTracker.sync_from_bbox(frame, operator_bbox)`
    instead of resetting it;
  - `_sync_lock_tracker()` treats `DetectionSource.OPERATOR` as a source that
    can refresh the template.
- Telemetry/UI:
  - worker forwards `operator_override_status/count/bbox`;
  - stats panel logs applied operator override and displays `operator` source
    as `Оператор`.

## Важный вывод

Ручной клик теперь является не слабой подсказкой детектору, а отдельным
каналом старта удержания. Если detector не видит дрон, pipeline всё равно
создаёт operator target и пытается вести его через template lock.

## Validation

- `pytest tests/test_video_stage_mapping.py tests/test_worker_operator_override.py tests/test_operator_override.py tests/test_target_manager_lifecycle.py tests/test_action_policy_behavior.py -q`
- full validation pending in session close.

## Следующий шаг

Полевой smoke в GUI: открыть клип, где дрон виден визуально, но detector
не даёт lock; кликнуть по дрону; проверить, что target source становится
`operator`, template lock удерживает bbox, а при потере цели UI честно
показывает потерю, а не возвращается к ложному target.
