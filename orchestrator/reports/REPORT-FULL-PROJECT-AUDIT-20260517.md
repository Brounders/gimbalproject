# Полный аудит проекта GimbalProject

**Дата:** 2026-05-17
**Ветка:** claude/sharp-rosalind-cdc716
**Аудитор:** Claude (read-only)
**Язык:** Русский (пути/код на английском)

---

## 1. Executive Summary

- **Проект находится в активной фазе tracker evolution.** Текущая активная задача: TASK-20260517-108 — сборка scale/source-aware weak4 pack для detector training. Plan ID: AP-TARGET-LAB-TRACKING-EVOLUTION-V1.

- **Compile check пройден без ошибок** для `python_scripts src app orchestrator tests`.

- **868 тест-функций в 56 файлах** — хорошее покрытие для Config, TargetManager, ActionPolicy, DTS, proposal trust, bbox stability, operator workflow.

- **Три entrypoint**: `main_tracker.py` (headless), `tracker_gui.py` (PySide6 GUI), `app/main_qml.py` (QML). Дублирование входных точек без явного RUNBOOK-указания какой использовать.

- **Два параллельных UI**: `app/main_gui.py` (PySide6/widgets, ~32 KB) и `app/main_qml.py` + `app/qml_bridge/` + `app/qml/*.qml` (QML). Оба активны. Это не случайность — они разные по назначению: main_gui старый desktop, main_qml новый operator UI.

- **Монолиты не устранены.** `src/uav_tracker/pipeline.py` (~58 KB) и `app/main_gui.py` (~32 KB) остаются большими, но декомпозиция частично выполнена (workers.py извлечён). `orchestrator/state/monolith_slicing_stage0.md` содержит план.

- **Нет модельных бинарей в репо.** `models/baseline.pt` в .gitignore; `baseline_manifest.json` указывает путь к бинарю на машине. YOLO26 smoke-run 2026-05-17 был остановлен и не произвёл артефактов.

- **Ключевой detector gap:** YOLO полностью отсутствует на IR weak clips (`9_dji2_range_medium` Hit@0.1=0.217, `antiuav_rgbt_20190925` Hit@0.1=0.333). Act5 selector/reacquire закрыт — следующий рычаг это targeted detector training.

- **`proposal_trust.py` SCENE_TRUST таблица** — ключевая инновация Act5 (TASK-103d). Calibrated по 14-клиповому GT minipack. Необходимо переоценить при изменении данных/модели.

- **python_scripts/ не документированы** — 48 скриптов без центрального README. Назначение 5 скриптов с 0 ссылками требует уточнения.

- **ui_web/ (`/ui_web/src/`) содержит TypeScript/React компоненты** (~26 файлов, 244 KB). Назначение не задокументировано. CI строит. Связь с Python runtime неизвестна.

- **automation/state/ содержит Windows-пути** (`C:\Users\PC\...`). Устарел с 2026-03-12/13. RTX-Mac sync flow требует актуализации.

- **TRAIN-20260517-002 (YOLO26 weak4 smoke)** числится как Draft/Not started. Попытка от 2026-05-17 была вручную остановлена и не считается результатом. Следующий тренинг требует полного smoke контракта с timeout и artifact gate.

---

## 2. Карта верхнеуровневых папок

```
GimbalProject/
├── src/               CORE    Ядро трекера: pipeline, config, tracking, detectors
├── app/               CORE    UI-слой: PySide6 GUI + QML + workers + DTS
├── python_scripts/    ACTIVE  48 инструментов: eval, training, GT, diagnostics
├── tests/             CORE    868 тестов, 56 файлов
├── configs/           CORE    YAML пресеты + CSV пакеты + GT JSON файлы
├── models/            CORE    baseline_manifest.json (бинари в .gitignore)
├── orchestrator/      GOVERNANCE  State + reports + tasks + briefs
├── legacy/            LEGACY  3 устаревших .py файла
├── automation/        ACTIVE  RTX конвейер state (Windows-пути, устарел)
├── docs/              GOVERNANCE  Архитектура, Codex role, Engineering codex
├── ui_web/            UNKNOWN TypeScript/React (~26 файлов); CI строит; назначение неизвестно
├── agents/            GOVERNANCE  auditor, engineer, manager MD
├── memory/            GOVERNANCE  Claude memory compiler (в .gitignore)
├── .ai/               GOVERNANCE  Architecture map, handoff, tasks
├── .claude/           GOVERNANCE  Settings, playbooks, skills, agents
├── .codex/            GOVERNANCE  Codex config + hooks
└── .github/           GOVERNANCE  CI workflow
```

