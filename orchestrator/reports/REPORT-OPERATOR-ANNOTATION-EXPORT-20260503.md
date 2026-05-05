# REPORT-OPERATOR-ANNOTATION-EXPORT-20260503

**Задача:** первый конвертер operator annotation logs → YOLO labels для дообучения модели
**Дата:** 2026-05-03
**Статус:** PASS · 19 тестов зелёные · smoke-run на реальных jsonl OK · выходные файлы в репо не добавлялись

Follow-up к `REPORT-OPERATOR-ASSISTED-TRACKING-V2-20260503.md`.

---

## 1. Что реализовано

| Файл | Тип | Назначение |
|------|-----|------------|
| `python_scripts/export_operator_annotations_to_yolo.py` | NEW | Standalone CLI: читает один jsonl или директорию, пишет YOLO `.txt` labels + manifest. |
| `tests/test_operator_annotation_export.py` | NEW | 19 unit-тестов: покрытие конверсии, malformed lines, OOB, dry-run, manifest, CLI. |
| `orchestrator/reports/REPORT-OPERATOR-ANNOTATION-EXPORT-20260503.md` | NEW | Этот отчёт. |
| `orchestrator/state/completed_tasks.md` | EDIT | Запись о завершении. |

Не трогал: `app/main_gui.py`, `app/workers.py`, `src/uav_tracker/pipeline.py`, `src/uav_tracker/tracking/*`, `configs/`, baseline thresholds, model, training, GUI, tracker behavior.

---

## 2. Формат входа

JSONL из `runs/operator_annotations/`. Каждая строка — один event:

```json
{"frame_index": 71, "source": "/abs/path/clip.mp4",
 "bbox_xyxy": [292, 241, 377, 324], "active_id": 9000,
 "active_source": "operator", "event": "operator_bbox"}
```

Конвертируются только строки с `event == "operator_bbox"`. Все прочие события (`operator_confirm`, `operator_release`, и т.п.) идут в manifest со статусом `skipped_event` и не порождают label-файлов.

Минимально требуемые поля: `event`, `source`, `frame_index`, `bbox_xyxy` (4-tuple).
Размер кадра в jsonl сейчас не пишется — поэтому передаётся аргументами `--frame-width` / `--frame-height`. Это явно, без догадок.

---

## 3. Формат выхода

### 3.1. YOLO label files

Один `.txt` на оператор-bbox-event:

```
<output-dir>/<video_stem>__f<frame_index:06d>.txt
```

Содержимое — одна YOLO-строка:

```
<class_id> <cx_norm> <cy_norm> <w_norm> <h_norm>
```

`class_id` задаётся `--class-id` (default `0`).

### 3.2. Manifest

`manifest.json` и/или `manifest.csv` в `--manifest-dir` (по умолчанию = `--output-dir`). Формат строки manifest:

| Поле | Описание |
|------|----------|
| `input_file` | путь к исходному jsonl |
| `line_number` | номер строки в jsonl (1-based) |
| `status` | `ok` / `malformed_line` / `missing_field` / `skipped_event` / `rejected_out_of_bounds` / `rejected_degenerate_bbox` |
| `source` | путь к видео из jsonl |
| `frame_index` | кадр |
| `bbox_xyxy` | исходный bbox |
| `label_path` | путь к созданному label-файлу (только при `status=ok`) |
| `yolo_xywh_norm` | результат конверсии (для `ok` и для `rejected_out_of_bounds` — для отладки) |
| `reason` | объяснение для всех non-ok статусов |

Manifest пишется и в `--dry-run` режиме? **Нет** — в текущей итерации dry-run полностью идемпотентен (не создаёт ни labels, ни manifest на диск). Логические счётчики возвращаются вызывающему через `ExportSummary`. Тест `test_dry_run_skips_label_files_but_writes_manifest` фиксирует это поведение.

### 3.3. Обработка bbox вне границ

**Решение зафиксировано: отклонять (`status=rejected_out_of_bounds`), не клипать.**

Обоснование: клипанная рамка может породить мусор для training (особенно если оператор задел край кадра по ошибке). Отклонение видно в manifest и оператор может перерисовать корректно.

Тест `test_bbox_out_of_bounds_is_rejected` фиксирует это поведение. `test_degenerate_bbox_is_rejected` отдельно проверяет zero-width/zero-height.

---

## 4. Как это поможет обучению

