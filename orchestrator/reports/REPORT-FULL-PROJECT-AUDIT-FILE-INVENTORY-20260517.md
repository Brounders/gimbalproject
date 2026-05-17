# Приложение A — Полный аннотированный инвентарь файлов

**Дата:** 2026-05-17
**Ветка:** claude/sharp-rosalind-cdc716
**Всего файлов (без .git, __pycache__, .pyc):** 605
**Python-файлов:** 187 | **Markdown-файлов:** 295 | **YAML:** 17 | **CSV:** 29 | **JSON:** 22

---

## Тег-легенда

| Тег | Значение |
|-----|----------|
| CORE | Runtime-критично; нельзя трогать без полного гейта |
| ACTIVE | Используется в текущем цикле, не runtime-критично |
| LEGACY | Явно устаревшее или в папке legacy/ |
| GENERATED_ARTIFACT | Создаётся скриптами; .gitignore |
| GOVERNANCE | Только административные файлы |
| CANDIDATE_ARCHIVE | Можно заархивировать |
| UNKNOWN_NEEDS_TRACE | Назначение неочевидно |
| DO_NOT_TOUCH_CORE | Изменение требует полного гейта |

---

## src/uav_tracker/ — Ядро трекера (46 .py файлов)

| Файл | Размер | Тег | Примечание |
|------|--------|-----|------------|
| __init__.py | 588 б | CORE | Ленивый re-export Config/TrackerPipeline |
| config.py | 20 KB | DO_NOT_TOUCH_CORE | ~100 полей конфига; публичный API |
| pipeline.py | 58 KB | DO_NOT_TOUCH_CORE | Монолит TrackerPipeline+VideoSession+draw |
| evaluation.py | 15 KB | CORE | evaluate_source для EvaluationWorker |
| exceptions.py | 1.5 KB | CORE | ModelNotFoundError, SourceOpenError и др. |
| frame_context.py | 824 б | CORE | FrameContext per-frame метаданные |
| modes.py | 1.9 KB | CORE | apply_runtime_mode operator/research/rpi |
| profile_io.py | 9.4 KB | CORE | apply_overrides, available_presets |
| runtime_config.py | 2.0 KB | CORE | RuntimeConfigView |
| detection_source.py | 1.0 KB | CORE | DetectionSource enum; primary_sources() |
| runtime/__init__.py | - | CORE | create_detector_backend() |
| runtime/base.py | - | CORE | Detection dataclass, DetectorBackend Protocol |
| runtime/ultralytics_backend.py | - | CORE | YOLO inference + thread timeout |
| runtime/hailo_backend.py | - | CORE | Hailo/RPi5 backend |
| tracking/action_policy.py | - | CORE | ActionPolicy, behavior intent |
| tracking/bbox_stability.py | - | CORE | BboxStabilizer TASK-103a |
| tracking/continuity_tracker.py | - | CORE | Hit/miss история |
| tracking/evidence.py | - | CORE | TargetBelief, SOURCE_RELIABILITY |
| tracking/focus_mode_controller.py | - | CORE | Focus/reacquire режим |
| tracking/lock_event_tracker.py | - | CORE | Audit-trail lock событий |
| tracking/lock_tracker.py | - | CORE | TemplateLockTracker |
| tracking/operator_override.py | - | CORE | Команды оператора |
| tracking/operator_seed.py | - | CORE | refine_operator_seed_bbox |
| tracking/operator_workflow.py | - | CORE | OperatorWorkflowMachine |
| tracking/proposal_trust.py | - | CORE | SCENE_TRUST таблица TASK-103d |
| tracking/target_manager.py | - | CORE | TargetManager: выбор цели, lock, reacquire |
| tracking/tracked_target.py | - | CORE | TrackedTarget dataclass |
| tracking/tracking_state_machine.py | - | CORE | Конечный автомат трека |
| detectors/night_detector.py | - | CORE | NightSmallTargetDetector MOG2/diff/peak |
| detectors/roi_assist.py | - | CORE | MotionROIProposer |
| display/display_state_tracker.py | - | CORE | Состояние overlay |
| display/frame_result.py | - | CORE | FrameOutput |
| display/overlay.py | - | CORE | draw_frame и overlay helpers |
| domain/adapters.py | - | CORE | frame_result_from_output |
| domain/degradation.py | - | CORE | DegradationStatus, FailureCase |
| domain/telemetry.py | - | CORE | JsonlTelemetryWriter |
| pipeline_control/budget_controller.py | - | CORE | CPU-бюджет, адаптивный scan |
| utils/geometry.py | - | CORE | iou() |

