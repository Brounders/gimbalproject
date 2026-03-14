# RUNBOOK — Система сопровождения БПЛА

> Единый источник истины по запуску и ролям команд.
> См. также: [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md)

---

## Быстрый старт (GUI)

```bash
source tracker_env/bin/activate
PYTHONPATH=src python tracker_gui.py
```

---

## Канонические точки входа

| Команда | Контур | Описание |
|---------|--------|----------|
| `tracker_gui.py` | Operator | GUI-оболочка (`app/main_gui.py`) |
| `main_tracker.py` | Operator/Research | CLI-оболочка (`app/main_cli.py`) |

Оба файла — тонкие проксари. Они не содержат логику.

---

## Operator: GUI

```bash
source tracker_env/bin/activate
PYTHONPATH=src python tracker_gui.py
```

Открывает главное окно с панелями: HeaderBar / LeftControlRail / VideoStage / BottomConsole.

**Канонические режимы оператора** (кнопки левой панели):

| Кнопка | Пресет | Описание |
|--------|--------|----------|
| Авто | `default` | Адаптивный: Auto Scene Detection (Day/Night/IR) |
| День | `default` (night off) | Только дневной детектор |
| Ночь | `night` | Ночной пресет |
| IR | `antiuav_thermal` | Thermal / Anti-UAV пресет |

---

## Operator: CLI

```bash
source tracker_env/bin/activate
PYTHONPATH=src python main_tracker.py --source 0 --preset default
PYTHONPATH=src python main_tracker.py --source test_videos/clip.mp4 --preset night
PYTHONPATH=src python main_tracker.py --help
```

---

## Evaluation

### Quick KPI smoke

```bash
source tracker_env/bin/activate
PYTHONPATH=src python python_scripts/run_quick_kpi_smoke.py \
    --sources test_videos/clip1.mp4,test_videos/clip2.mp4 \
    --preset default \
    --max-frames 300
```

Аргументы: `--sources`, `--pack` (CSV), `--preset`, `--max-frames`, `--mode`, `--output-json`, `--output-csv`.

### Quality gate (regression)

**Regression pack-файлы по сценариям:**

| Pack-файл | Пресет | Клипы |
|-----------|--------|-------|
| `configs/regression_pack.csv` | любой | все сценарии (полный set) |
| `configs/regression_pack_day.csv` | `default` | только дневные клипы |
| `configs/regression_pack_night.csv` | `night` | ночные + noise клипы |
| `configs/regression_pack_ir.csv` | `antiuav_thermal` | IR/thermal клипы |

```bash
source tracker_env/bin/activate

# Полный gate (все сценарии)
PYTHONPATH=src python python_scripts/run_quality_gate.py

# Per-scenario
PYTHONPATH=src python python_scripts/run_quality_gate.py \
    --pack-file configs/regression_pack_day.csv --preset default
PYTHONPATH=src python python_scripts/run_quality_gate.py \
    --pack-file configs/regression_pack_night.csv --preset night
PYTHONPATH=src python python_scripts/run_quality_gate.py \
    --pack-file configs/regression_pack_ir.csv --preset antiuav_thermal
```

Exit code: `0` = PASS, `4` = FAIL, `2` = config error.

#### Day Gate — известное ограничение (FPS-only)

Клип `drone_closeup_mixkit_44644_360.mp4` не имеет GT-файла (`label.json` / `gt.json`).
В `evaluation.py` метрика `false_lock` считает как false_lock **каждый** кадр, где tracker
активен, а `gt_visible=False`. Без GT — `gt_visible` всегда `False` → `false_lock=1.000`
гарантирован для **любой** модели, включая de-facto baseline.

**Следствие:** `false_lock` из day gate **не является дифференциатором** между моделями.
Используйте day gate только для сравнения `fps` и `active_id_changes_per_min`.
Для добавления GT: поместите `label.json` или `gt.json` рядом с видеофайлом.

#### Канонический запуск по контексту

