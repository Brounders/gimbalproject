---
name: gimbal-dts-data-flow
description: Use for GimbalProject DTS, operator annotations, quality/duplicate calculations, accepted/staged review state, YOLO export, and training pack staging. Prevents fixtures, fake metrics, and accidental training launch.
---

# Gimbal DTS Data Flow

## Current Facts

- DTS UI: `app/ui/training_desk.py`
- DTS data: `app/training_desk_data.py`
- input logs: `runs/operator_annotations/*.jsonl`
- review state: `runs/operator_annotations/dts_review_state.json`
- statuses: `new`, `accepted`, `rejected`, `staged`
- export script: `python_scripts/export_operator_annotations_to_yolo.py`

## Rules

- Use real JSONL records.
- Do not replace DTS data with fixtures.
- Do not display fake quality values.
- Do not display fake duplicate findings.
- Do not export `new` or `rejected` records.
- Export/staging includes only `accepted` and `staged`.
- Do not start training automatically.

## Quality Metrics

Prefer deterministic helpers:

- structural validity;
- source availability;
- frame readability;
- bbox bounds;
- bbox area ratio;
- crop size;
- sharpness via cv2 Laplacian variance;
- exposure/brightness stats.

Return `OK`, `WARN`, `FAIL`, or `N/A`.

## Duplicate Rules

Detect:

- exact duplicate: same source, frame, bbox;
- near duplicate: same source, nearby frame, high IoU;
- same-frame overlap: same source, same frame, high IoU.

Never auto-delete or auto-reject duplicates.

## Export/Staging

If connecting export/staging:

- preserve audit manifest;
- infer frame size from video when possible;
- fail clearly when frame size/source is unavailable;
- write deterministic pack paths under `runs/`;
- keep generated artifacts out of git.