---

## 3. Runtime Architecture — Пайплайн трекера

### Поток обработки кадра

```
TrackerPipeline.process_frame(frame)
  │
  ├─ 1. BudgetController.check()      # адаптивный CPU-бюджет
  │
  ├─ 2. Global YOLO scan              # GLOBAL_SCAN_INTERVAL (каждые N кадров)
  │     UltralyticsBackend.predict()  # source=YOLO
  │
  ├─ 3. Local validation scan         # если есть активная цель
  │     UltralyticsBackend.predict()  # crop вокруг bbox, source=LOCAL
  │
  ├─ 4. ROI assist                    # если ROI_ASSIST_ENABLED
  │     MotionROIProposer.propose()   # source=ROI
  │
  ├─ 5. Night/IR detector             # если сцена позволяет
  │     NightSmallTargetDetector.detect()  # source=NIGHT
  │     (MOG2 + frame diff + hotspot/peak)
  │
  ├─ 6. TemplateLockTracker.update()  # source=LOCK
  │     template matching в search window
  │
  ├─ 7. OperatorWorkflowMachine       # если оператор дал команду
  │     operator_seed + override      # source=OPERATOR
  │
  ├─ 8. TargetManager.age_targets()  # обновить все цели
  │
  ├─ 9. select_active() → legacy path
  │     pick_active_by_trust()        # TASK-103d SCENE_TRUST
  │     BboxStabilizer.smooth()       # TASK-103a EMA
  │
  ├─ 10. ActionPolicy.decide()        # keep/drop/telemetry
  │      FPIDSuppressor (weak evidence)
  │
  ├─ 11. DisplayStateTracker.update()
  │
  └─ 12. FrameOutput + JsonlTelemetryWriter
```

### Детектор бэкенды

| Бэкенд | Файл | Условие |
|--------|------|---------|
| UltralyticsBackend | `src/uav_tracker/runtime/ultralytics_backend.py` | По умолчанию |
| HailoBackend | `src/uav_tracker/runtime/hailo_backend.py` | device=hailo или path.endswith('.hef') |

Выбор: `create_detector_backend(model_path, device)` в `src/uav_tracker/runtime/__init__.py`.

### Критическая семантика DetectionSource

`DetectionSource.primary_sources()` включает: YOLO, ROI, LOCAL, LOCK, OPERATOR — **не включает NIGHT**.

Следствие:
- `has_confirmed_drone_lock()` отказывает non-primary активным целям
- drone_score обновляется только для primary sources
- night может быть выбрана trust-selector, но остаётся second-class для lock/focus семантики
- Зафиксировано как Known Design Decision в `orchestrator/reports/REPORT-TRACKING-TOOLS-AUDIT-20260517.md`

### Auto-scene detect

`tracking_live_auto.yaml`: `auto_scene_detect: true`. Контролирует переключение night/IR параметров детектора в реальном времени. Запускается каждый кадр (`auto_scene_sample_interval: 1`), подтверждение через 1 кадр (`auto_scene_confirm_frames: 1`).

### Lock/Reacquire политика (Act5, TASK-103a–103f)

| Механизм | Файл | TASK |
|---------|------|------|
| BboxStabilizer EMA | `tracking/bbox_stability.py` | 103a |
| Auto-scene v2 | `pipeline.py` | 103c |
| ProposalTrust SCENE_TRUST | `tracking/proposal_trust.py` | 103d |
| LockHealth release valve | `tracking/target_manager.py` `_low_trust_streak` | 103e |
| Reacquire suppression | `tracking/target_manager.py` `_health_released_tid` | 103f |

---

## 4. Tooling Architecture — python_scripts/

### Группы по назначению

