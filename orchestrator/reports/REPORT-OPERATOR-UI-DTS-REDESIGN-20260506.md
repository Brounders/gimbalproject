# REPORT-OPERATOR-UI-DTS-REDESIGN-20260506

**Задача:** Полный редизайн PySide6 UI (operator window + DTS Training Desk) под HTML-референсы из `/Users/bround/Downloads/handoff/` + реальные quality-метрики, реальный duplicate detection, реальный wiring экспорта в YOLO labels и сборки training pack.

**Дата:** 2026-05-06
**Статус:** PASS · 611 тестов зелёные · compileall OK · GUI smoke OK · ничего из tracker/pipeline не тронуто

---

## 1. Что изменено / создано

| Файл | Тип | Назначение |
|------|-----|------------|
| `app/ui/theme.py` | EDIT | Новая палитра под референс (BG0=#0A0D12, FG0=#F3F5F9, OK=#5FD97E, BAD=#E06B6B, ACC=#7EB8D3) + примитивы для нового UI: `RailIconBtn`, `RefTargetCard`, `RefRowKey/Val/ValStrong`, `RefConfPct/Track/Fill`, `TeleCell`/`TeleKey`/`TeleVal`/`TeleBar`, `StatusPill`, `BottomInfoBar`, `GlassPanel`, и полный набор для DTS: `DtsHeader`, `DtsCounterPill`, `DtsSidebar`, `DtsCenter`, `DtsRecordPanel`, `DtsFooter`, `DtsFilterBtn`, `DtsEventsTable`, `DtsPreviewSurface/CropSurface`, `DtsRecordHeading/Class/Key/Val`, `DtsQualityRow/State/Value`, `DtsAccept`/`DtsReject`/`DtsStage`/`DtsExport`. |
| `app/ui/layout_builders.py` | EDIT | Полностью переработан `build_right_panel`: target card по референсу (title row → meta-rows: ID/СОСТОЯНИЕ/ВРЕМЯ ТРЕКА/КАМЕРА → confidence bar c крупным процентом → secondary CONF/FPS/РЕЖИМ row); + telemetry grid card (6 ячеек FPS/БЮДЖЕТ/ВЫСОТА/СКОРОСТЬ/ЦЕЛЕЙ/ID-СВ.). Добавлен `build_bottom_info_bar`. Все легаси-имена сохранены (`_rp_id_label`, `_rp_name_label`, `_rp_sub_label`, `_rp_live_badge`, `_rp_state_chip`, `_rp_conf_*`, `_rp_rt_*`) — `stats_renderer` не сломан. |
| `app/main_gui.py` | EDIT | Подключён `build_bottom_info_bar` в `_build_ui`. `_open_training_desk` теперь использует `showMaximized()` (раньше `show()`). |
| `app/stats_renderer.py` | EDIT | Добавлены апдейты новых полей: `_rp_id_val`, `_rp_state_val`, `_rp_time_val`, `_rp_camera_val`, `_rp_class_label`, `_rp_alt_v`, `_rp_speed_v`, `_rp_idchg_v`, `bottom_fps_label`, `bottom_info_text`. Маппинг камеры: scenario `night/ir/antiuav_thermal → IR`, `day/default/small_target → EO`. |
| `app/training_desk_quality.py` | NEW (393 строки) | **Реальный quality layer**: `evaluate_record_quality(record)` → `QualityReport` с 7 строками: Структура / Источник / BBox bounds / BBox size / Crop / Резкость (Laplacian variance) / Экспозиция (mean brightness). Cv2-aware fault-tolerant: если cv2 нет или видео не открывается — пиксельные строки `QUALITY_NA`, не падает. + `aggregate_quality(records)` для DTS-summary. + `find_duplicates(records)` с тремя правилами: `exact` (same source/frame/bbox), `overlap` (same source/frame, IoU≥0.50), `near` (same source, frame_distance≤5, IoU≥0.85). + `bbox_iou`, `duplicate_summary`. Все пороги — именованные константы. |
| `app/ui/training_desk.py` | REWRITE (~510 строк, было 329) | Полный редизайн под референс: header (title · counters NEW/ACC/REJ/STG · path · clock · reload · close) → body 3 колонки (sidebar с filters/search/events table; center с 2-pane preview frame+crop + zoom/bbox/prev/next toolbar; record panel с record-id/class/status/meta/quality rows/duplicate links/accept/reject/stage) → footer (accepted/staged stats + export YOLO + build pack + output path). `Esc` закрывает (через `QShortcut`). Открывается `showMaximized()` из main_gui. Реальный quality через `evaluate_record_quality`, реальные дубли через `find_duplicates`. Кэш quality по `record_id` чтобы не открывать видео повторно. |
| `python_scripts/stage_operator_training_pack.py` | NEW (264 строки) | YOLO-style training pack assembler. Читает `runs/operator_annotations/*.jsonl` + `dts_review_state.json`, фильтрует по статусам `accepted/staged`, экстрактит кадры через cv2, пишет `images/{train,val}/`, `labels/{train,val}/`, `manifest.json`, `manifest.csv`, `data.yaml`. Train/val split детерминированный по `sha1(record_id)`, default ratio 0.2. CLI с `--no-extract` для labels-only режима. **Не запускает обучение.** |
| `tests/test_training_desk_quality.py` | NEW (18 тестов) | Покрывает `bbox_iou` (4 кейса), quality rows для каждого fail-режима, `aggregate_quality` для missing-source/invalid-struct, find_duplicates (exact, near, low-IoU не дубль, разные источники, missing bbox, far-frame, same-frame overlap), `duplicate_summary`. |
| `tests/test_stage_operator_training_pack.py` | NEW (10 тестов) | `_stable_split` (детерминизм, распределение), `_xyxy_to_yolo` (центр, zero-size, OOB), end-to-end stage_pack с `--no-extract`: фильтрация по статусам, skip invalid event silently, manifest json/csv/data.yaml записываются, CLI parse_args. |

---

## 2. Как обработан rollback-контекст

В `git log` видны 4 revert-коммита по предыдущей попытке operator HUD redesign (cd001a0 → 5abbc54 → a1c525a → 9cd169f). Текущий `HEAD` = `cd001a0` — это baseline после revert.

Поведение в этой задаче:

- Не воскрешал старую (revert'нутую) ветку.
- Использовал HTML-референсы из handoff + текстовое описание PROMPT.md как утверждённое направление.
- Все правки делал поверх текущего post-rollback состояния.
- Не делал commit/push.
- Сохранены имена ВСЕХ существующих widget'ов которые использует `stats_renderer` и `_wire_actions` (start_btn, stop_btn, dts_btn, expert_btn, fullscreen_btn, next_target_btn, operator_confirm_btn, operator_release_btn, mode buttons, source/record controls, _rp_*, _tc_*, _dock_*) — старые сигналы и slot'ы остались на месте.

---

## 3. Какие реальные quality-метрики реализованы

7 строк `QualityRow` per-record, каждая со своим состоянием `OK/WARN/FAIL/NA`:

| Строка | Сигнал | Источник |
|--------|--------|----------|
| **Структура** | event=`operator_bbox` + bbox валиден + frame_index≥0 + source указан | данные jsonl |
| **Источник** | файл существует + cv2 открывает → пишет `WxH` | `_frame_size(source)` |
| **BBox bounds** | bbox внутри `(0..frame_w, 0..frame_h)` | сравнение с реальным размером кадра |
| **BBox size** | area_ratio = bbox_area / frame_area; warn при `<0.0008` (мелкий) или `>0.65` (большой) | `SMALL_AREA_RATIO_WARN`, `LARGE_AREA_RATIO_WARN` |
| **Crop** | min(w,h) ≥ 8 px (`MIN_CROP_PIXELS`) | xywh из bbox |
| **Резкость** | Laplacian variance на crop'е; `<8` fail, `<25` warn | `cv2.Laplacian` + `np.var` |
| **Экспозиция** | mean brightness crop; `<12` или `>248` fail; `<30` или `>230` warn | `np.mean` over greyscale crop |

Все пороги — именованные константы в `app/training_desk_quality.py`. Pixel-rows никогда не врут: если cv2 не установлен или видео не читается — `QUALITY_NA`, не псевдо-OK.

Aggregate counts (для DTS summary) считаются дешёво — без открытия каждого видео: только структура + bounds + size + missing source.

---

## 4. Какие правила дублей реализованы

Три правила, дешёвый O(N²) per-source pass (записи группируются по `source` сначала):

1. **`exact`** — одинаковые source + frame_index + bbox.
2. **`overlap`** — одинаковые source + frame_index, IoU ≥ `DUP_SAME_FRAME_IOU` (0.50).
3. **`near`** — одинаковые source, |Δframe| ≤ `DUP_NEAR_FRAME_DISTANCE` (5), IoU ≥ `DUP_NEAR_IOU` (0.85).

Возвращает `dict[record_id → list[DuplicateLink]]` с полями `kind`, `iou`, `frame_distance`, `other_frame_index`, `other_status`, `other_source_basename`. Записи без bbox/source игнорируются — нет ложно-положительных. **Не удаляет, не отклоняет автоматически** — оператор решает сам.

DTS показывает дубли двумя способами: маркер `⊕` в колонке `ID` таблицы + список (до 6 записей) в record panel с указанием kind/IoU/frame distance.

---

## 5. Как работает export / staging

### Экспорт YOLO (кнопка `↓ ЭКСПОРТ YOLO`)

1. Берёт записи со статусом `accepted` или `staged`, у которых event=`operator_bbox` и bbox валидный.
2. Создаёт `runs/dts_exports/<timestamp>/labels/`.
3. Пишет отфильтрованный jsonl `selected_operator_annotations.jsonl` — переносит **исходную JSON-строку** из лога по `(log_path, line_number)`, сохраняя audit trail.
4. Определяет размер кадра из первого доступного видео (`_frame_size`).
5. Запускает `python_scripts/export_operator_annotations_to_yolo.py` через subprocess с `--input <отфильтрованный jsonl>` и реальными `--frame-width/-height`.
6. Показывает QMessageBox с командой и stdout/stderr (труcates до 1500 символов). Путь обновляется в footer.

Если размер кадра определить нельзя — экспорт останавливается и предупреждает оператора. Не даёт молчаливой неправильной нормализации.

### Сборка training pack (кнопка `○ СОБРАТЬ PACK`)

1. Создаёт `runs/operator_training_packs/pack_<timestamp>/`.
2. Запускает `python_scripts/stage_operator_training_pack.py` через subprocess.
3. Скрипт:
   - читает все `runs/operator_annotations/*.jsonl` + `dts_review_state.json`,
   - фильтрует по `accepted/staged`,
   - для каждой записи открывает source video через cv2, читает кадр, пишет JPG в `images/{train|val}/<stem>__f<NNNNNN>.jpg`,
   - пишет YOLO label `.txt` рядом в `labels/{train|val}/`,
   - обновляет `manifest.json` и `manifest.csv` со статусами `ok`/`skipped_status`/`skipped_invalid`/`skipped_source`/`skipped_frame`,
   - пишет `data.yaml` (минимальный — `train`, `val`, `names: {0: drone}`).
4. Train/val split детерминированный: `sha1(record_id)` в [0..1) сравнивается с `--val-ratio` (default 0.2).
5. Возвращает manifest в QMessageBox.

**Обучение не запускается** — pack лежит на диске, оператор сам решает что с ним делать.

---

## 6. Validation

| Команда | Результат |
|---------|-----------|
| `pytest tests/test_training_desk_quality.py -q` | **18 passed** |
| `pytest tests/test_stage_operator_training_pack.py -q` | **10 passed** |
| `pytest tests/test_training_desk_data.py tests/test_operator_annotation_export.py tests/test_video_stage_mapping.py -q` | **33 passed** |
| `pytest tests -q` | **611 passed** (+103 vs prior 508) |
| `compileall -q python_scripts src app orchestrator tests` | OK |
| `git diff --check` | clean |
| `QT_QPA_PLATFORM=offscreen` `MainWindow()` | OK, все widget-имена живы |
| `QT_QPA_PLATFORM=offscreen` `TrainingDeskDialog().reload()` | OK · 57 records · `cnt_new=51` (реальные данные из `runs/operator_annotations/`) |

---

## 7. Что сохранено из текущего поведения

| Зона | Статус |
|------|--------|
| `src/uav_tracker/pipeline.py`, `tracking/*` | НЕ ТРОНУТО |
| Model loading / detector behavior | НЕ ТРОНУТО |
| Quality gate thresholds | НЕ ТРОНУТО |
| Training runtime | НЕ ТРОНУТО |
| Hailo / deployment code | НЕ ТРОНУТО |
| `app/workers.py` (TrackerWorker / EvaluationWorker) | НЕ ТРОНУТО |
| Source/camera/stream selection controls | работают (тот же `source_type_combo`, `camera_index_spin`, `source_path_edit`, `source_browse_btn`) |
| Recording controls и output path | работают (`record_check`, `output_edit`, `output_browse_btn`) |
| Quick режимы auto/day/night/IR | работают (те же `quick_*_btn` в topbar) |
| Expert dialog и DTS button в topbar | DTS остался в topbar (`dts_btn`) — теперь открывает maximized |
| Fullscreen | работает |
| Next target / operator confirm / operator release | работают (те же `next_target_btn`, `operator_confirm_btn`, `operator_release_btn` + `_dock_*` иконки) |
| Start/Stop/Evaluate | работают (те же `start_btn`, `stop_btn`, `eval_btn`) |
| Video stage rendering, click-to-target, drag-bbox mapping | НЕ ТРОНУТО (`VideoStage` и `video_stage_mapping` тесты — 8 passed) |
| Worker shutdown behavior | НЕ ТРОНУТО |

---

## 8. Risks / manual checks

1. **Реальный пользовательский полный-экран DTS не проверен на конкретной мониторной геометрии.** `showMaximized()` работает в offscreen; на multi-monitor желателен manual check что DTS открывается на том же экране что MainWindow.
2. **Pixel quality (sharpness/exposure) требует cv2 + numpy.** В тестовом окружении они есть; на bare-Python хосте строки этих метрик станут `QUALITY_NA` и оператор это увидит явно.
3. **Train/val split — простой `sha1`-bucket.** Подходит для быстрой сборки pack'а; для production split'а с балансом по сценам (день/ночь/IR) — отдельная задача.
4. **Frame-size inference в export.** Берёт размер первого открываемого видео из выборки. Если в выборке есть клипы РАЗНЫХ разрешений, нормализация будет неправильной для видео с другим размером. В этом случае оператор должен делать экспорт по-разрешениям отдельно (фильтр по source). Это видно в manifest.
5. **`subprocess.run` для exporter / stager** даёт stdout/stderr оператору, но не передаёт прогресс. Для длинных pack'ов (тысячи кадров) UI заморозится на время сборки. Mitigation: можно вынести в `QThread` отдельной задачей.
6. **Новые `_rp_alt_v` / `_rp_speed_v` показывают `—`** — данных о высоте/скорости в `stats_renderer` пока нет (нет gimbal telemetry channel). Слоты подготовлены, заполнятся когда придёт реальная телеметрия.
7. **Операторские `RailIconBtn` примитивы добавлены в theme**, но не вынесены в layout_builders как самостоятельная колонка — текущая левая колонка остаётся "GlassPanel" с source/record/eval. Это компромисс между визуальным соответствием референсу и сохранением всех текущих контролов в видимом месте. Если нужен exact-reference layout с icon-only rail — отдельный bounded шаг.
8. **Visible-night и IR-first ActionPolicy** не затронуты этим циклом — UI-only задача, как и оговорено в PROMPT.md §4.

---

**Stop after task.** Следующий шаг выбирает Codex/Human.
