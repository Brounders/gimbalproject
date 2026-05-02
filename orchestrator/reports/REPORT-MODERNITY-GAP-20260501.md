# REPORT-MODERNITY-GAP-20260501

Status: ACCEPTED
Date: 2026-05-01
Owner: Codex
Type: Architecture audit / decision matrix

## Цель

Оценить современность текущего GimbalProject относительно актуального пути Ultralytics и выбрать безопасные следующие эксперименты без изменения runtime, baseline, thresholds, обучения и новых зависимостей.

## Источники

- `orchestrator/state/active_plan.md` — `AP-MODERNITY-GAP`.
- `../wiki/sources/ultralytics_site_map.md` — локальная карта Ultralytics, актуальная линия `YOLO26`.
- `../wiki/sources/ultralytics_yolo.md` — Python API, tracking, Results API.
- Context7 `/websites/ultralytics` — проверка `model.track()`, `persist=True`, `bytetrack.yaml`, `botsort.yaml`, `Results.boxes.id`, `yolo26n.pt`.
- `src/uav_tracker/runtime/ultralytics_backend.py` — текущая интеграция Ultralytics.
- `src/uav_tracker/pipeline.py` — гибридный runtime-конвейер.
- `src/uav_tracker/tracking/target_manager.py` — active target и lock policy.
- `src/uav_tracker/tracking/lock_tracker.py` — template lock.
- `src/uav_tracker/detectors/night_detector.py` — MOG2/night motion detector.
- `src/uav_tracker/detectors/roi_assist.py` — motion ROI assist.
- `src/uav_tracker/display/overlay.py` — operator/research overlay.
- `orchestrator/reports/REPORT-20260429-tracker-ab.md` — template lock ON/OFF на night gate.
- `orchestrator/reports/REPORT-BYTETRACK-EVAL-20260501.md` — project pipeline vs native Ultralytics tracking.
- `runs/evaluations/ultralytics_tracking/mgap_bytetrack_tracking_eval_night_bytetrack.json` — full `ByteTrack` measurement.
- `runs/evaluations/ultralytics_tracking/mgap_botsort_tracking_eval_night_botsort.json` — full `BoT-SORT` measurement.
- `runs/evaluations/ultralytics_tracking/mgap_botsort_reid_tracking_eval_night_botsort.json` — full `BoT-SORT + ReID` measurement.

## Факты по Ultralytics

- Актуальная модельная линия в локальной и Context7-документации: `YOLO26`; упоминания `YOLOv11` в roadmap/training scripts являются устаревшими для новых экспериментов.
- Штатный tracking работает через `model.track(...)`.
- `BoT-SORT` является default tracker через `botsort.yaml`; `ByteTrack` включается через `tracker="bytetrack.yaml"`.
- Для покадрового видео-цикла нужен `persist=True`, иначе состояние tracker между кадрами не является рабочей основой.
- Track IDs доступны через `Results.boxes.id`.
- `model.track()` internally sets low confidence input for ByteTrack-like association; ручное завышение `conf` может ухудшить native tracking на слабых целях.
- Custom tracker YAML path is supported by `model.track(..., tracker="custom_tracker.yaml")`.
- Installed `ultralytics 8.4.19` ships `botsort.yaml` with `with_reid: False` and `model: auto`; measurement config `configs/trackers/botsort_reid.yaml` enables `with_reid: True`.

## Факты по текущему проекту

- `UltralyticsBackend.track_frame()` уже использует `model.track(..., persist=True, tracker='bytetrack.yaml')` и берет `track_id` из `box.id`.
- `TrackerPipeline` не является ByteTrack-only: после YOLO track IDs идут `TargetManager`, `TemplateLockTracker`, local validation, ROI assist, night detector, lock telemetry, display state.
- A/B от 2026-04-29 показал, что отключение `TemplateLockTracker` ломает night gate по `id_chg/min`: 12.23 PASS против 36.70 FAIL.
- Native ByteTrack-only measurement от 2026-05-01 не готов к runtime replacement: на hard night/IR он часто не создает active track, поэтому низкий `id_chg/min` не является качественным tracking-успехом.
- Day false_lock на no-GT clip остается структурным артефактом оценки, а не сигналом качества модели.

## MGAP-001 — штатные трекеры Ultralytics

Полный прогон выполнен на `configs/regression_pack.csv`, preset `night`, baseline model from current config.