**Evaluation/Gate (активно используются в gate циклах):**
- `run_quality_gate.py` — основной quality gate runner
- `run_quick_kpi_smoke.py` — быстрый KPI smoke (26 ссылок)
- `run_offline_benchmark.py` — полный offline benchmark
- `run_problem_pack_gate.py` — problem pack gate
- `run_action_policy_gate.py` — ActionPolicy gate
- `run_model_battle.py` — A/B сравнение моделей
- `run_scenario_sweep.py` — sweep по сценариям
- `compare_kpi_snapshots.py` — KPI snapshot сравнение

**Target Lab / GT:**
- `run_tracking_gt_diagnostics.py` — Target Lab GT диагностика (ключевой инструмент)
- `validate_tracking_gt.py` — валидация GT файлов
- `import_regression_pack_gt.py` — импорт GT
- `build_detector_evidence_pack.py` — detector evidence (TASK-103h, новый)
- `build_gt_yolo_pack.py` — GT → YOLO pack (TASK-104, новый)
- `render_yolo_pack_contact_sheets.py` — contact sheets (TASK-107)
- `render_ir_detection_contact_sheets.py` — IR contact sheets

**Dataset:**
- `dataset_audit.py` — аудит датасетов
- `convert_antiuav_rgbt_to_yolo.py` — конвертация AntiUAV
- `build_mixed_dataset.py` — смешанный датасет
- `sanitize_yolo_pairs.py` — очистка пар

**Training:**
- `train_yolo_from_yaml.py` — YOLO training
- `train_drone_bird.py` — drone+bird training
- `training_conveyor.py` — RTX конвейер
- `run_ultralytics_tracking_eval.py` — Ultralytics native tracking eval

**Operator/DTS:**
- `export_operator_annotations_to_yolo.py` — JSONL → YOLO labels
- `stage_operator_training_pack.py` — DTS → YOLO pack
- `replay_frame_telemetry.py` — replay JSONL телеметрии

**Model lifecycle:**
- `run_intake.py` — полный intake (проверка promotion_contract.yaml)
- `install_baseline.py` — установка baseline.pt
- `fetch_training_artifact.py` — GitHub Release → ZIP
- `publish_training_artifact.py` — публикация на GitHub
- `verify_baseline.py` — проверка baseline

**Diagnostics:**
- `build_diagnostics_report.py` — строит diagnostics.md
- `diagnose_ir_hotspot_oracle.py` — IR hotspot диагностика (0 ссылок)
- `diagnose_ir_sensitivity.py` — IR чувствительность (0 ссылок)
- `run_backend_parity.py` — parity Ultralytics/Hailo

---

## 5. Training/Evaluation Pipeline

### Путь обучения (текущий актуальный)

```
Operator clips (видео)
    │
    ├─ Target Lab (app/qml_bridge/target_lab_bridge.py)
    │   └─ run_tracking_gt_diagnostics.py → GT diagnostics
    │       matched/missed/off-target JPG samples
    │
    ├─ GT Assist (app/qml_bridge/gt_assist_bridge.py)
    │   └─ configs/gt_minipack/ → CSV файлы с GT строками
    │
    ├─ Operator Annotations (app/workers.py → JsonlTelemetryWriter)
    │   └─ runs/operator_annotations/*.jsonl (в .gitignore)
    │
    └─ DTS (app/ui/training_desk.py)
        review state → runs/operator_annotations/dts_review_state.json
        accepted/staged → export via:
            export_operator_annotations_to_yolo.py → YOLO labels
            stage_operator_training_pack.py → pack
```

### Текущий weak4 training cycle (TASK-108)

```
configs/gt_minipack/ (weak4 GT)
    │
    build_gt_yolo_pack.py
    [quarantine: 1_minie3_range_close wide strips]
    [quarantine: antiuav_rgbt_train large silhouettes as gate-only]
    │
    runs/training_packs/weak4_103h_20260517/ (в .gitignore)
    │
    train_yolo_from_yaml.py (RTX) → TRAIN-20260517-002
    (Статус: Draft/Not started; smoke contract не выполнен на RTX)
    │
    GitHub Release → fetch_training_artifact.py → run_intake.py
    │
    run_quality_gate.py (vs baseline_manifest.json)
    run_model_battle.py
    │
    dts_candidate_gate.py (safe copy only)
    │
    install_baseline.py (только после полного gate PASS)
```

