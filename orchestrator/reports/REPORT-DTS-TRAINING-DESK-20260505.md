# REPORT-DTS-TRAINING-DESK-20260505

## Статус

Accepted / implemented by Codex Mac.

## Цель

Сделать первый Data Training Station / Training Desk слой для контроля
operator-разметки перед экспортом в YOLO labels и обучением.

## Реализовано

- Кнопка `DTS` в верхней панели интерфейса.
- Окно `DTS — Training Desk`:
  - фильтры `Все / Новые / Принятые / Отклонённые / Готовые`;
  - счётчики `new / accepted / rejected / staged`;
  - таблица operator annotation events;
  - preview кадра с bbox, если исходный `source` доступен;
  - карточка выбранной разметки;
  - действия `Принять`, `Отклонить`, `В training pack`;
  - `Предыдущий`, `Следующий`, `Zoom -/+`, `BBox on/off`;
  - отчёт качества и поиск дублей.
- Data layer:
  - `app/training_desk_data.py`;
  - загрузка `runs/operator_annotations/*.jsonl`;
  - стабильные `record_id`;
  - sidecar review state `runs/operator_annotations/dts_review_state.json`.

## Что сознательно не сделано

- Не запускается обучение.
- Не редактируется bbox мышью внутри DTS в этой итерации.
- Кнопки `Экспорт YOLO` и `Собрать training pack` пока объясняют следующий
  шаг, но не запускают pipeline автоматически. Это сделано намеренно, чтобы
  оператор сначала проверял качество разметки.

## Validation

- `pytest tests/test_training_desk_data.py -q`
- PySide offscreen import/instantiation sanity
- compileall/app sanity pending in final session validation.

## Следующий шаг

Связать DTS с export/staging scripts:

- экспортировать только `accepted/staged`;
- открыть папку staging pack;
- добавить ручную кнопку запуска training только после проверки pack.
