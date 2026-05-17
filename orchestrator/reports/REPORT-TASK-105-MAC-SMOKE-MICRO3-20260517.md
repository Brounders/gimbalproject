# TASK-20260517-105 Mac Smoke Triage And Micro3 Gate

Date: 2026-05-17
Owner: Codex Mac

## Correction

No RTX run was performed.  The stopped YOLO26 smoke was a Mac-local attempt and
must not be described as RTX evidence.

The active state was corrected:

- no active RTX task;
- `TRAIN-20260517-002` is only a draft RTX dispatch contract;
- Mac-local triage is tracked as `TASK-20260517-105`.

## Artifact Triage

The first Mac tiny smoke did complete, but Ultralytics wrote artifacts under a
nested path:

- actual: `runs/detect/runs/detect/train/yolo26_weak4_mac_tiny_smoke_20260517`
- expected: `runs/detect/train/yolo26_weak4_mac_tiny_smoke_20260517`

Cause: `python_scripts/train_yolo_from_yaml.py` passed a relative `project`
path to Ultralytics.  The wrapper now resolves `--project` to an absolute path
before calling `model.train()`.

Pathfix smoke:

- run: `runs/detect/train/yolo26_weak4_mac_tiny_smoke_pathfix_20260517`
- exit: `0`
- `results.csv`: present
- `weights/best.pt`: present
- `weights/last.pt`: present
- `train.log`: present

## Micro3 Candidate

Run:

- `runs/detect/train/yolo26_weak4_mac_micro3_20260517`
- model: `models/yolo26n.pt`
- data: `runs/training_packs/weak4_103h_20260517/data.yaml`
- epochs: `3`
- device: `mps`
- batch: `4`
- workers: `0`
- exit: `0`

Artifacts:

- `results.csv`: present
- `weights/best.pt`: present
- `weights/last.pt`: present
- `train.log`: present

Ultralytics val after 3 epochs:

- all mAP50: `0.474`
- drone mAP50: `0.515`
- non-drone flyer mAP50: `0.433`

This is useful only as local direction evidence.  It is not production evidence.

## Weak4 Evidence Comparison

Candidate evidence:

- `runs/evaluations/detector_evidence_pack/weak4_micro3_20260517/summary.csv`

| Clip | Baseline best Hit@0.1 | Micro3 best Hit@0.1 | Decision |
|---|---:|---:|---|
| `1_minie3_range_close` | 0.5312 | 1.0000 | strong positive movement |
| `9_dji2_range_medium` | 0.2171 | 0.5855 | strong positive movement |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | 0.3333 | 0.3333 | no gate movement; YOLO improved only to 0.2556 |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | 0.9543 | 0.8514 | regression in best source; YOLO regressed badly |

## Decision

Do not promote Micro3.

What we learned:

- targeted training can break the ceiling on `1_minie3_range_close` and
  `9_dji2_range_medium`;
- `antiuav_rgbt_20190925_200805` still needs either better labels, more frames,
  or thermal-specific treatment;
- the already-strong `antiuav_rgbt_train` clip must be protected as a holdout or
  weighted stability gate to avoid catastrophic forgetting.

## Next Concrete Step

Open `TASK-20260517-106`:

1. Build weak4-v2 training pack with `antiuav_rgbt_train` treated as protected
   gate material, not as normal training pressure.
2. Train a short candidate with lower learning rate and/or frozen backbone.
3. Accept only if it improves `1_minie3_range_close` and `9_dji2_range_medium`
   without dropping `antiuav_rgbt_train` below baseline tolerance.
