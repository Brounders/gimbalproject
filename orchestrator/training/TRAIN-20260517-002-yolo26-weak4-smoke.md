# TRAIN-20260517-002 — YOLO26 Weak4 Smoke Retry

Date: 2026-05-17
Status: Ready
Owner: RTX

## Purpose

Artifact-generation proof for the weak4 targeted detector pack.  This is not a
quality run and must not be counted as model evidence unless the artifact
contract passes.

## Dataset

Use:

```bash
/Users/bround/Documents/Projects/GimbalProject/runs/training_packs/weak4_103h_20260517/data.yaml
```

Pack summary:

- total samples: 783;
- train: 627;
- val: 156;
- class 0: `drone`;
- class 1: `non_drone_flyer`;
- hard negatives: airplane and bird GT samples.

## Launch Contract

Use a tiny, strict smoke:

```bash
cd /Users/bround/Documents/Projects/GimbalProject
mkdir -p runs/detect/train/yolo26_weak4_smoke_20260517
timeout 60m ./tracker_env/bin/python python_scripts/train_yolo_from_yaml.py \
  --data runs/training_packs/weak4_103h_20260517/data.yaml \
  --model models/yolo11n.pt \
  --project runs/detect/train \
  --name yolo26_weak4_smoke_20260517 \
  --device 0 \
  --imgsz 736 \
  --batch 8 \
  --workers 0 \
  --epochs 1 \
  --patience 1 \
  --cache none \
  --save-period 1 \
  --val \
  --plots \
  2>&1 | tee runs/detect/train/yolo26_weak4_smoke_20260517/train.log
```

If `timeout` is not available on the target shell, use the platform equivalent
but keep the 60 minute external cap.

## Required Artifact Check

After the command exits, report:

```bash
RUN_DIR=runs/detect/train/yolo26_weak4_smoke_20260517
test -f "$RUN_DIR/results.csv" && echo "results.csv=OK" || echo "results.csv=MISSING"
test -f "$RUN_DIR/weights/last.pt" && echo "last.pt=OK" || echo "last.pt=MISSING"
test -f "$RUN_DIR/train.log" && echo "train.log=OK" || echo "train.log=MISSING"
tail -n 40 "$RUN_DIR/train.log"
```

## Required RTX Status Fields

Return these fields exactly:

- `status`
- `run_name`
- `run_dir`
- `checkpoint_used`
- `train_proc_count`
- `gpu_temp`
- `cpu_temp`
- `epochs_done_total`
- `epoch_current`
- `epoch_target`
- `epoch_progress_pct`
- `resume_mode`
- `exit_reason`
- `best_pt`
- `last_pt`
- `log_path`
- `download_url`
- `tail_log_20`

## Acceptance

PASS only if:

- command exits normally or via controlled timeout after writing checkpoint;
- `results.csv` exists;
- `weights/last.pt` exists;
- `train.log` exists and contains the training start plus final exit context.

FAIL if:

- only `args.yaml` exists;
- no checkpoint is written;
- the log is missing;
- the run hangs without epoch/progress evidence.
