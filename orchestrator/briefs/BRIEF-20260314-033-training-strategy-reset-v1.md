# BRIEF-20260314-033 — Training Strategy Reset v1

## Контекст
Весь curriculum `drone-bird-yolo` (132 эпохи, chunk1-10) отклонён.
Решение записано в `decision_log.json`: `reject_and_reset_training_strategy`.

Корневая причина (из REPORT-20260313-086):
- Все кандидаты (chunk6 ep73-84, chunk10 ep121-132) провалили night gate
  с нарастающей деградацией при росте эпох.
- Тренд: `more epochs = worse night performance`.
- Вывод: датасет `drone-bird-yolo` не содержит ночных видимого-диапазона данных,
  достаточных для сохранения night tracking quality.

## Шаги до следующего обучения (обязательные)

### Шаг 1: Аудит датасета (1 сессия)
- Проверить состав `drone-bird-yolo`:
  - Соотношение day / night / IR фреймов
  - Есть ли night visible-light данные?
  - Дисбаланс классов (drone vs bird)?
- Инструмент: `python_scripts/` или ручной анализ YAML/папок датасета.
- Deliverable: отчёт с цифрами.

### Шаг 2: Формализация baseline.pt (сделано 2026-03-14)
- `models/baseline.pt` установлен — `drone_bird_probe_fast`.
- `install_baseline.py` выполнен.

### Шаг 3: Починить day quality gate (сделано 2026-03-14)
- false_lock_rate теперь пропускается когда gt_frames=0.

### Шаг 4: Дизайн нового тренировочного датасета
Требования к датасету (из evidence):
- Минимум 20% night visible-light фреймов
- Явное покрытие large-target night сцен
- Паритет drone / non-drone
- Стратегия аугментации для night (brightness, contrast jitter)

### Шаг 5: Новый training brief
После аудита датасета — новый BRIEF с:
- Составом датасета
- Early stopping criterion: night gate check каждые N эпох
- Milestone checkpoints для промежуточного качество-gate

## Предупреждение
НЕ запускать обучение до:
1. Аудита датасета (Шаг 1)
2. Согласования с Human нового состава данных
3. Подтверждения что базовый night runtime gate остаётся PASS

## Статус
Ожидает открытия нового Plan с Шагом 1 (аудит датасета).