---

## app/ — UI-слой (35 .py файлов + QML)

| Файл | Размер | Тег | Примечание |
|------|--------|-----|------------|
| dts_candidate_gate.py | 10 KB | CORE | Безопасная копия кандидата SAFE-001 |
| dts_diagnostics.py | 6.2 KB | CORE | Строит diagnostics.md для DTS compare |
| dts_training_loop.py | 2.6 KB | CORE | Training loop UX через subprocess |
| job_state_machine.py | 4.8 KB | CORE | Header state, job state |
| main_cli.py | 6.1 KB | CORE | CLI entrypoint |
| main_gui.py | 32 KB | DO_NOT_TOUCH_CORE | PySide6 монолит MainWindow |
| main_qml.py | 2.5 KB | CORE | QML entrypoint |
| profile_controller.py | 10.6 KB | CORE | Profile load/save/apply |
| source_controller.py | 2.1 KB | CORE | Source controls |
| stats_renderer.py | 11 KB | CORE | KPI overlay |
| training_desk_data.py | 7.3 KB | CORE | DTS data layer JSONL |
| training_desk_quality.py | 17.5 KB | CORE | Качество + дубликаты |
| workers.py | 16.4 KB | CORE | TrackerWorker, EvaluationWorker |
| ui/layout_builders.py | 22 KB | DO_NOT_TOUCH_CORE | Все PySide6 layout builders |
| ui/theme.py | 28 KB | CORE | APP_STYLESHEET, цвета, шрифты |
| ui/training_desk.py | 34 KB | DO_NOT_TOUCH_CORE | DTS диалог полный CRUD |
| ui/cards.py | - | CORE | build_target_info_card |
| ui/state_machine.py | - | CORE | UIState, UIStateMachine |
| ui/video_mapping.py | - | CORE | Координаты видео↔виджет |
| ui/video_stage.py | - | CORE | VideoStage QWidget |
| qml_bridge/*.py | - | CORE | 8 bridge классов для QML |
| qml/Main.qml + ~19 QML | - | ACTIVE | QML компоненты оператора |

---

## python_scripts/ — Инструменты (48 .py файлов + 3 .sh)

### Высокая ссылочность (10+ упоминаний в проекте)

| Файл | Refs | Тег | Назначение |
|------|------|-----|------------|
| run_quick_kpi_smoke.py | 26 | ACTIVE | Быстрый KPI-смок |
| install_baseline.py | 18 | ACTIVE | Установка baseline.pt |
| run_offline_benchmark.py | 15 | ACTIVE | Offline benchmark для gate |
| run_problem_pack_gate.py | 14 | ACTIVE | Gate problem pack |
| run_action_policy_gate.py | 10 | ACTIVE | ActionPolicy gate |

### Средняя ссылочность (3–9)

| Файл | Refs | Тег | Назначение |
|------|------|-----|------------|
| train_yolo_from_yaml.py | 9 | ACTIVE | YOLO training |
| stage_operator_training_pack.py | 8 | ACTIVE | DTS → YOLO pack |
| training_conveyor.py | 8 | ACTIVE | RTX конвейер |
| run_tracking_gt_diagnostics.py | 6 | ACTIVE | Target Lab GT диагностика |
| export_operator_annotations_to_yolo.py | 6 | ACTIVE | JSONL → YOLO labels |
| compare_kpi_snapshots.py | 6 | ACTIVE | KPI сравнение |
| run_model_battle.py | 4 | ACTIVE | A/B сравнение моделей |
| run_scenario_sweep.py | 4 | ACTIVE | Sweep сценариев |
| smoke_qml_mvp.py | 4 | ACTIVE | QML smoke |
| fetch_training_artifact.py | 5 | ACTIVE | GitHub Release → ZIP |
| run_intake.py | 5 | ACTIVE | Полный intake |
| publish_training_artifact.py | 3 | ACTIVE | Публикация артефакта |
| run_ultralytics_tracking_eval.py | 3 | ACTIVE | Ultralytics tracking eval |
| run_quality_gate.py | - | ACTIVE | Quality gate runner |

### Низкая ссылочность (0–2) — потенциальные кандидаты на архив

| Файл | Refs | Тег | Примечание |
|------|------|-----|------------|
| build_detector_evidence_pack.py | 0 | ACTIVE | Создан TASK-103h 2026-05-17 |
| build_gt_yolo_pack.py | 0 | ACTIVE | Создан TASK-104 2026-05-17 |
| diagnose_ir_hotspot_oracle.py | 0 | CANDIDATE_ARCHIVE | Нет тестов; не упоминается в активных задачах |
| diagnose_ir_sensitivity.py | 0 | CANDIDATE_ARCHIVE | Нет тестов |
| render_ir_detection_contact_sheets.py | 0 | ACTIVE | Создан TASK-107 |
| render_yolo_pack_contact_sheets.py | 1 | ACTIVE | Создан TASK-107 |
| build_mixed_dataset.py | 1 | CANDIDATE_ARCHIVE | 1 упоминание; нет тестов |
| monitor_six_hour_session.py | 1 | CANDIDATE_ARCHIVE | Специфичен для 6h сессий |
| summarize_batch_reports.py | 1 | CANDIDATE_ARCHIVE | 1 упоминание |
| dataset_audit.py | 2 | ACTIVE | Тест есть |
| validate_tracking_gt.py | 2 | ACTIVE | |
| replay_frame_telemetry.py | 2 | ACTIVE | Тест есть |

---

## tests/ — Тесты (56 файлов, 868 функций)

| Крупнейший файл | Функций |
|-----------------|---------|
| test_config.py | 74 |
| test_modes.py | 58 |
| test_target_manager_lifecycle.py | 52 |
| test_profile_io.py | 52 |
| test_extracted_components.py | 48 |
| test_replay_frame_telemetry.py | 33 |
| test_pipeline_helpers.py | 28 |
| test_stage_operator_training_pack.py | 26 |

---

## configs/ — Конфигурации (57 файлов)

| Файл | Тег | Примечание |
|------|-----|------------|
| default.yaml | CORE | Базовый пресет models/baseline.pt |
| tracking_live_auto.yaml | CORE | Live-auto; Target Lab использует этот пресет |
| night.yaml | CORE | Ночной режим |
| small_target.yaml | CORE | Маленькие цели; отключает night detector для EO |
| antiuav_thermal_peak.yaml | CORE | IR peak detector |
| antiuav_thermal_*.yaml (6 шт.) | CORE | IR варианты |
| night_field_osd.yaml | CORE | Ночь + OSD-safe |
| rpi_hailo.yaml | CORE | RPi5+Hailo |
| antiuav_02_1610_demo.yaml | CANDIDATE_ARCHIVE | Demo; 0 ссылок в коде |
| regression_pack*.csv (11 шт.) | CORE | Regression packs |
| action_policy_gate_pack.csv | CORE | ActionPolicy gate |
| gt_candidate_gate_pack*.csv | ACTIVE | GT gate packs |
| promotion_contract.yaml | CORE | Условия promote модели |
| dataset_contract.yaml | CORE | Dataset contract |
| problem_pack_gate_contract.json | CORE | Problem pack gate |
| ground_truth/regression_pack/ (10 JSON) | CORE | GT для Target Lab диагностики |
| gt_minipack/ | ACTIVE | GT minipack (15 CSV файлов) |

---

## legacy/ (4 файла) — LEGACY

benchmark.py, real_tracker.py, train_script.py — явно устаревшие; README.md документирует это.

---

## models/ — Модели

baseline_manifest.json — CORE. *.pt и *.hef — GENERATED_ARTIFACT (в .gitignore, физически отсутствуют).

---

## automation/ (7 файлов)

artifact_manifest.json и dataset_registry.json — CORE для RTX-Mac flow, но содержат Windows-пути и не обновлялись с марта 2026. CANDIDATE_ARCHIVE для путей.

---

## ui_web/ (26 файлов TSX/TS/JSON)

UNKNOWN_NEEDS_TRACE. TypeScript/React компоненты. CI строит. Не связаны с Python runtime.
Возможное назначение: веб-интерфейс для оператора или dashboard. Требует выяснения у Human/Codex.

---

## Entrypoints

| Файл | Тег | Назначение |
|------|-----|------------|
| main_tracker.py | CORE | Headless CLI |
| tracker_gui.py | CORE | GUI запуск |
| app/main_cli.py | CORE | CLI wrapper |
| app/main_gui.py | CORE | PySide6 GUI main |
| app/main_qml.py | CORE | QML GUI main |

---

*Конец инвентаря. Создано 2026-05-17.*
