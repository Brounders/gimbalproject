# Models

> Registry of all model artifacts: status, gate results, provenance

## Current Baseline

### drone_bird_probe_fast

| Property | Value |
|----------|-------|
| Status | **baseline** (formally installed AP-026) |
| Path | `models/baseline.pt` |
| Source | `runs/detect/runs/drone_bird_probe_fast/weights/best.pt` |
| SHA256 | `bedc77fe7b899de1ac68ae654f49fcee6301a9d3f8a61e9eff5c1e8d66641d44` |
| Runtime state at install | AP-025 (`night_confirm=5`, `night_track_dist=65`, `lock_lost_grace=1`) |
| Manifest | `models/baseline_manifest.json` |

**Gate results (AP-025 runtime):**

| Context | Clip | false_lock | id_chg/min | Result |
|---------|------|-----------|-----------|--------|
| Night | `night_ground_large_drones` | **0.510** | **12.23** | PASS |
| Night | `night_ground_indicator_lights` | **0.121** | **0.00** | PASS |
| IR | `Demo_IR_DRONE_146` | ~0.556 | 0.00 | FAIL (known open issue) |
| Day | `drone_closeup_mixkit_44644_360` | 1.000 | 0.00 | structural (not a discriminator) |

> This model was the de-facto runtime fallback (`drone_bird_probe_fast` via `resolve_model_path()`)
> even before formal installation. `models/baseline.pt` was absent until AP-026.

### Fallback Resolution

If `models/baseline.pt` is absent, the runtime calls `resolve_model_path()` which falls back to
`drone_bird_probe_fast`. This means the system was always running on the correct model even without
formal installation.

---

## Rejected Candidates

### drone-bird-yolo curriculum (chunks 1–10)

| Property | Value |
|----------|-------|
| Status | **reject_and_reset_training_strategy** (AP-026, 2026-03-13) |
| Dataset | `drone-bird-yolo` |
| Run name | `curriculum_drone-bird-yolo` |
| Epochs | 132/144 completed |
| Chunks published | chunk1_v2 through chunk10 |

**Best evaluated candidates:**

| Candidate | Chunk | Epochs | Night large_drones false_lock | Night gate |
|-----------|-------|--------|------------------------------|-----------|
| chunk6 | 6 | 73-84 | 0.830 | FAIL |
| chunk10 | 10 | 121-132 | 0.951 | FAIL |

Trend: **worsening with more epochs** — diverging from night-usable representations.
Root cause hypothesis: `drone-bird-yolo` dataset is IR-dominant; visible-light night performance
degrades as training progresses.

### epoch142 (rtx_drone_stability_12h_v1)

| Property | Value |
|----------|-------|
| Status | **hold_and_tune** (AP-011, 2026-03-11) |
| Reason | Persistent false-lock and ID-churn regressions on night/noise clips after retune cycle |
| Decision date | 2026-03-11 |

---

## Governance Rules (models/README.md)

| Status | Meaning |
|--------|---------|
| `baseline` | Accepted, installed at `models/baseline.pt`, has manifest |
| `candidate` | Under evaluation, not yet decided |
| `hold_and_tune` | Failed gate but potentially recoverable with tuning |
| `reject` | Failed gate, not worth pursuing further |
| `reject_and_reset_training_strategy` | Fundamental dataset/strategy problem; start over |

## Related

- [quality_gates.md](../concepts/quality_gates.md) — gate thresholds
- [training_strategy.md](../concepts/training_strategy.md) — why curriculum was rejected
- [model_decisions.md](../decisions/model_decisions.md) — formal decision log