### Gate артефакты

| Артефакт | Расположение | Статус |
|---------|-------------|--------|
| baseline_manifest.json | `models/baseline_manifest.json` | CORE; drone_bird_probe_fast 2026-03-14 |
| regression_pack*.csv | `configs/` | CORE; 11 pack файлов |
| promotion_contract.yaml | `configs/promotion_contract.yaml` | CORE; читается run_intake.py |
| problem_pack_gate_contract.json | `configs/problem_pack_gate_contract.json` | CORE |
| GT JSON files | `configs/ground_truth/regression_pack/` | CORE; 10 файлов |
| YOLO26 smoke (2026-05-17) | `runs/` | INVALID; только args.yaml, нет weights |

---

## 6. Orchestration Model

### Роли

| Роль | Ответственность | Авторитет |
|------|----------------|-----------|
| Human | Продуктовое направление, approvals | Финальное решение |
| Codex | Контроль проекта, аудиты, shaping планов | Может предлагать и выполнять |
| Claude | Bounded worker для одной задачи | Не может выбирать стратегию |
| Git + accepted reports | Факты что изменилось и почему | Высший авторитет для фактов |
| active_plan.md | Контроль текущего выполнения | Только если прошёл check_orchestration_state.py |

### State machine задач

```
open_tasks.md (backlog)
    │
    active_plan.md (execution allowed)
    │
    ├─ ACTIVE → выполнить → completed_tasks.md
    ├─ DONE → принять отчёт
    └─ DEFERRED → вернуть в open_tasks.md
```

### Текущее состояние

- `active_plan.md` Status: **Active**
- Активная задача: **TASK-20260517-108** (Scale/source-aware weak4 pack)
- Active RTX tasks: none
- Deferred: 3 задачи (commit boundary review, candidate data collection, full promotion gate)
- Open training: TRAIN-20260514-001 (Deferred), TRAIN-20260517-002 (Draft/Not started)

### CI Pipeline

`.github/workflows/ci.yml`:
- Python syntax check (`compileall`) на `python_scripts src app`
- pytest без зависимостей (PySide6 не устанавливается в CI)
- Node build для `ui_web/` (если есть `package.json`)
- `check_orchestration_state.py`

**Проблема:** тесты в CI запускаются без PySide6. Часть тестов (особенно DTS/QML) может быть пропущена или падать без GUI.

---

## 7. UI/App Layer

### PySide6 GUI (app/main_gui.py)

Монолит MainWindow со следующими слоями:
- `app/ui/layout_builders.py` — все layout builders (22 KB)
- `app/ui/theme.py` — стили (28 KB)
- `app/ui/training_desk.py` — DTS диалог (34 KB)
- `app/workers.py` — TrackerWorker, EvaluationWorker (извлечены)
- `app/ui/state_machine.py` — UIState, UIStateMachine
- `app/ui/video_stage.py` — VideoStage widget
- `app/ui/cards.py`, `command_console.py`, `expert_dialog.py`

DTS (Training Desk) в `app/ui/training_desk.py`:
- Полный CRUD для оператор-аннотаций
- Реальный quality check (Laplacian, exposure, bbox size)
- Реальная дедупликация
- Export YOLO через subprocess → `stage_operator_training_pack.py`
- Не запускает training автоматически

### QML UI (app/main_qml.py)

Современный operator UI через `app/qml/Main.qml` и `app/qml_bridge/`:
- `TrackerBridge` — мост к TrackerPipeline
- `DtsBridge` + `DtsFrameProvider` — DTS через QML
- `GtAssistBridge` + `GtFrameProvider` — GT материал
- `TargetLabBridge` — Target Lab диагностика
- `GeoBridge` — геокоординаты
- `SettingsBridge` — настройки из QML
- `AppState` — глобальное состояние

Target Lab (app/qml_bridge/target_lab_bridge.py):
- Запускает `run_tracking_gt_diagnostics.py` через QProcess
- Отображает matched/missed/off-target JPG samples
- `labSummaryText` — текстовая сводка для UI

### Дублирование UI

