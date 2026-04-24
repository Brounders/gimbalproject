# Model Decisions

> Formal decision log for model candidates and training strategies (mirrors automation/state/decision_log.json)

## Decision 1 — drone-bird-yolo curriculum: reject_and_reset_training_strategy

| Field | Value |
|-------|-------|
| Decision ID | `decision_drone-bird-yolo_20260313` |
| Date | 2026-03-13 |
| Decided by | Claude Mac (AP-026) |
| Dataset | `drone-bird-yolo` |
| Artifacts evaluated | chunk6 (ep73-84), chunk10 (ep121-132) |
| Runtime state | AP-025 (`night_confirm=5`, `night_track_dist=65`, `lock_lost_grace=1`) |
| **Decision** | **`reject_and_reset_training_strategy`** |

**Reason:**
All candidates fail the night gate with massive regression vs de-facto baseline.
Trend worsens with more epochs. No candidate is promotable.
Root cause: `drone-bird-yolo` dataset likely IR-dominant, causing visible-light night regression.

**Evidence:**
| Metric | Baseline | Chunk6 | Chunk10 |
|--------|----------|--------|---------|
| Night large_drones false_lock | 0.510 | 0.830 | 0.951 |
| Night large_drones id_chg/min | 12.23 | 48.93 | 55.05 |
| Night indicator false_lock | 0.096 | 0.973 | 0.902 |
| Night gate | PASS | FAIL | FAIL |

Gate reports: `runs/evaluations/quality_gate/ap026_*`

---

## Decision 2 — drone_bird_probe_fast: install_as_baseline

| Field | Value |
|-------|-------|
| Decision ID | `baseline_install_drone_bird_probe_fast_20260313` |
| Date | 2026-03-13 |
| Decided by | Claude Mac (AP-026 autonomous session) |
| Model | `drone_bird_probe_fast` |
| Source | `runs/detect/runs/drone_bird_probe_fast/weights/best.pt` |
| SHA256 | `bedc77fe7b899de1ac68ae654f49fcee6301a9d3f8a61e9eff5c1e8d66641d44` |
| Runtime state | AP-025 (`night_confirm=5`, `night_track_dist=65`, `lock_lost_grace=1`) |
| **Decision** | **`install_as_baseline`** |

**Reason:**
First formal baseline installation. Night gate PASS (AP-025). IR gate measured as reference
(known failing — open issue). SHA256 recorded for traceability.

**Gate results:**
- Night: `runs/evaluations/quality_gate/quality_gate_night.json` — PASS
- IR: `runs/evaluations/quality_gate/baseline_formalization_irquality_gate_antiuav_thermal.json` — reference

**Manifest:** `models/baseline_manifest.json`

---

## Decision 3 — epoch142 (rtx_drone_stability_12h_v1): hold_and_tune

| Field | Value |
|-------|-------|
| Date | 2026-03-11 |
| Decided by | Claude Mac (AP-011) |
| **Decision** | **`hold_and_tune`** |

**Reason:**
Persistent false-lock and ID-churn regressions on night/noise clips after retune cycle.
Short threshold sweep could not reliably recover operator-critical stability.

---

## Next Decision Required

Before any new training run: audit `drone-bird-yolo` dataset composition.
Only after that can a `reject_and_reset_training_strategy` action plan be approved.

## Related

- [training_strategy.md](../concepts/training_strategy.md) — why curriculum was rejected
- [models.md](../entities/models.md) — model statuses and gate results
- [quality_gates.md](../concepts/quality_gates.md) — gate contract
