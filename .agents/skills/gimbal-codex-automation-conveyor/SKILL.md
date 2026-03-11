---
name: gimbal-codex-automation-conveyor
description: Use when running GimbalProject through Codex app Automations for repeated training and intake work: dataset registry, training ledger, artifact manifest, GitHub release publishing, and Mac-side artifact intake. Trigger for automation, ledger, manifest, GitHub artifact, RTX training chunk, or intake conveyor tasks.
---

# Gimbal Codex Automation Conveyor

Use this skill for stable Codex app Automations in GimbalProject.

## Use when
- You are creating or updating a recurring Codex Automation in the app.
- You need deterministic `scan -> choose -> train chunk -> publish artifact -> intake` behavior.
- You need to avoid retraining the same dataset chunk twice.
- You need GitHub-delivered artifacts instead of temporary local HTTP serving.

## Do not use when
- The task is normal one-off training or manual benchmark work.
- The task is a runtime/UI change unrelated to the conveyor.

## Workflow
1. Read `automation/README.md` for the current conveyor contract.
2. Use `python_scripts/training_conveyor.py` to initialize state, scan datasets, select the next chunk, record run progress, and record final decisions.
3. Use `python_scripts/publish_training_artifact.py` to upload a completed zip to GitHub Releases and append to `automation/state/artifact_manifest.json`.
4. Use `python_scripts/fetch_training_artifact.py` on Mac to pull the latest published artifact into `imports/`.
5. Keep binary artifacts out of `main`; commit only manifests, ledger, and decisions.

## Required files
- `automation/state/dataset_registry.json`
- `automation/state/training_ledger.json`
- `automation/state/artifact_manifest.json`
- `automation/state/decision_log.json`

## References
- `automation/README.md`
- `automation/prompts/rtx_training_chunk.md`
- `automation/prompts/mac_intake_gate.md`

## Rules
- Prefer one deterministic script over ad hoc shell logic.
- Never commit `.pt` or `.zip` artifacts into `main`.
- Treat `training_ledger.json` as the source of truth for per-dataset progress.
- Treat `artifact_manifest.json` as the source of truth for GitHub-published deliverables.
