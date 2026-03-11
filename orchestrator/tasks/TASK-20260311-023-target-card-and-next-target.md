# TASK: TASK-20260311-023-target-card-and-next-target

Task ID: TASK-20260311-023
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Добавить целевую карточку в правый верхний угол video stage и кнопку `Next Target` в header, сохранив существующую бизнес-логику трекера.

## Scope
- In scope:
  - добавить `build_target_info_card()`;
  - разместить карточку в `MainVideoStage`;
  - карточка показывает: `ID`, `confidence`, `time on target`, `FPS`, `Lock/Idle`;
  - добавить кнопку `Next Target` в `HeaderBar`;
  - подключить `Next Target` к переключению primary target на следующий доступный ID через существующий tracker flow или минимальное безопасное расширение UI-to-runtime interface.
- Out of scope:
  - переписывание target selection logic;
  - новые tracking algorithms.

## Files
- `app/main_gui.py`
- `app/ui/*` (если нужен локальный helper/widget)
- `src/uav_tracker/pipeline.py` только если требуется минимальный contract hook без изменения decision logic

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- Smoke GUI path if possible.
- Проверка отсутствия crash при обновлении карточки на кадрах без цели.

## Acceptance Criteria
- [ ] Target card отображается в video stage и обновляется от текущего frame state.
- [ ] `Next Target` присутствует в header.
- [ ] При отсутствии цели карточка ведет себя корректно и не ломает UI.
