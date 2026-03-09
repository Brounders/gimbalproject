# RUNBOOK: Канонический Контур Проекта

## 1) Операторский запуск (Mac)
- GUI:
```bash
cd /Users/bround/Documents/Projects/GimbalProject
./tracker_env/bin/python tracker_gui.py
```
- CLI (быстрый контроль):
```bash
./tracker_env/bin/python main_tracker.py --preset night_ir_lock_v2 --mode operator --source test_videos/night_ground_large_drones.mp4 --device mps --max-frames 240 --no-display
```

## 2) Обучение на RTX (ноутбук)
- Запуск fine-tune (в RTX-сессии):
```bash
cd C:\Users\PC\GimbalProject
tracker_env\Scripts\python.exe python_scripts\train_yolo_from_yaml.py --help
```
- Результат, который нужен Mac:
  - `best.pt`
  - `last.pt`
  - `results.csv`

## 3) Экспорт артефакта с RTX
- Положить модель в:
  - `models/checkpoints/rtx_drone_first_6h_v2_best.pt`

## 4) Качество на Mac (benchmark + quality-gate)
```bash
cd /Users/bround/Documents/Projects/GimbalProject
./tracker_env/bin/python python_scripts/run_offline_benchmark.py --source-list configs/regression_pack.csv --preset night_rtx_candidate --mode operator --device mps --max-frames 240 --tag release_

./tracker_env/bin/python python_scripts/run_quality_gate.py --pack-file configs/regression_pack.csv --preset night_rtx_candidate --mode operator --device mps --max-frames 240 --tag release_
```

## 5) A/B для операторского профиля
```bash
./tracker_env/bin/python python_scripts/run_profile_ab.py --base-preset night_ir_lock_v2 --profiles operator_standard,fast --mode operator --device mps --max-frames 240
```

## 6) Единый оркестратор (рекомендуется)
```bash
./tracker_env/bin/python python_scripts/run_stable_cycle.py --run-ab --candidate-preset night_rtx_candidate --device mps --mode operator --max-frames 240
```

## 7) Правило релиза
- Релиз профиля только если:
  - `quality_gate_passed = true`
  - средний `score` из gate >= 45
- Иначе: донастройка порогов и повтор цикла.