| Механизм | Современный статус | Текущий проект | Решение |
|----------|--------------------|----------------|---------|
| `ByteTrack` | Нативно поддержан в Ultralytics | Уже используется в `UltralyticsBackend.track_frame()` | Оставить как source of primary IDs; не считать отсутствующим |
| `BoT-SORT` | Нативный default tracker | Не используется runtime, но поддержан evaluation script | Измерен; не заменяет self-hold |
| `BoT-SORT + ReID` | Поддержан через `with_reid: True` в tracker YAML | Добавлен measurement-only config | Измерен; не заменяет self-hold |
| `persist=True` | Обязателен для frame loop | Уже используется | Оставить |
| `Results.boxes.id` | Канонический track ID API | Уже используется | Оставить |
| Tracker tuning YAML | Современный путь настройки без сторонних зависимостей | Не параметризован в runtime | Рассмотреть measurement-only tuning позже |

### MGAP-001 Measurement Summary

| Tracker | Config | Native presence | Native id_chg/min | Native false_lock | Native FPS | Decision |
|---------|--------|-----------------|-------------------|-------------------|------------|----------|
| `ByteTrack` | `bytetrack.yaml` | 0.1838 | 0.0000 | 0.1838 | 32.37 | FAIL as replacement |
| `BoT-SORT` | `botsort.yaml` | 0.1838 | 0.0000 | 0.1838 | 30.74 | FAIL as replacement |
| `BoT-SORT + ReID` | `configs/trackers/botsort_reid.yaml` | 0.3265 | 0.0000 | 0.3265 | 29.68 | FAIL as replacement |
| Project pipeline | current hybrid | 0.4379-0.4448 | 4.9752-7.0140 | 0.4379-0.4448 | 40.98-43.08 | KEEP |

Interpretation:

- `ByteTrack` and default `BoT-SORT` are effectively identical on this pack.
- Both native trackers produce zero ID churn mostly because they do not maintain active tracks on hard night/IR clips.
- `BoT-SORT + ReID` raises native presence on `Demo_IR_DRONE_146` from 0.0383 to 0.8946, but native false_lock rises to 0.8946 too; this is not a usable operator improvement.
- `BoT-SORT` and `BoT-SORT + ReID` emitted many `not enough matching points` warnings on `night_ground_indicator_lights`, consistent with weak global-motion compensation features in this scene.

Key per-clip results:

| Clip | Scene | Project presence | ByteTrack | BoT-SORT | BoT-SORT + ReID |
|------|-------|------------------|-----------|----------|-----------------|
| `night_ground_large_drones` | night | 0.5208 | 0.0000 | 0.0000 | 0.0000 |
| `Demo_IR_DRONE_146` | ir | 0.5399 | 0.0383 | 0.0383 | 0.8946 false_lock |
| `IR_DRONE_001` | ir | 0.4684 | 0.0000 | 0.0000 | 0.0000 |
| `IR_BIRD_001` | noise | 0.0581 | 0.0645 | 0.0645 | 0.0645 |
| `night_ground_indicator_lights` | noise | 0.0797-0.0815 | 0.0000 | 0.0000 | 0.0000 |

MGAP-001 decision: штатные Ultralytics trackers не могут заменить `TemplateLockTracker` / self-hold layer on current clips.

## MGAP-002 — самописные механизмы

| Компонент | Текущий метод | Современный аналог | Разрыв | Решение |
|-----------|---------------|--------------------|--------|---------|
| `TargetManager` | Active target policy, cooldown, drone score EMA, reacquire prediction | Native tracker association + app-level target policy | Нативный tracker не решает operator lock semantics | Оставить; дробить только по отдельному refactor task |
| `TemplateLockTracker` | `cv2.matchTemplate` continuity in focus mode | Native tracker buffers / BoT-SORT GMC/ReID | Старый метод, но gate-critical | Не удалять; заменить только после night gate proof |
| `NightSmallTargetDetector` | MOG2 + frame diff + contour confirmation | Detector-trained night/thermal model | Технический долг по detection quality | Измерить глубже; replacement требует dataset/model cycle |
| `ROI assist` | Motion proposals + crop YOLO | Higher-resolution detect / tiled inference / native solutions | Полезный локальный accelerator, но не стандартизован | Оставить; измерить ablation после tracker experiments |
| `Display overlay` | OpenCV text/HUD and PySide6 panels | Operator-grade UI/HUD with separated algorithm/display semantics | Визуальное отставание есть, но это не algorithm gap | Отдельный UI cycle, не смешивать с tracking decisions |

## MGAP-003 — модельный путь

Текущий baseline `drone_bird_probe_fast` остается production reference because night gate passes. Новизна `YOLO26` сама по себе не является основанием для baseline promotion.

Новый модельный путь:

