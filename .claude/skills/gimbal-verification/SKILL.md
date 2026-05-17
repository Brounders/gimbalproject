---
name: gimbal-verification
description: Use before reporting GimbalProject work complete. Runs task-specific tests, compileall, PySide sanity, visual checks when relevant, and prevents unverified success claims.
---

# Gimbal Verification

## Rule

Do not claim work is complete until validation ran or you clearly state why it could not run.

## Baseline Validation

Run:

```bash
python3 -m compileall -q python_scripts src app orchestrator tests
```

Then run task-specific tests:

- DTS data: `pytest tests/test_training_desk_data.py -q`
- DTS quality: `pytest tests/test_training_desk_quality.py -q`
- staging pack: `pytest tests/test_stage_operator_training_pack.py -q`
- video mapping: `pytest tests/test_video_stage_mapping.py -q`
- export: `pytest tests/test_operator_annotation_export.py -q`

Use only tests relevant to changed files.

## UI Validation

For PySide6 UI:

- run offscreen import/instantiation sanity;
- produce screenshot or explain why not possible;
- report visual gaps honestly.

## Final Report

Include:

- exact commands run;
- pass/fail result;
- failures with short cause;
- unrun checks and why.
