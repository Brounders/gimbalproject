# TASK: TASK-20260311-012-stable-cycle-preset-preflight

Task ID: TASK-20260311-012
Owner: Claude Mac
Priority: P2
Status: Open

## Goal
Встроить `validate_profile_presets.py` как pre-flight шаг в `run_stable_cycle.py`,
чтобы невалидный пресет прерывал цикл до запуска бенчмарка, а не вызывал
непредсказуемое поведение в runtime.

## Scope
- In scope:
  - прочитать `run_stable_cycle.py` и найти точку вставки pre-flight шага;
  - добавить вызов валидатора в начало основного цикла / перед benchmark-шагом;
  - если валидатор возвращает exit code != 0 — остановить цикл с чётким сообщением;
  - если пресет не указан явно — пропустить проверку или проверить весь configs/ без блокировки.
- Out of scope:
  - изменение логики benchmark, quality-gate, release decision;
  - изменение `validate_profile_presets.py`, `profile_io.py`, runtime-трекера.

## Constraints
- Минимальный diff в `run_stable_cycle.py`.
- Без новых зависимостей.
- Не ломать happy-path — если `validate_profile_presets.py` недоступен, выводить warning и продолжать.

## Inputs
- `python_scripts/run_stable_cycle.py` (обязательно читать перед правкой!)
- `python_scripts/validate_profile_presets.py`

## Implementation Hint
Прямой import функции `main()` из валидатора предпочтительнее subprocess:
```python
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).parent))
try:
    from validate_profile_presets import main as _validate_presets
    _HAS_VALIDATOR = True
except ImportError:
    _HAS_VALIDATOR = False
```

Место вставки: до первого шага benchmark в `run_stable_cycle.py`.

## Validation
- `python3 -m compileall -q python_scripts src app tests`
- `./tracker_env/bin/python python_scripts/run_stable_cycle.py --help` (без падения)
- При передаче несуществующего пресета: выходит с понятным сообщением до бенчмарка.

## Acceptance Criteria
- [ ] Pre-flight вызов валидатора добавлен в run_stable_cycle.py.
- [ ] Невалидный/несуществующий пресет прерывает цикл до benchmark.
- [ ] Валидный пресет → цикл продолжается без изменений.
- [ ] compileall OK, --help не падает.