`app/main_gui.py` и `app/main_qml.py` — разные UI, но **одновременно активны**.
По `active_plan.md` QML (`app/main_qml.py`) является текущим operator UI для Target Lab workflow.
PySide6 widgets GUI (`app/main_gui.py`) остаётся как desktop research/operator fallback.

---

## 8. Data/Artifact Flow

```
Реальные видео (datasets/ — не в git)
    │
    ▼
Operator annotations
    app/workers.py → JsonlTelemetryWriter
    runs/operator_annotations/*.jsonl (в .gitignore)
    │
    ▼
GT material
    configs/gt_minipack/*.csv (в git)
    configs/ground_truth/regression_pack/*.json (в git)
    │
    ▼
Training packs
    build_gt_yolo_pack.py → runs/training_packs/ (в .gitignore)
    stage_operator_training_pack.py → runs/operator_training_packs/ (в .gitignore)
    │
    ▼
Model training (RTX)
    train_yolo_from_yaml.py
    runs/detect/runs/*/weights/best.pt (в .gitignore)
    │
    ▼
Artifact publication
    publish_training_artifact.py → GitHub Release
    │
    ▼
Mac intake
    fetch_training_artifact.py → ZIP
    run_intake.py → quality gate check vs promotion_contract.yaml
    run_quality_gate.py, run_model_battle.py
    │
    ▼
Acceptance decision
    dts_candidate_gate.py → safe copy в models/candidates/
    install_baseline.py → models/baseline.pt (только после gate PASS)
    baseline_manifest.json обновляется
```

---

## 9. File And Folder Classification

| Папка | Тег | LOC (Python) | Примечание |
|-------|-----|-------------|------------|
| `src/uav_tracker/` | DO_NOT_TOUCH_CORE | ~12000 (оценочно) | 46 Python файлов |
| `app/` | DO_NOT_TOUCH_CORE | ~15000 (оценочно) | 35 Python + QML |
| `python_scripts/` | ACTIVE | ~8000 (оценочно) | 48 Python файлов |
| `tests/` | CORE | ~17000 (оценочно) | 56 файлов, 868 тестов |
| `configs/` | CORE | — | 57 файлов |
| `models/` | CORE | — | Только manifest; бинари в .gitignore |
| `orchestrator/` | GOVERNANCE | — | ~1.3 MB |
| `legacy/` | LEGACY | ~500 | 3 устаревших файла |
| `automation/` | ACTIVE | — | RTX state; Windows-пути |
| `ui_web/` | UNKNOWN_NEEDS_TRACE | — | TypeScript/React |
| `docs/` | GOVERNANCE | — | |
| `memory/` | GOVERNANCE | — | В .gitignore |

---

## 10. Dead/Legacy/Duplicate Candidates

### SAFE_TO_IGNORE / CANDIDATE_ARCHIVE

| Путь | Ссылки | Риск | Рекомендация |
|------|--------|------|-------------|
| `configs/antiuav_02_1610_demo.yaml` | 0 | НИЗКИЙ | CANDIDATE_ARCHIVE — добавить в .gitignore или удалить |
| `python_scripts/diagnose_ir_hotspot_oracle.py` | 0 | НИЗКИЙ | CANDIDATE_ARCHIVE — нет тестов, покрыто build_detector_evidence_pack |
| `python_scripts/diagnose_ir_sensitivity.py` | 0 | НИЗКИЙ | CANDIDATE_ARCHIVE — нет тестов |
| `python_scripts/monitor_six_hour_session.py` | 1 | НИЗКИЙ | CANDIDATE_ARCHIVE — специфичен для RTX 6h сессий |
| `python_scripts/summarize_batch_reports.py` | 1 | НИЗКИЙ | CANDIDATE_ARCHIVE — batch режим заменён GT diagnostics |
| `python_scripts/build_mixed_dataset.py` | 1 | НИЗКИЙ | CANDIDATE_ARCHIVE — смешанный датасет не в текущем цикле |

### NEEDS_OWNER_DECISION