```bash
# Авто-выбор pack-file и preset по контексту сценария:
PYTHONPATH=src python python_scripts/run_quality_gate.py --context day
PYTHONPATH=src python python_scripts/run_quality_gate.py --context night
PYTHONPATH=src python python_scripts/run_quality_gate.py --context ir

# С кандидатом и baseline comparison:
PYTHONPATH=src python python_scripts/run_quality_gate.py \
    --context night --model <candidate.pt> \
    --baseline runs/evaluations/quality_gate/baseline_quality_gate_night.json \
    --tag candidate_v1_
```

### Problem-clip fast loop

Быстрая проверка на проблемных клипах до/после runtime tuning.
Pack-файлы:
- `configs/regression_pack_problem_night.csv`
- `configs/regression_pack_problem_ir.csv`

```bash
# Быстрая проверка KPI (180 кадров, night пресет)
PYTHONPATH=src python python_scripts/run_quick_kpi_smoke.py \
    --sources test_videos/night_ground_large_drones.mp4,test_videos/night_ground_indicator_lights.mp4,test_videos/IR_DRONE_001.mp4,test_videos/Demo_IR_DRONE_146.mp4 \
    --preset night --max-frames 180

# Full gate на problem pack (ночные + noise клипы)
PYTHONPATH=src python python_scripts/run_quality_gate.py \
    --pack-file configs/regression_pack_problem_night.csv \
    --preset night

# Full gate на problem pack (IR клипы)
PYTHONPATH=src python python_scripts/run_quality_gate.py \
    --pack-file configs/regression_pack_problem_ir.csv \
    --preset antiuav_thermal
```

### Problem-pack mini-gate (threshold contract)

Явный threshold contract для hard clips. Более lenient, чем основной gate.
Threshold values определены в `configs/problem_pack_gate_contract.json`.

**One-command invocation (AP-021+):**
```bash
PYTHONPATH=src python python_scripts/run_problem_pack_gate.py
```
Wrapper читает `configs/problem_pack_gate_contract.json`, запускает gate на night и IR клипах раздельно,
возвращает exit code 0 (all pass) или 4 (any fail).

**Ручной запуск (canonical invocations из contract):**
```bash
# Night clips (night_ground_large_drones + night_ground_indicator_lights)
# AP-022+: night scene uses --max-night-id-changes-per-min (separate from noise and ir/day)
PYTHONPATH=src python python_scripts/run_quality_gate.py \
    --pack-file configs/regression_pack_problem_night.csv \
    --preset night \
    --max-id-changes-per-min 25 \
    --max-night-id-changes-per-min 18 \
    --min-continuity 0.30 \
    --min-presence 0.05 \
    --max-false-lock-rate 0.55 \
    --max-noise-false-lock-rate 0.35 \
    --max-noise-id-changes-per-min 15

# IR clips (IR_DRONE_001 + Demo_IR_DRONE_146)
PYTHONPATH=src python python_scripts/run_quality_gate.py \
    --pack-file configs/regression_pack_problem_ir.csv \
    --preset antiuav_thermal \
    --max-id-changes-per-min 25 \
    --min-continuity 0.30 \
    --min-presence 0.05 \
    --max-false-lock-rate 0.55 \
    --max-noise-false-lock-rate 0.35 \
    --max-noise-id-changes-per-min 15
```

Contract: `configs/problem_pack_gate_contract.json` — версионированный файл с rationale и canonical invocations.

### A/B evidence loop (problem clips)

Канонический before/after workflow для измерения эффекта runtime tuning на problem clips.

**Шаг 1 — снять before-снимок (до изменений):**
```bash
mkdir -p runs/evaluations/ab
PYTHONPATH=src python python_scripts/run_quick_kpi_smoke.py \
    --pack configs/regression_pack_problem_night.csv \
    --preset night --max-frames 180 \
    --output-json runs/evaluations/ab/before_night.json
```

**Шаг 2 — внести изменения в YAML конфиги.**

**Шаг 3 — снять after-снимок:**
```bash
PYTHONPATH=src python python_scripts/run_quick_kpi_smoke.py \
    --pack configs/regression_pack_problem_night.csv \
    --preset night --max-frames 180 \
    --output-json runs/evaluations/ab/after_night.json
```

