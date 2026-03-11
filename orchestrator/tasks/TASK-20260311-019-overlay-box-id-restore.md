# TASK: TASK-20260311-019-overlay-box-id-restore

Task ID: TASK-20260311-019
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Вернуть базовый операторский overlay к виду: аккуратная рамка вокруг активной цели + `ID` цели у верхнего левого угла рамки. Прицел/reticle не должен быть базовым отображением.

## Scope
- In scope:
  - найти, почему operator overlay снова показывает reticle/crosshair вместо рамки;
  - восстановить bbox-centered overlay как default operator behavior;
  - вывести `ID=<active_id>` рядом с рамкой;
  - оставить reticle только как debug/expert-only option, если он еще нужен.
- Out of scope:
  - полный редизайн overlay;
  - изменение lock-policy или target scoring.

## Files
- `src/uav_tracker/overlay.py`
- `src/uav_tracker/pipeline.py`
- `app/main_gui.py` (только если требуется корректная передача display state)

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- Локальный smoke-run на одном test video, если возможен.
- Ручная проверка: default operator mode показывает рамку + ID, без reticle по умолчанию.

## Acceptance Criteria
- [ ] В базовом операторском режиме отображается рамка вокруг цели.
- [ ] `ID` активной цели виден рядом с рамкой.
- [ ] Прицел не появляется самопроизвольно в default operator flow.
