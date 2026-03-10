# TRAINING TASK: TRAIN-20260311-001-rtx-curriculum-step1

## Goal
Запустить на RTX очередной этап curriculum-обучения (step1) от текущего `rtx_latest_best.pt`, чтобы не перезапускать один и тот же run вручную и получить воспроизводимый артефакт для intake на Mac.

## Dataset
- Curriculum plan: `configs/training_curriculum.yaml`
- Активный шаг: `mendeley_ir_mix` (`datasets/drone_bird_mendeley_ir_mix_v1/dataset.yaml`)

## Inputs
- Base model: `models/checkpoints/rtx_latest_best.pt`
- Script: `python_scripts/run_training_curriculum.py`
- Device: `cuda`

## Run Plan
1. Проверить, что на RTX синхронизированы `run_training_curriculum.py` и `training_curriculum.yaml`.
2. Запустить:
   - `tracker_env\Scripts\python.exe python_scripts\run_training_curriculum.py --plan configs/training_curriculum.yaml --max-steps 1`
3. Дождаться штатного завершения шага.
4. Упаковать артефакт run и отдать `download_url` для intake на Mac.

## Required Artifacts
- `best.pt`
- `last.pt`
- `results.csv`
- `args.yaml`
- `summary/tail log`
- `download_url` (HTTP)

## Validation
- Проверка, что `runs/curriculum_state/rtx_curriculum_v1.json` обновлен:
  - добавлен `completed: ["mendeley_ir_mix"]`
  - `latest_best` указывает на новый checkpoint.
- Проверка отсутствия параллельных train-процессов по завершении.

## Acceptance
- [ ] Шаг curriculum завершен без падения.
- [ ] Артефакты выгружены и доступны по URL.
- [ ] State-файл curriculum обновлен корректно.