**Шаг 4 — сравнить delta-таблицу:**
```bash
python python_scripts/compare_kpi_snapshots.py \
    runs/evaluations/ab/before_night.json \
    runs/evaluations/ab/after_night.json
```

Символы в колонке OK?: `✓` = значимое улучшение, `✗` = значимый регресс, ` ` = нет изменений.
По умолчанию порог значимости `--threshold 0.05`.

### Offline benchmark

```bash
source tracker_env/bin/activate
PYTHONPATH=src python python_scripts/run_offline_benchmark.py --help
```

### Scenario sweep

```bash
source tracker_env/bin/activate
PYTHONPATH=src python python_scripts/run_scenario_sweep.py --help
```

---

## Локальный quality-gate flow (baseline/candidate decision)

Канонический порядок для принятия решений о модели на Mac:

| Шаг | Команда | Что проверяет | PASS |
|-----|---------|---------------|------|
| **1. Quick smoke** | `run_quick_kpi_smoke.py` | FPS, id_changes, false_lock_rate на 1-2 клипах | FPS > 8, без краша |
| **2. Benchmark** | `run_offline_benchmark.py` | Полная прогонка по сценарию | Метрики в пределах baseline |
| **3a. Gate day** | `run_quality_gate.py --context day` | Дневные клипы, preset=default | Exit 0 |
| **3b. Gate night** | `run_quality_gate.py --context night` | Ночные клипы, preset=night | Exit 0 |
| **3c. Gate ir** | `run_quality_gate.py --context ir` | IR/thermal клипы, preset=antiuav_thermal | Exit 0 |
| **4. Decision** | результаты всех трёх gate | Все три context-gate PASS | promote |

> **Правило promote:** ВСЕ три context-gate (day + night + ir) должны вернуть exit 0.
> Если хотя бы один — FAIL: `hold_and_tune` или `reject`. См. [models/README.md](models/README.md).

```bash
source tracker_env/bin/activate

# Шаг 1: Quick smoke (ночной пресет, 180 кадров)
PYTHONPATH=src python python_scripts/run_quick_kpi_smoke.py \
    --sources test_videos/night_ground_large_drones.mp4 \
    --preset night --max-frames 180

# Шаг 2: Offline benchmark (ночной сценарий)
PYTHONPATH=src python python_scripts/run_offline_benchmark.py \
    --source-list configs/regression_pack_night.csv --preset night

# Шаги 3a-3c: Quality gate по контекстам
PYTHONPATH=src python python_scripts/run_quality_gate.py --context day
PYTHONPATH=src python python_scripts/run_quality_gate.py --context night
PYTHONPATH=src python python_scripts/run_quality_gate.py --context ir

# Шаг 4: Все три exit 0 → promote через install_baseline.py
```

> Для candidate-модели добавить `--model <path>` в шаги 1-3.
> Threshold'ы baseline: см. [OPERATOR_BASELINE.md](OPERATOR_BASELINE.md).

### Decision artifact standard

**Canonical output (per context):**

| Context | Output JSON |
|---------|-------------|
| day | `runs/evaluations/quality_gate/<tag>quality_gate_default.json` |
| night | `runs/evaluations/quality_gate/<tag>quality_gate_night.json` |
| ir | `runs/evaluations/quality_gate/<tag>quality_gate_antiuav_thermal.json` |

Задать тег через `--tag`:
```bash
# Именование: baseline_YYYYMMDD или candidate_vN_YYYYMMDD
PYTHONPATH=src python python_scripts/run_quality_gate.py --context night --tag candidate_v1_20260312_
```

**Ключевые поля JSON (`report_type: "quality_gate"`):**

| Поле | Тип | Значение |
|------|-----|----------|
| `report_type` | str | `"quality_gate"` |
| `context` | str | `"day"` \| `"night"` \| `"ir"` \| `""` |
| `gate_passed` | bool | `true` = PASS, `false` = FAIL |
| `failures` | list[str] | Список источник: fail_reasons |
| `mean` | dict | Агрегированные метрики по всем клипам |
| `rows[].passed` | bool | Результат по каждому клипу |
| `rows[].fail_reasons` | str | Конкретные нарушения threshold |