1. Обновить будущие experiment docs/scripts с `YOLOv11` на `YOLO26` как текущую линию.
2. Запускать `YOLO26n` only as candidate/reference experiment.
3. Прогонять через existing intake/gate flow.
4. Сравнивать против baseline по project gate metrics, а не по upstream mAP/FPS.
5. Не менять `models/baseline.pt` без promotion contract.

## MGAP-004 — визуальное отставание

| Слой | Оценка |
|------|--------|
| Algorithm quality | Главный риск сейчас не UI, а hard night/IR detection presence и identity continuity |
| Operator display | OpenCV overlay функционален, но выглядит research-first; PySide6 уже частично вынесен в `app/ui` |
| Decision | UI улучшать отдельным циклом после algorithm decision; не использовать красивый HUD как доказательство качества tracking |

## MGAP-005 — матрица решений

| Компонент | Текущий метод | Современный путь | Разрыв | Риск изменения | Следующий эксперимент |
|-----------|---------------|------------------|--------|----------------|-----------------------|
| Primary tracking | Ultralytics `ByteTrack` via `model.track()` | `ByteTrack` / `BoT-SORT` native | ByteTrack уже есть; BoT-SORT не измерен | Средний: может снизить presence на night | Full `BoT-SORT` measurement на same packs |
| Active target policy | `TargetManager` | App-level policy поверх native IDs | Нужен проекту, upstream не заменяет | Высокий: ломает lock semantics | No rewrite; add focused metrics if needed |
| Lock continuity | `TemplateLockTracker` | Tracker tuning / BoT-SORT GMC/ReID | Старый метод, но gate-critical | Высокий: known night gate fail without it | Только ablation после BoT-SORT proof |
| Night detection | MOG2 + diff | Trained small-target/night model | Самый большой technical gap | Высокий: dataset/model dependency | Dataset/model planning, no runtime change now |
| ROI assist | Motion crop proposals | Tiled/high-res inference patterns | Нужна метрика contribution | Средний: may affect FPS/presence | ROI on/off ablation after tracker pass |
| Model family | Custom baseline from older line | `YOLO26n` candidate | Roadmap stale | Средний: new model may fail domain gate | Candidate-only `YOLO26n` intake benchmark |
| Quality gates | Project gate scripts | Contract-based evaluation | Уже хороший локальный путь | Низкий | Keep; add native tracker comparison reports |
| Display | OpenCV overlay + PySide6 panels | Operator HUD redesign | Visual gap separate from algorithm | Низкий/средний | UI audit cycle after algorithm experiments |

## Решение

1. Не заменять текущий project pipeline на native ByteTrack-only.
2. Не заменять текущий project pipeline на native `BoT-SORT`.
3. Не заменять текущий project pipeline на `BoT-SORT + ReID`; текущий ReID-прогон даёт false_lock regression на IR.
4. Не удалять `TemplateLockTracker`; он доказанно держит night gate по `id_chg/min`.
5. Считать `YOLO26` актуальным модельным направлением для будущих экспериментов.
6. Считать `NightSmallTargetDetector` главным modernity gap, но не менять его без dataset/model cycle.
7. Следующий безопасный эксперимент теперь не tracker replacement, а `YOLO26n` candidate-only intake/gate benchmark без baseline promotion.

## Что не менялось

- Runtime code.
- Baseline model.
- Thresholds.
- Presets.
- Training scripts.
- GUI.
- Dependencies.

Measurement-only tooling changed:

- `python_scripts/run_ultralytics_tracking_eval.py` now accepts `--tracker-config`.
- `configs/trackers/botsort_reid.yaml` was added for `BoT-SORT + ReID` measurement only.
- `tests/test_ultralytics_tracking_eval.py` covers tracker config resolution.

## Валидация

- `git pull --ff-only origin main` → up to date.
- Context7 `/websites/ultralytics` verified current tracking API and `YOLO26` examples.
- Local Ultralytics wiki route read.
- Runtime code inspected at line-level.
- Previous accepted reports cross-checked.
- `./tracker_env/bin/python -m pytest tests/test_ultralytics_tracking_eval.py -q` → 5 passed.
- `./tracker_env/bin/python -m compileall -q python_scripts/run_ultralytics_tracking_eval.py tests/test_ultralytics_tracking_eval.py` → OK.
- Full `ByteTrack` measurement completed.
- Full `BoT-SORT` measurement completed.
- Full `BoT-SORT + ReID` measurement completed.

## Остаточные риски

- `YOLO26` facts are current as of 2026-05-01; future Ultralytics docs may move again.
- Existing training scripts still mention `YOLOv11`; this report records the gap but does not patch scripts.
- Native tracker full results depend on actual clip coverage; smoke-only runs are not decision evidence.
- UI visual gap is intentionally separated from algorithm decisions.
