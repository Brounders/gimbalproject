# TASK: TASK-20260501-090 — MG-001 unified model intake

Task ID: TASK-20260501-090
Alias: MG-001
Status: Open
Owner: Claude Mac
Plan: AP-PHASE2-MODEL-DATASET-INTAKE

## Goal

Create a single model-intake wrapper so a new model can be evaluated through the formal promotion gates without manual command assembly.

## Scope

- Add `python_scripts/run_intake.py`.
- Accept CLI:
  - `python_scripts/run_intake.py model.pt`
  - `python_scripts/run_intake.py model.pt --preset night|day|ir`
- Read thresholds, baseline references, required contexts, and known gaps from `configs/promotion_contract.yaml`.
- Reuse existing quality-gate logic by invoking or wrapping `python_scripts/run_quality_gate.py`.
- Generate `orchestrator/reports/REPORT-INTAKE-{model}.md`.
- Produce one of three decisions:
  - `ACCEPTED`
  - `HOLD`
  - `REJECTED`

## Decision Rules

- `ACCEPTED`: all applicable required gates pass and no blocking known gap applies.
- `HOLD`: model is useful only for a restricted context or blocked by an acknowledged gap.
- `REJECTED`: one or more required gates fail without an acknowledged non-production exception.

## Non-Scope

- Do not change model baseline.
- Do not run training.
- Do not change runtime thresholds.
- Do not change `run_quality_gate.py` behavior unless a tiny reusable helper extraction is strictly necessary.
- Do not touch UI, Hailo, ByteTrack, or thermal YOLO work.

## Validation

- `python_scripts/run_intake.py --help`
- A dry/smoke invocation that does not require long benchmark execution, if implemented.
- `python -m compileall -q python_scripts src app orchestrator tests`
- `python -m pytest -q`
- `python orchestrator/scripts/check_orchestration_state.py`

## Report

Write `orchestrator/reports/REPORT-MG-001.md` with:

- What was implemented
- How `promotion_contract.yaml` is interpreted
- Example commands
- Validation results
- Risks / remaining manual steps