**Правило принятия решения (promote):**
- ВСЕ три context-gate (`day` + `night` + `ir`) `gate_passed = true` → promote
- Любой FAIL, нарушения tunable → `hold_and_tune`
- Любой FAIL, регресс за границы tolerance → `reject`

**Install (promote):**
```bash
PYTHONPATH=src python python_scripts/install_baseline.py \
    --source <accepted_candidate.pt> \
    --notes "Accepted YYYYMMDD: <description>" \
    --gate-report runs/evaluations/quality_gate/<tag>quality_gate_night.json \
    --preset-gates "day=runs/evaluations/quality_gate/<tag>quality_gate_default.json,night=runs/evaluations/quality_gate/<tag>quality_gate_night.json,ir=runs/evaluations/quality_gate/<tag>quality_gate_antiuav_thermal.json"
```

States и governance: [models/README.md](models/README.md)

### Canonical summary contract

Все benchmark/gate JSON содержат поле `report_type` для различения:

| Поле | Quality Gate JSON | Benchmark JSON |
|------|------------------|----------------|
| `report_type` | `"quality_gate"` | `"benchmark"` |
| `gate_passed` | bool | — |
| `context` | `"day"`/`"night"`/`"ir"`/`""` | — |
| `tag` | — | string |
| `preset` | string | string |
| `mean` | dict (avg metrics) | dict (avg metrics) |
| `rows` | list | list |
| `failures` | list[str] | — |

**Правило:** канонический decision artifact = `quality_gate_<preset>.json`.
Benchmark JSON используется для exploratory evaluation, не для промоушена.

---

## Training

> **Примечание:** training-контур предполагает наличие dataset в `datasets/` и GPU.

### Запуск обучения

```bash
source tracker_env/bin/activate
PYTHONPATH=src python python_scripts/train_yolo_from_yaml.py --help
PYTHONPATH=src python python_scripts/train_drone_bird.py --help
```

### Утилиты датасета

```bash
python python_scripts/sanitize_yolo_pairs.py --help     # проверка пар label/image
python python_scripts/build_mixed_dataset.py --help     # сборка mixed датасета
python python_scripts/convert_antiuav_rgbt_to_yolo.py  # конвертация Anti-UAV RGBT
```

### Мониторинг обучения

```bash
python python_scripts/watch_training_progress.py        # live-прогресс
python python_scripts/check_training_status.py          # статус текущего run
python python_scripts/monitor_six_hour_session.py       # мониторинг 6-часовой сессии
python python_scripts/summarize_batch_reports.py        # сводка по batch-репортам
```

### Codex Automations conveyor

> Контур для RTX training chunks и Mac intake через Codex app Automations и GitHub manifests.
> Подробности: `automation/README.md`

```bash
# RTX (Windows / Codex App Automation in background worktree)
C:/Users/PC/GimbalProject/tracker_env/Scripts/python.exe python_scripts/training_conveyor.py init --state-dir automation/state
C:/Users/PC/GimbalProject/tracker_env/Scripts/python.exe python_scripts/training_conveyor.py scan --dataset-root "<dataset_root>" --state-dir automation/state
C:/Users/PC/GimbalProject/tracker_env/Scripts/python.exe python_scripts/training_conveyor.py next-chunk --state-dir automation/state --base-checkpoint "<absolute_checkpoint>" --chunk-epochs 12 --write-plan automation/state/next_training_chunk.json --claim
C:/Users/PC/GimbalProject/tracker_env/Scripts/python.exe python_scripts/publish_training_artifact.py --help

# Mac intake
/Users/bround/Documents/Projects/GimbalProject/tracker_env/bin/python python_scripts/fetch_training_artifact.py --help
```

---

## Orchestration

### Проверка состояния оркестратора