| Путь | Причина | Вопрос |
|------|---------|--------|
| `ui_web/` | Нет документации назначения | Это standalone web UI? Связан с Python runtime? |
| `automation/state/artifact_manifest.json` | Windows-пути, устарел с 2026-03-13 | Обновлять на Mac или оставить только для RTX? |
| `automation/state/dataset_registry.json` | Windows-пути, устарел с 2026-03-12 | Аналогично |
| `app/main_gui.py` vs `app/main_qml.py` | Два активных UI | Какой является primary operator UI? |

### DO_NOT_TOUCH_CORE

| Путь | Обоснование |
|------|-------------|
| `src/uav_tracker/pipeline.py` | Runtime критично; любое изменение требует полного gate |
| `src/uav_tracker/config.py` | Public API для всех модулей; изменение ломает тесты |
| `src/uav_tracker/tracking/target_manager.py` | 52 теста; Act5 logic |
| `src/uav_tracker/tracking/proposal_trust.py` | Calibrated SCENE_TRUST; Act5 |
| `app/ui/training_desk.py` | DTS review state; реальные данные оператора |
| `app/training_desk_data.py` | DTS data layer; read/write review state |

### GENERATED_ARTIFACT (не в git)

- `runs/` — все runtime артефакты
- `models/*.pt`, `models/*.hef` — model binaries
- `datasets/` — обучающие датасеты
- `logs/` — логи
- `exports/`, `imports/` — pipeline артефакты

---

## 11. Test Coverage And Gaps

### Хорошо покрыто

| Механизм | Тест файлы |
|---------|-----------|
| Config параметры и загрузка | test_config.py (74 теста), test_config_defaults.py, test_config_validate.py |
| Runtime modes | test_modes.py (58 тестов) |
| TargetManager lifecycle, switch, cooldown | test_target_manager_lifecycle.py (52), test_target_manager_lock_policy.py (12) |
| Profile I/O | test_profile_io.py (52 теста) |
| ActionPolicy | test_action_policy.py (25), test_action_policy_behavior.py (17), test_action_policy_gate.py |
| DTS data layer | test_training_desk_data.py, test_training_desk_quality.py |
| DTS UX | test_dts_candidate_gate.py, test_dts_compare_ux.py, test_dts_training_loop.py |
| Operator annotation export | test_operator_annotation_export.py (19 тестов) |
| Stage operator training pack | test_stage_operator_training_pack.py (26 тестов) |
| Proposal trust | test_proposal_trust.py (14 тестов) |
| Bbox stability | test_bbox_stability.py (12 тестов) |
| Focus mode controller | test_focus_mode_controller.py |
| Lock tracker | test_lock_tracker.py |
| Lock health | test_lock_health.py |
| Operator workflow | test_operator_workflow.py, test_operator_override.py |
| GT tools | test_tracking_gt_tools.py (15 тестов) |
| Target Lab bridge | test_target_lab_bridge.py (12 тестов) |
| QML app state | test_qml_app_state.py (20 тестов) |

### Пробелы в покрытии

| Механизм | Статус | Риск |
|---------|--------|------|
| `NightSmallTargetDetector` | Нет юнит-тестов | ВЫСОКИЙ — критично для IR recall |
| `HailoBackend` | Нет тестов (платформозависим) | СРЕДНИЙ |
| `UltralyticsBackend` | Нет прямых тестов (требует GPU/model) | СРЕДНИЙ |
| `pipeline.py` полный pipeline | Нет интеграционных тестов | ВЫСОКИЙ — монолит |
| CI с PySide6 | pytest запускается без PySide6 в CI | ВЫСОКИЙ — UI тесты могут падать |
| `build_detector_evidence_pack.py` | Нет тестов (новый скрипт) | СРЕДНИЙ |
| `build_gt_yolo_pack.py` | Нет тестов (новый скрипт) | СРЕДНИЙ |
| SCENE_TRUST calibration | Тест на значения таблицы есть, но нет теста на regression поведение | СРЕДНИЙ |
| auto_scene_detect | test_live_scene_runtime.py есть | НИЗКИЙ |

---

## 12. Root Problems

### P1 — Detector recall gap на IR weak clips (КРИТИЧНО)

