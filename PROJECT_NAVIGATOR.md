# Project Navigator

## Strategic Context
- `PROJECT_COURSE_LOCK.md` -> fixed project mission, priorities, and non-negotiable rules.
- `SESSION_OPERATION_PROTOCOL.md` -> Mac/RTX operating loop and reporting protocol.
- `CURRENT_PHASE_STATUS.md` -> current phase focus and immediate completion criteria.

## Core Runtime (canonical)
- `main_tracker.py` -> CLI entrypoint (`app/main_cli.py`)
- `tracker_gui.py` -> Desktop GUI entrypoint (`app/main_gui.py`)
- `src/uav_tracker/` -> detection, tracking, runtime, evaluation core
- `configs/` -> presets and runtime profiles

## Training and Dataset Tooling
- `python_scripts/train_yolo_from_yaml.py` -> generic YOLO training runner
- `python_scripts/train_drone_bird.py` -> dataset prep + train for Drone/Bird workflows
- `python_scripts/*dataset*`, `*convert*`, `*sanitize*`, `*normalize*` -> dataset preparation helpers

## Evaluation and Quality Gate
- `python_scripts/run_offline_benchmark.py`
- `python_scripts/run_quality_gate.py`
- `python_scripts/run_backend_parity.py`
- `python_scripts/run_scenario_sweep.py`

## Legacy Area
- `legacy/prototypes/` -> historical prototype scripts (non-production)
- Root wrappers (`HYBRID_NIGHT_TRACKER.py`, `real_tracker.py`, `tracker_final.py`, `train_script.py`, `benchmark.py`) are compatibility shims only.

## Data/Artifacts (not source code)
- `datasets/` -> source datasets and prepared datasets
- `runs/` -> model runs, logs, checkpoints, reports
- `tracker_env/` -> Python virtual environment
