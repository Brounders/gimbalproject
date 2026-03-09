#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/bround/Documents/Projects/GimbalProject"
VENV_PY="$ROOT/tracker_env/bin/python"
DATASET_RGBT="/Users/bround/Desktop/Anti-UAV-RGBT"
PRIMARY_DATASET="$ROOT/datasets/drone_bird_yolo"
NIGHT_DATASET="$ROOT/datasets/antiuav_rgbt_ir_yolo"
MIX_DATASET="$ROOT/datasets/drone_bird_night_mix"
RUN_NAME="drone_bird_night_6h"
CACHE_MODE="${CACHE_MODE:-none}"
LOG_DIR="$ROOT/runs/autosession_logs"
mkdir -p "$LOG_DIR"

START_TS="$(date +%Y%m%d_%H%M%S)"
SESSION_LOG="$LOG_DIR/${START_TS}_session.log"

echo "[INFO] start: $(date -Iseconds)" | tee -a "$SESSION_LOG"
echo "[INFO] root:  $ROOT" | tee -a "$SESSION_LOG"
echo "[INFO] log:   $SESSION_LOG" | tee -a "$SESSION_LOG"
echo "[INFO] cache: $CACHE_MODE" | tee -a "$SESSION_LOG"

if [[ ! -x "$VENV_PY" ]]; then
  echo "[ERROR] Python not found: $VENV_PY" | tee -a "$SESSION_LOG"
  exit 2
fi
if [[ ! -d "$DATASET_RGBT" ]]; then
  echo "[ERROR] Dataset not found: $DATASET_RGBT" | tee -a "$SESSION_LOG"
  exit 2
fi
if [[ ! -d "$PRIMARY_DATASET" ]]; then
  echo "[ERROR] Primary dataset not found: $PRIMARY_DATASET" | tee -a "$SESSION_LOG"
  exit 2
fi

echo "[STEP] compile scripts" | tee -a "$SESSION_LOG"
"$VENV_PY" -m py_compile \
  "$ROOT/python_scripts/convert_antiuav_rgbt_to_yolo.py" \
  "$ROOT/python_scripts/normalize_yolo_labels_to_boxes.py" \
  "$ROOT/python_scripts/build_mixed_dataset.py" \
  "$ROOT/python_scripts/train_yolo_from_yaml.py" | tee -a "$SESSION_LOG"

echo "[STEP] convert Anti-UAV-RGBT -> YOLO (infrared)" | tee -a "$SESSION_LOG"
"$VENV_PY" "$ROOT/python_scripts/convert_antiuav_rgbt_to_yolo.py" \
  --dataset-root "$DATASET_RGBT" \
  --out-root "$NIGHT_DATASET" \
  --splits "train,val,test" \
  --modalities "infrared" \
  --sample-step 24 \
  --max-frames-per-seq 24 \
  --min-box-size 4 \
  --jpg-quality 88 | tee -a "$SESSION_LOG"

echo "[STEP] build mixed dataset lists" | tee -a "$SESSION_LOG"
"$VENV_PY" "$ROOT/python_scripts/build_mixed_dataset.py" \
  --primary-root "$PRIMARY_DATASET" \
  --night-root "$NIGHT_DATASET" \
  --out-root "$MIX_DATASET" \
  --night-multiplier 2.5 \
  --shuffle | tee -a "$SESSION_LOG"

echo "[STEP] normalize primary labels to detect-only format" | tee -a "$SESSION_LOG"
"$VENV_PY" -u "$ROOT/python_scripts/normalize_yolo_labels_to_boxes.py" \
  --dataset-root "$PRIMARY_DATASET" \
  --fix | tee -a "$SESSION_LOG"

BASE_MODEL="$ROOT/models/yolo11n.pt"
if [[ -f "$ROOT/runs/detect/runs/drone_bird_v2/weights/best.pt" ]]; then
  BASE_MODEL="$ROOT/runs/detect/runs/drone_bird_v2/weights/best.pt"
fi

TRAIN_MODEL="$BASE_MODEL"
RESUME_FLAG=""
if [[ -f "$ROOT/runs/detect/runs/$RUN_NAME/weights/last.pt" ]]; then
  TRAIN_MODEL="$ROOT/runs/detect/runs/$RUN_NAME/weights/last.pt"
  RESUME_FLAG="--resume"
fi

echo "[STEP] train 6h | model=$TRAIN_MODEL resume=${RESUME_FLAG:-false}" | tee -a "$SESSION_LOG"
"$VENV_PY" "$ROOT/python_scripts/train_yolo_from_yaml.py" \
  --data "$MIX_DATASET/dataset.yaml" \
  --model "$TRAIN_MODEL" \
  --project "$ROOT/runs/detect/runs" \
  --name "$RUN_NAME" \
  --device mps \
  --imgsz 736 \
  --batch 8 \
  --workers 2 \
  --epochs 2000 \
  --time-hours 6 \
  --patience 120 \
  --cache "$CACHE_MODE" \
  --lr0 0.0022 \
  --lrf 0.01 \
  $RESUME_FLAG | tee -a "$SESSION_LOG"

echo "[INFO] finished: $(date -Iseconds)" | tee -a "$SESSION_LOG"
echo "[INFO] run dir: $ROOT/runs/detect/runs/$RUN_NAME" | tee -a "$SESSION_LOG"
