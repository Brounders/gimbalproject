# ARC-002 — Декомпозиция TargetManager: FocusModeController

**Дата:** 2026-04-30  
**Статус:** ✅ DONE  
**Ветка:** claude/busy-hamilton-9c2e2a

---

## Что сделано

Извлечён `FocusModeController` из `TargetManager`.

**Новый файл:** `src/uav_tracker/tracking/focus_mode_controller.py` (51 строка)

Перенесены:
- State: `_focus_mode` → `_active`, `_focus_enter_streak` → `_enter_streak`, `_focus_exit_streak` → `_exit_streak`
- Методы: `is_focus_mode()` → `is_active()`, `update_focus_mode()` → `update(confirmed)`, `should_run_night_detector()` → `should_run_night_detector(frames_since_primary)`

`TargetManager` делегирует через `self._focus_ctrl`:
- `is_focus_mode()` → `self._focus_ctrl.is_active()`
- `update_focus_mode()` → `self._focus_ctrl.update(self.has_confirmed_drone_lock())`
- `should_run_night_detector()` → `self._focus_ctrl.should_run_night_detector(self._frames_since_primary)`

**Публичный API `TargetManager` не изменился** — `pipeline.py` и `overlay.py` не затронуты.

## Числа

| Файл | До | После |
|------|----|-------|
| target_manager.py | 434 | 401 |
| focus_mode_controller.py | — | 51 |

## Что проверено

- `python3 -m compileall -q src` — OK
- `python3 -m unittest discover -s tests -q` — **338/338 OK**
- 4 теста трогали `mgr._focus_mode = True` напрямую — обновлены до `mgr._focus_ctrl._active = True`

## Риски

- Тесты по-прежнему трогают `._focus_ctrl._active` — внутренний state. Если FocusModeController получит property-защиту в будущем, тесты нужно пересмотреть.

## Что осталось

- ARC-003 (contingent): `_try_reacquire_active_from_primary` / `_merge_active_lock` / `_predict_center` (~60 строк) — кандидаты на `ReacquirePolicy`, но требуют передачи `targets` dict → нужен отдельный анализ seam
- TD-003: magic numbers → Config
- TEST-001: coverage → 35%
