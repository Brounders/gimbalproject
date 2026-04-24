# Training Strategy

> RTX-side model training: pipeline, curriculum approach, what has been tried, current status

## Infrastructure

### Control Plane (automation/state/)

| File | Purpose |
|------|---------|
| `dataset_registry.json` | Datasets available on RTX |
| `training_ledger.json` | Training history, chunk status |
| `artifact_manifest.json` | Published artifacts and GitHub Release URLs |
| `decision_log.json` | Mac-side decisions after quality gate |

### Flow

```
RTX trains → publishes GitHub Release → Mac intake → quality gate → decision
```

This end-to-end flow was first proven working in AP-014.
Binary artifacts stay out of `main` — published via GitHub Releases.

### Scripts (RTX side)

Automation scripts live in `automation/` and handle:
- Curriculum chunk scheduling
- Progress tracking
- Artifact upload

## Current Curriculum: drone-bird-yolo (REJECTED)

**Status**: `reject_and_reset_training_strategy` (AP-026, 2026-03-13)

| Property | Value |
|----------|-------|
| Dataset ID | `drone-bird-yolo` |
| Run name | `curriculum_drone-bird-yolo` |
| Scene profile | `mixed` (likely IR-dominant — see open questions) |
| Epochs completed | 132 of 144 |
| Chunks published | chunk1_v2 through chunk10 |
| Last evaluated chunks | chunk6 (ep73-84), chunk10 (ep121-132) |

### Why Rejected

All candidates fail the night gate with massive regression vs de-facto baseline:

| Metric | De-facto Baseline | Chunk6 | Chunk10 |
|--------|------------------|--------|---------|
| Night large_drones false_lock | **0.510** | 0.830 | 0.951 |
| Night large_drones id_chg/min | **12.23** | 48.93 | 55.05 |
| Night indicator false_lock | **0.096** | 0.973 | 0.902 |
| Night gate | **PASS** | FAIL | FAIL |

**The trend worsens with more epochs.** This is not a tuning range issue — the model is
diverging from night-usable representations as the curriculum progresses.

Suspected root cause: `drone-bird-yolo` dataset contains predominantly IR/thermal imagery.
Training on it causes the model to optimize for IR patterns at the expense of
visible-light night performance.

## De-facto Baseline (current best model)

`drone_bird_probe_fast` — see [models.md](../entities/models.md).
This model predates the curriculum and passes the AP-025 night gate.

## Recommended Next Steps (not yet approved, from AP-026)

1. **Audit dataset composition**: count visible-light night vs IR clips in `drone-bird-yolo`.
   Hypothesis: the curriculum is IR-dominant, which explains the visible-light night regression.

2. **Baseline formalization**: formally install `drone_bird_probe_fast` as `models/baseline.pt`.
   *(Partially done in AP-026 autonomous session — verify manifest.)*

3. **Training strategy reset options**:
   - Option A: Re-train from scratch with a dataset including both night visible-light AND IR clips
   - Option B: Fine-tune `drone_bird_probe_fast` specifically on problematic cases
   - Option C: Investigate whether `drone-bird-yolo` contains any visible-light night data

> ❓ OPEN: Dataset composition audit not yet done. No new training approved until this is analyzed.

## Related

- [models.md](../entities/models.md) — model statuses
- [quality_gates.md](quality_gates.md) — gate contract
- [model_decisions.md](../decisions/model_decisions.md) — formal decision log
- [open_questions.md](../synthesis/open_questions.md)
