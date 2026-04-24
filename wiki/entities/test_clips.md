# Test Clips

> Reference for all clips used in smoke, regression, and problem-pack gates

## Problem Pack Clips (critical gate clips)

### night_ground_large_drones.mp4 — PRIMARY PROBLEM CLIP

| Property | Value |
|----------|-------|
| Context | Night, visible-light |
| Target type | Large drones at ground level |
| Pack | `regression_pack_problem_night.csv` |
| Gate threshold | false_lock < 0.55, id_chg/min < 18.0 |

**Historical measurements:**

| State | false_lock | id_chg/min | Pass? |
|-------|-----------|-----------|-------|
| Baseline (2026-03-11, no hardening) | 0.861 | 58.72 | FAIL |
| AP-021 (stage-4) | 0.722 | 48.93 | FAIL |
| AP-022 (stage-4b) | 0.750 | 55.05 | FAIL |
| AP-024 (night knobs) | 0.771 | 30.58 | FAIL |
| **AP-025 (night_confirm=5)** | **0.510** | **12.23** | **PASS** |
| drone-bird-yolo chunk6 | 0.830 | 48.93 | FAIL |
| drone-bird-yolo chunk10 | 0.951 | 55.05 | FAIL |

### night_ground_indicator_lights.mp4

| Property | Value |
|----------|-------|
| Context | Night, visible-light |
| Target type | Indicator/warning lights (noise-like scene) |
| Pack | `regression_pack_problem_night.csv` |
| Gate threshold | noise-specific `--max-noise-id-changes-per-min` |

**Historical measurements:**

| State | false_lock | id_chg/min | Pass? |
|-------|-----------|-----------|-------|
| AP-021 (stage-4) | 0.339 | 0.00 | partial |
| AP-022 (stage-4b) | 0.458 | 0.00 | FAIL (false_lock too high) |
| AP-025 (night_confirm=5) | **0.121** | **0.00** | **PASS** |

---

## IR Problem Pack Clips

### Demo_IR_DRONE_146.mp4

| Property | Value |
|----------|-------|
| Context | IR/thermal |
| Target type | Drone, thermal |
| Pack | `regression_pack_problem_ir.csv` |

**Measurements:**
- Baseline (2026-03-11): false_lock=0.556, id_chg/min=0.00
- AP-019 (stage-2): false_lock=0.575, id_chg/min=0.00 (improved)
- De-facto baseline (AP-025 runtime): false_lock reference (IR gate open issue)

### IR_BIRD_001.mp4

| Property | Value |
|----------|-------|
| Context | IR/thermal |
| Target type | Bird, thermal |
| Pack | `regression_pack_problem_ir.csv` |

Baseline: false_lock=0.478, id_chg/min=0.00.

> ❓ OPEN: IR gate thresholds not yet formally defined. IR clips measured as reference only.

---

## General Regression Clips

### drone_closeup_mixkit_44644_360.mp4

| Property | Value |
|----------|-------|
| Context | Day |
| Target type | Drone, close-up |
| Pack | `regression_pack.csv` (day) |

Baseline: false_lock=1.000, id_chg/min=0.00, FPS=164.8.

> ⚠️ false_lock=1.000 is structural — drone exits frame quickly. All models score 1.000.
> Not a useful discriminator. Need a better day regression clip.

---

## Smoke Baseline Snapshot (2026-03-11, `default` preset, 180 frames/clip)

| Clip | FPS | id_chg/min | false_lock |
|------|-----|-----------|-----------|
| `drone_closeup_mixkit_44644_360.mp4` | 164.8 | 0.00 | 1.000 |
| `night_ground_large_drones.mp4` | 59.5 | 58.72 | 0.861 |
| `Demo_IR_DRONE_146.mp4` | 55.0 | 0.00 | 0.556 |
| `IR_BIRD_001.mp4` | 61.5 | 0.00 | 0.478 |
| **Aggregate** | **85.2** | **14.68** | **0.724** |

## Related

- [quality_gates.md](../concepts/quality_gates.md) — gate thresholds
- [runtime_hardening.md](../concepts/runtime_hardening.md) — measurement history
- [night_defect_history.md](../synthesis/night_defect_history.md)
