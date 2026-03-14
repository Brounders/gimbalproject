# BRIEF-20260314-032 — A07: Kalman vs EMA Research Decision

## Вопрос
Заменить EMA-предсказание (`vx/vy`) в `target_manager.py` на фильтр Калмана?

## Текущая реализация
`target_manager.py:264-266`:
```python
target.vx = vel_alpha * dx + (1.0 - vel_alpha) * target.vx
target.vy = vel_alpha * dy + (1.0 - vel_alpha) * target.vy
```
Предсказание при reacquire: `cx += vx * horizon * gain` (линейная экстраполяция).

## Анализ пользы Калмана

Фильтр Калмана даёт:
- Оптимальную оценку состояния с явной моделью шума
- Лучшую оценку скорости при шумных измерениях
- Более обоснованный probability-based prediction horizon

## Почему НЕ НУЖЕН сейчас

**Ключевой факт**: все недавние провалы quality gate были на уровне детектора
(`false_lock`, `id_chg/min`), а не на уровне предсказания траектории.
Ночная проблема решена через `NIGHT_CONFIRM=5` — фильтрация на уровне детектора.

Аргументы против:
1. **Ни один problem-pack клип не демонстрирует** drift от плохой velocity estimation.
2. **Калман требует настройки Q и R** (process noise, measurement noise) —
   новые magic numbers без evidence-based calibration.
3. **Риск регрессии на ночных клипах**, которые только что получили PASS.
4. **Сложность без чёткого качественного выигрыша** — не измеримо через текущий gate.

## Решение

**Оставить EMA.** Реализовать Калман только если появится evidence:
- Problem-pack clip, где false_lock или id_chg явно вызваны плохим prediction
- Hailo deployment с известными латентными характеристиками

## Статус A07
ЗАКРЫТ: решение задокументировано, реализация не требуется.
