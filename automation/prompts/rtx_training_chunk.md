Replace `{{PYTHON_CMD}}`, `{{DATASET_ROOT}}`, `{{BASE_CHECKPOINT}}`, and `{{CHUNK_EPOCHS}}` manually before creating the automation.

For RTX Git-based automations, use absolute paths. Example:
- `{{PYTHON_CMD}}` -> `C:/Users/PC/GimbalProject/tracker_env/Scripts/python.exe`
- `{{DATASET_ROOT}}` -> `C:/Users/PC/Desktop/Обучение`
- `{{BASE_CHECKPOINT}}` -> `C:/Users/PC/GimbalProject/runs/detect/runs/rtx_drone_stability_12h_v1/weights/best.pt`

Use `$gimbal-codex-automation-conveyor`.

Goal: execute exactly one RTX training chunk from the Codex app Automation.

Steps:
1. `git pull --ff-only origin main`
2. `{{PYTHON_CMD}} python_scripts/training_conveyor.py scan --dataset-root "{{DATASET_ROOT}}" --state-dir automation/state`
3. `{{PYTHON_CMD}} python_scripts/training_conveyor.py next-chunk --state-dir automation/state --base-checkpoint "{{BASE_CHECKPOINT}}" --chunk-epochs {{CHUNK_EPOCHS}} --write-plan automation/state/next_training_chunk.json --claim`
4. If no dataset is eligible, stop cleanly and summarize why.
5. If a plan exists, run one training chunk only, using the suggested dataset yaml, checkpoint, run name, and target total epochs from `automation/state/next_training_chunk.json`.
6. Export one zip artifact for the run.
7. Publish it with `{{PYTHON_CMD}} python_scripts/publish_training_artifact.py ...`.
8. Record the run with `{{PYTHON_CMD}} python_scripts/training_conveyor.py record-run ...`.
9. Commit and push only state/manifests/logs required by the conveyor.

Constraints:
- Do not train more than one dataset per automation run.
- Do not create ad hoc temporary committed presets.
- Do not commit binary artifacts to `main`.
- If publishing fails, keep the local zip and return a clear failure summary.
