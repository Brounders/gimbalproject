# TASK: TASK-20260311-030-candidate-model-eval-override

Task ID: TASK-20260311-030
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Убрать ручной и грязный путь оценки candidate-модели через временные preset-файлы и дать benchmark/gate скриптам явный способ подставлять отдельный `model_path`.

## Scope
- In scope:
  - добавить безопасный override `model_path` для evaluation scripts (`benchmark`, `quality_gate`, при необходимости `quick_kpi_smoke`);
  - не менять canonical operator presets ради разового candidate-eval;
  - сохранить обратную совместимость текущих команд.
- Out of scope:
  - изменения основного GUI operator flow;
  - переписывание profile system целиком.

## Files
- `python_scripts/run_offline_benchmark.py`
- `python_scripts/run_quality_gate.py`
- `python_scripts/run_quick_kpi_smoke.py` только если нужен для консистентности
- `src/uav_tracker/profile_io.py` только если нужен минимальный helper

## Validation
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `source tracker_env/bin/activate && python python_scripts/run_offline_benchmark.py --help`
- `source tracker_env/bin/activate && python python_scripts/run_quality_gate.py --help`
- smoke-проверка, что candidate model path можно подставить без редактирования `configs/night.yaml`

## Acceptance Criteria
- [ ] Для candidate evaluation больше не нужен временный committed preset.
- [ ] Скрипты benchmark/gate принимают явный override модели или эквивалентный чистый механизм.
- [ ] Существующие вызовы без нового override продолжают работать как раньше.