**Проблема:** YOLO полностью отсутствует на `9_dji2_range_medium` и `antiuav_rgbt_20190925_200805`:
- `9_dji2_range_medium`: Hit@0.1=0.217 (best: antiuav_thermal_peak)
- `antiuav_rgbt_20190925_200805_1_2_infrared`: Hit@0.1=0.333

**Причина:** weak4 training pack содержит несовместимые позитивные геометрии:
- Широкие горизонтальные strips от `1_minie3_range_close`
- Крупные aircraft-silhouette от `antiuav_rgbt_train`
- Компактные hotspot боксы (желаемый режим)

**Статус:** TASK-20260517-108 активна для решения.

### P2 — NightSmallTargetDetector: высокая дисперсия качества

**Проблема:** `IR_DRONE_025` recall=0.987, `9_dji2_range_medium` практически ноль. Один и тот же MOG2+diff алгоритм. Дисперсия объясняется клиповой спецификой (расстояние, угол, тепловой контраст), но это означает непредсказуемость в новых клипах.

### P3 — Монолиты не устранены

`pipeline.py` (~58 KB) и `main_gui.py` (~32 KB) остаются большими. `monolith_slicing_stage0.md` содержит план, но реализация деferred. Добавление фич в эти файлы продолжает усугублять проблему.

### P4 — DetectionSource.NIGHT не является primary

Архитектурное решение безопасности мешает эволюции night/IR tracking. При добавлении NIGHT в primary_sources() нужен полный gate (risk count, false_lock, id_chg).

### P5 — Два параллельных UI без четкого приоритета

`app/main_gui.py` и `app/main_qml.py` оба активны. Это не bug, но документация о том, какой использовать для каких сценариев, отсутствует в RUNBOOK.md.

### P6 — RTX-Mac sync state устарел

`automation/state/` содержит Windows-пути и данные от марта 2026. TRAIN-20260517-002 числится Draft/Not started — нет корневого артефакта.

### P7 — ui_web/ без документации

26 файлов TypeScript/React. CI строит. Назначение не задокументировано. Возможная потеря ресурсов на поддержку невостребованного кода.

---

## 13. Modernization Vector

### Краткосрочные улучшения (без изменения runtime)