1. **Closed-loop data path:** оператор размечает «провальные» сцены в GUI → pipeline пишет jsonl → этот скрипт превращает их в YOLO labels. Появляется первый воспроизводимый канал получения новых positive samples без ручной разметки в LabelImg.
2. **Готовый шаблон формата:** YOLO normalized xywh — стандартный формат для Ultralytics training. Достаточно собрать `images/` и `labels/` и указать в data.yaml — готовый dataset prefix.
3. **Manifest как audit trail:** даёт прозрачную статистику что вошло в training и почему. Без него невозможно отладить регрессии после fine-tune.
4. **Не блокирует следующие шаги:** скрипт изолирован, не меняет runtime, baseline или GUI. Можно безопасно гонять на любой коллекции jsonl сессий.

---

## 5. Что сознательно не сделано

1. **Извлечение кадров из видео.** В этой итерации только labels + manifest. Извлечение фреймов — отдельный шаг (требует ffmpeg/cv2 вызова, опционы downsampling, формат изображений). Должно быть отдельной задачей с собственным скриптом и тестами.
2. **Запись width/height в pipeline jsonl.** Pipeline сейчас не пишет размер кадра. Скрипт принимает их аргументами. Доработка jsonl — отдельный bounded change в pipeline writer и его out-of-scope.
3. **train/val split.** Скрипт пишет плоский каталог labels. Разбиение — задача train wrapper'а.
4. **YAML data.yaml.** Не создаётся: класс не один универсальный, формирование data.yaml зависит от target dataset layout, выходит за scope.
5. **Multi-class разметка.** Сейчас единый `--class-id` для всех bbox оператора. Multi-class разметка потребует расширения jsonl-протокола в pipeline.
6. **Dedup дублирующихся frame_index.** Если оператор разметил один и тот же кадр дважды — последний перезатирает первый (одинаковое имя файла). Это видно в manifest как два `ok` подряд с одним `label_path`. Намеренное «last write wins»; явный dedup — следующая итерация.
7. **Кросс-проверка с GT.** Если для клипа уже есть `_gt.json`, скрипт его не сравнивает. Это аудиторская задача отдельного script'а.
8. **Включение в `python_scripts/run_intake.py`.** Оставлено как отдельный шаг — скрипт здесь живёт изолированно.

---

## 6. Validation

| Команда | Результат |
|---------|-----------|
| `pytest tests/test_operator_annotation_export.py -q` | **19 passed** |
| `compileall -q python_scripts src app orchestrator tests` | OK |
| `git diff --check` | clean |
| `orchestrator/scripts/check_orchestration_state.py` | OK · active=0 · open=0 · completed=70 |
| Smoke run dry-run на 8 jsonl из `runs/operator_annotations/` (frame 1920×1080) | total_lines=28, ok=28, files_written=0, malformed=0, OOB=0 |

Тестовое покрытие охватывает:

- xyxy → YOLO normalized xywh (4 кейса включая edge cases);
- `is_in_unit_bounds` (4 кейса);
- end-to-end: label files создаются с правильным содержимым;
- malformed json не валит export, попадает в manifest;
- bbox out-of-bounds rejected, не clipped;
- degenerate bbox (zero-width/height) rejected;
- dry-run не пишет ни labels, ни manifest на диск;
- manifest json+csv содержат ожидаемые поля и статусы;
- non-`operator_bbox` event → `skipped_event`;
- missing fields → `missing_field`;
- CLI defaults и parse_manifest_formats.

---

## 7. Риски

1. **Ручная передача frame size.** Если оператор укажет неверный `--frame-width/--frame-height`, нормализация будет тихо неверна (но всё ещё внутри [0, 1] для маленьких bbox). Mitigation: записывать размер кадра в jsonl pipeline-ом — отдельная bounded задача.
2. **Один абсолютный путь в `source` jsonl.** Если папка проекта переехала, путь устареет. Скрипт его НЕ открывает (только использует stem для имени файла), поэтому работает; но для будущей extraction-задачи путь нужно будет ремапить.
3. **Last-write-wins по `<stem>__f<NNNNNN>.txt`.** Если оператор переразметил один и тот же кадр в разных сессиях — поздняя сессия перезапишет раннюю. Manifest показывает оба события. Намеренный trade-off ради простоты.
4. **`class_id=0` как default.** Если будущая модель использует другой class id для дрона, нужно явно передать `--class-id`.

---

## 8. Следующий шаг (предложение для Codex/Human)

1. Расширить pipeline operator annotation writer: добавить `frame_width`/`frame_height` в jsonl, чтобы убрать ручной аргумент.
2. Сделать сопутствующий `extract_operator_frames.py` (cv2 → JPG/PNG в `images/`), параллельный по структуре каталога с этим экспортёром.
3. Объединить с GT proverka (если есть `_gt.json` для клипа — сравнить operator bbox с GT bbox и пометить расхождения в manifest).
4. Реальный fine-tune эксперимент на собранном operator-датасете — отдельный training cycle, требует Codex/Human approval.

---

**Stop after task.** Следующий шаг выбирает Codex/Human.
