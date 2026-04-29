# REPORT-20260429: YOLOv11n Benchmark vs Baseline

**Date:** 2026-04-29  
**Status:** ACCEPTED — REJECT for production; requires fine-tune  
**Model:** `models/yolo11n.pt` (SHA256: `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`)  
**Baseline:** `models/baseline.pt` (drone_bird_probe_fast)

---

## Gate Results

### Night context (`--max-false-lock-rate 0.55 --max-night-id-changes-per-min 18.0`)

| Model | false_lock | id_chg/min | fps | PASS |
|-------|-----------|-----------|-----|------|
| baseline.pt | 0.510 | 12.23 | 28.0 | ✅ |
| yolo11n.pt | **0.767** | **36.70** | 21.7 | ❌ |

### Day context (defaults)

| Model | false_lock | id_chg/min | fps | PASS |
|-------|-----------|-----------|-----|------|
| yolo11n.pt | 0.917 | 0.00 | **53.3** | ✅ (structural) |

### IR context (`--max-false-lock-rate 0.70`)

| Clip | false_lock | id_chg/min | PASS |
|------|-----------|-----------|------|
| Demo_IR_DRONE_146 | 0.725 | 46.01 | ❌ |
| IR_DRONE_001 | 0.807 | 17.94 | ❌ |

---

## Analysis

YOLOv11n (pretrained, no fine-tune) is **significantly worse** than baseline on all detection-sensitive contexts:

- **Night:** false_lock ×1.5 worse (0.767 vs 0.510); id_chg/min ×3 worse (36.70 vs 12.23)
- **IR:** false_lock higher across both clips
- **Day FPS:** 53.3 vs ~25 — 2× faster, but this context is not the bottleneck

The pretrained yolo11n has no drone-specific training. Without fine-tuning on drone-bird data, class confusion causes high false_lock and the target tracker loses ID rapidly.

---

## Decision

**REJECT yolo11n for production.** Baseline (drone_bird_probe_fast) remains the active model.

**Required before yolo11n can replace baseline:**
1. Fine-tune yolo11n on drone-bird dataset (requires OQ-001 resolution — dataset composition)
2. Gate PASS on night clip: false_lock ≤ 0.55, id_chg/min ≤ 18.0
3. SHA256 registered in baseline_manifest.json

---

## Day FPS Note

yolo11n achieves 53.3 FPS on day clip (vs ~25 for baseline) — consistent with the −42% inference time claim. This speed advantage will be realised after fine-tuning.

---

## Next Steps

1. **OQ-001** (dataset composition) — prerequisite for fine-tuning
2. After OQ-001: fine-tune yolo11n on balanced drone+bird dataset
3. Re-run this benchmark; promote if night gate PASS