```bash
source tracker_env/bin/activate
PYTHONPATH=src python orchestrator/scripts/check_orchestration_state.py
```

Выводит: `orchestrator_state_check=OK|FAIL`, `active_tasks=N`, `completed_tasks=N`.

### Директории

| Путь | Назначение |
|------|------------|
| `orchestrator/state/active_plan.md` | Текущий план и активные задачи |
| `orchestrator/state/open_tasks.md` | Backlog задач |
| `orchestrator/state/completed_tasks.md` | Реестр выполненных задач |
| `orchestrator/tasks/` | Детальные описания задач |
| `orchestrator/reports/` | Отчёты о выполнении |

---

## Тесты

```bash
source tracker_env/bin/activate
PYTHONPATH=src python -m unittest -q tests.test_target_manager_lock_policy tests.test_package_import tests.test_select_active_policy
```

---

## Пресеты (configs/)

| Файл | Назначение |
|------|------------|
| `configs/default.yaml` | Базовый дневной пресет |
| `configs/night.yaml` | Ночной пресет (пониженный conf, Night detector) |
| `configs/small_target.yaml` | Малые цели (ROI assist) |
| `configs/antiuav_thermal.yaml` | Thermal / Anti-UAV (IR) |
| `configs/rpi_hailo.yaml` | RPi 5 + Hailo backend |

---

## Baseline model

Стабильный локальный production path модели:

```
models/baseline.pt
```

Все operator-пресеты (`default`, `night`, `small_target`, `antiuav_thermal`) ссылаются на этот файл.

### Как обновить baseline

1. Принять candidate-модель (после прохождения quality gate).
2. Установить через canonical install flow:
   ```bash
   source tracker_env/bin/activate
   PYTHONPATH=src python python_scripts/install_baseline.py \
       --source <path_to_accepted.pt> \
       --notes "Accepted YYYYMMDD: <описание>" \
       --gate-report runs/evaluations/quality_gate/<tag>_quality_gate_<preset>.json
   ```
   Скрипт копирует `.pt` в `models/baseline.pt` и пишет `models/baseline_manifest.json`
   с sha256, датой, ссылкой на gate report.
3. Закоммитить `models/baseline_manifest.json` в репозиторий (только манифест, не `.pt`).

> `models/baseline.pt` — бинарный файл, не хранится в git.
> При первом развёртывании запустите `install_baseline.py --source <pt>`.
> Governance contract: [models/README.md](models/README.md)

---

## Non-canonical скрипты (legacy)

Ранние прототипы и вспомогательные инструменты перемещены в `legacy/`:

| Файл | Описание |
|------|----------|
| `legacy/benchmark.py` | M1 matmul + YOLO performance benchmark |
| `legacy/real_tracker.py` | Ранний прототип camera tracker |
| `legacy/train_script.py` | Ранний training harness |

Эти файлы не входят в operator workflow. Подробности: [legacy/README.md](legacy/README.md)

Вспомогательные `python_scripts/` (не canonical, но актуальные):

- `python_scripts/run_backend_parity.py` — сравнение backend-выходов
- `python_scripts/run_dataset_batch.py` — пакетная обработка датасетов

---

## Bootstrap (первый запуск / новая машина)

```bash
# 1. Создать venv
python3.11 -m venv tracker_env

# 2. Установить зависимости
source tracker_env/bin/activate
pip install -r requirements.txt

# 3. Установить baseline-модель через canonical flow
PYTHONPATH=src python python_scripts/install_baseline.py \
    --source <path_to_accepted.pt> \
    --notes "Accepted YYYYMMDD: initial local baseline"

# 4. Smoke-проверка
PYTHONPATH=src python -c "from uav_tracker.pipeline import TrackerPipeline; print('OK')"
PYTHONPATH=src python main_tracker.py --help
```

Зависимости: `requirements.txt` в корне репозитория.
Полный список: `torch`, `ultralytics`, `opencv-python`, `PySide6`, `numpy`, `PyYAML`, `lapx`, `scipy`, `requests`.
Training-specific зависимости (`wandb` и др.) — не обязательны для desktop runtime.