1. **Документировать python_scripts/** — добавить README.md с таблицей "скрипт → назначение → когда запускать"
2. **Документировать ui_web/** — выяснить и зафиксировать назначение
3. **Архивировать 5 устаревших скриптов** (diagnose_ir_*, monitor_six_hour, summarize_batch, build_mixed_dataset)
4. **Актуализировать automation/state/** — убрать жёстко заданные Windows-пути или задокументировать что они RTX-specific

### Среднесрочные улучшения (требуют gate)

5. **NightSmallTargetDetector unit tests** — добавить тесты с synthetic контентом (градиент, тепловой blob)
6. **Pipeline integration test** — добавить smoke test с synthetic видео или кадрами
7. **CI с PySide6** — добавить offscreen Qt тест в CI или explicit skip
8. **SCENE_TRUST regression test** — тест что SCENE_TRUST таблица не ломает известные хорошие клипы

### Долгосрочные улучшения (NEEDS_OWNER_DECISION)

9. **Декомпозиция pipeline.py** — по monolith_slicing_stage0.md
10. **DetectionSource.NIGHT promotion decision** — явное architecture decision record
11. **ByteTrack/SORT** — оценено, rejected в REPORT-BYTETRACK-EVAL-20260501.md; переоценить после detector improvement

---

## 14. Proposed Folder Restructure

Подробный plan в приложении B. Краткое summary:

```
Без изменений:      src/, app/, tests/, configs/, models/, orchestrator/
Phase 0 (безопасно): удалить antiuav_02_1610_demo.yaml
Phase 1 (безопасно): архивировать 5 python_scripts
Phase 2 (решение):  python_scripts/ → tools/
Phase 3 (решение):  декомпозиция монолитов
Phase 4 (решение):  ui_web/ clarification
```

---

## 15. Migration Plan

**Phase 0:** Одобрена для немедленного выполнения — 0 import fixes.
**Phase 1:** Одобрена после Phase 0 — только перемещение, не удаление.
**Phase 2–4:** Требуют Human/Codex decision перед началом.

Подробные шаги и верификационные команды в `REPORT-FULL-PROJECT-AUDIT-RESTRUCTURE-PLAN-20260517.md`.

---

## 16. High-Impact Next Tasks (Top 10)

Ранжированы по impact на текущие цели.

| # | Задача | Impact | Файлы |
|---|--------|--------|-------|
| 1 | TASK-20260517-108: Scale/source-aware weak4 pack | КРИТИЧНО | build_gt_yolo_pack.py, weak4 pack |
| 2 | Smoke contract для TRAIN-20260517-002 на RTX | ВЫСОКИЙ | train_yolo_from_yaml.py |
| 3 | Добавить unit tests для NightSmallTargetDetector | ВЫСОКИЙ | detectors/night_detector.py |
| 4 | Задокументировать ui_web/ | СРЕДНИЙ | ui_web/README.md |
| 5 | Документировать python_scripts/ README | СРЕДНИЙ | python_scripts/README.md |
| 6 | Архивировать 5 устаревших python_scripts | СРЕДНИЙ | см. раздел 10 |
| 7 | CI: добавить offscreen PySide6 sanity test | СРЕДНИЙ | .github/workflows/ci.yml |
| 8 | Актуализировать automation/state/ RTX пути | СРЕДНИЙ | automation/state/*.json |
| 9 | Добавить integration smoke test для pipeline | СРЕДНИЙ | tests/test_pipeline_smoke.py |
| 10 | Commit boundary review (TASK-20260514-093) | СРЕДНИЙ | git status |

---

## 17. Risks And Open Questions

### Технические риски

| Риск | Серьёзность | Статус |
|------|-------------|--------|
| YOLO recall=0 на 2 IR клипах | КРИТИЧНО | Активно решается (TASK-108) |
| NightSmallTargetDetector дисперсия | ВЫСОКИЙ | Нет тестов; нужны после detector training |
| TRAIN-20260517-002 не запущен на RTX | ВЫСОКИЙ | Smoke contract готов, но нет RTX run |
| pipeline.py монолит трудно тестировать | СРЕДНИЙ | monolith_slicing_stage0.md есть |
| CI без PySide6 | СРЕДНИЙ | UI тесты могут пройти только офлайн |
| DetectionSource.NIGHT не primary | СРЕДНИЙ | Known design decision, зафиксировано |

### Открытые вопросы

| Вопрос | Где искать ответ |
|--------|----------------|
| ui_web/ — что это? | Human/Codex решение |
| automation/state/ Windows-пути — обновлять? | Human/Codex решение |
| Когда TRAIN-20260517-002 уйдёт на RTX? | Human approval |
| DetectionSource.NIGHT → primary? | Требует gate evidence |
| main_gui.py vs main_qml.py — какой primary? | Human/Codex решение для RUNBOOK.md |
| Commit boundary review (TASK-093) — когда? | Deferred; нужно до remote push |
| configs/gt_minipack/generated/ в .gitignore? | UNKNOWN_NEEDS_TRACE |

---

## 18. Appendix Links

- **Инвентарь файлов:** `orchestrator/reports/REPORT-FULL-PROJECT-AUDIT-FILE-INVENTORY-20260517.md`
- **План реструктуризации:** `orchestrator/reports/REPORT-FULL-PROJECT-AUDIT-RESTRUCTURE-PLAN-20260517.md`
- **Активный план:** `orchestrator/state/active_plan.md`
- **Открытые задачи:** `orchestrator/state/open_tasks.md`
- **Open training:** `orchestrator/state/open_training.md`
- **Monolith slicing:** `orchestrator/state/monolith_slicing_stage0.md`
- **Tracking tools audit:** `orchestrator/reports/REPORT-TRACKING-TOOLS-AUDIT-20260517.md`
- **Detector evidence:** `orchestrator/reports/REPORT-DETECTOR-EVIDENCE-WEAK4-20260517.md`
- **Label audit:** `orchestrator/reports/REPORT-TASK-107-WEAK4-LABEL-AUDIT-20260517.md`
- **Act5 final:** `orchestrator/reports/REPORT-TASK-103-ACT5-FINAL-20260516.md`

---

*Создано аудитором Claude (read-only) 2026-05-17. Изменений кода не вносилось.*
