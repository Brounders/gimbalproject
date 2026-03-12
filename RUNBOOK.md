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

Exit code: `0` = PASS, `1` = FAIL, `2` = config error.

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
| **3. Quality gate** | `run_quality_gate.py` | Deterministic pack, exit code | Exit 0 |
| **4. Decision** | ручное сравнение | Сравнить с `OPERATOR_BASELINE.md` | Нет регресса по ключевым KPI |

```bash
source tracker_env/bin/activate

# Шаг 1: Quick smoke (ночной пресет, 180 кадров)
PYTHONPATH=src python python_scripts/run_quick_kpi_smoke.py \
    --sources test_videos/night_ground_large_drones.mp4 \
    --preset night --max-frames 180

# Шаг 2: Offline benchmark (ночной сценарий)
PYTHONPATH=src python python_scripts/run_offline_benchmark.py \
    --source-list configs/regression_pack_night.csv --preset night

# Шаг 3: Quality gate (полный pack)
PYTHONPATH=src python python_scripts/run_quality_gate.py

# Шаг 4: Сравнить результат с OPERATOR_BASELINE.md
```

> Для candidate-модели добавить `--model <path>` в шаги 1-3.
> Threshold'ы baseline: см. [OPERATOR_BASELINE.md](OPERATOR_BASELINE.md).

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
2. Скопировать принятый `.pt` в стабильный path:
   ```bash
   cp <path_to_accepted_candidate.pt> models/baseline.pt
   ```
3. Закоммитить обновление (или задокументировать hash) в orchestrator-отчёт.

> `models/baseline.pt` — не создаётся автоматически при клонировании репозитория.
> При первом развёртывании скопируйте актуальную принятую модель вручную.

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

# 3. Поместить baseline-модель
cp <принятый_кандидат.pt> models/baseline.pt   # см. секцию "Baseline model"

# 4. Smoke-проверка
PYTHONPATH=src python -c "from uav_tracker.pipeline import TrackerPipeline; print('OK')"
PYTHONPATH=src python main_tracker.py --help
```

Зависимости: `requirements.txt` в корне репозитория.
Полный список: `torch`, `ultralytics`, `opencv-python`, `PySide6`, `numpy`, `PyYAML`, `lapx`, `scipy`, `requests`.
Training-specific зависимости (`wandb` и др.) — не обязательны для desktop runtime.
