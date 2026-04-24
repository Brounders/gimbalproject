# Night Defect History

> Complete timeline of the night large-target false-lock problem from discovery to first PASS

## The Problem

`night_ground_large_drones.mp4` — the primary problem clip — showed extreme instability
from the very first baseline measurement:
- `false_lock=0.861` (86% of lock frames were false)
- `id_chg/min=58.72` (target ID changed ~59 times per minute)

Gate thresholds: `false_lock < 0.55` AND `id_chg/min < 18.0`.

## Timeline

### 2026-03-11 — Baseline Measurement

No hardening applied. Smoke run with `default` preset, 180 frames.

| Clip | false_lock | id_chg/min |
|------|-----------|-----------|
| `night_ground_large_drones` | 0.861 | 58.72 |

### 2026-03-11 — AP-018: Lock Threshold Tightening

Raised `drone_lock_score_min`, `drone_reacquire_score_min`, `lock_confirm_frames`.
Lock policy harder to enter.

### 2026-03-11 — AP-019: Grace Period + Spatial Gate

Reduced `lock_lost_grace` (2→1), `lock_mode_release_frames` (6→4), `lock_reacquire_dist` (120→90).
Faster lock release, narrower reacquire window.

### 2026-03-11 — AP-020: ID Switch Cooldown

Doubled `active_id_switch_cooldown_frames` (30→60). Slowed EMA (`class_ema_alpha` 0.22→0.15).
Target: reduce id_chg/min directly.

### 2026-03-12 — AP-021 (stage-4): Track Acquisition Hardening

`track_state_acquire_frames` +1, `lock_mode_acquire_frames` +1, `active_id_switch_allow_if_lost_frames` ×2.

**First partial victory**: `night_ground_indicator_lights` bounded.
`night_ground_large_drones` still: false_lock=0.722, id_chg/min=48.93.

### 2026-03-13 — AP-022 (stage-4b): Lock Tracker Correlation Gate

`track_state_lost_frames` (8→12), `lock_tracker_min_score` (0.42→0.52).

`night_ground_large_drones`: false_lock=0.750, id_chg/min=55.05. **Regression on id_chg.**

**Adversarial review finding (AP-026-review):** The next step is NOT more lock policy tuning.
Root cause is at the **night detector level**. Must expose detector knobs.

### 2026-03-13 — AP-024: Night Detector Knobs Exposed

New YAML keys: `night_max_area`, `night_track_dist`, `night_lost_max`, `night_confirm`, `night_max_ar`.

6-config tuning sweep:
- `night_track_dist` is the primary driver of id_chg/min
- `night_lost_max` is the primary driver of false_lock
- `night_max_area` had no measurable effect

Best AP-024 config: `night_max_area=220`, `night_track_dist=65`, `night_lost_max=8`.

| Clip | false_lock | id_chg/min |
|------|-----------|-----------|
| `night_ground_large_drones` | 0.771 | 30.58 (−44%) |

Gap vs threshold: 1.70× (was 3.06×). Still FAIL.

### 2026-03-13 — AP-025: night_confirm=5 → FIRST PASS

New knob: `night_confirm` (consecutive frames required to establish detection = continuity gate).

Sweep finding: `night_confirm` is the dominant lever.
`lock_lost_grace=2` tried and abandoned (caused id_chg regression back to 55.05).

**Final config: `night_confirm=5`, `night_track_dist=65`, `lock_lost_grace=1`.**

| Clip | false_lock | id_chg/min | Gate |
|------|-----------|-----------|------|
| `night_ground_large_drones` | **0.510** | **12.23** | **PASS** |
| `night_ground_indicator_lights` | **0.121** | **0.00** | **PASS** |

**Night problem-pack gate PASS — first time in project history.**

## Root Cause Analysis

The fundamental issue was that transient false positives were generated at the **night detector level**
(MOG2 blob analysis) and propagated into the lock policy layer. No amount of lock policy tuning
could fix detector-level instability.

The fix (`night_confirm=5`) implemented continuity gating: a blob must appear in 5 consecutive
frames before it enters the candidate set. This filtered out single-frame noise blobs that were
causing false entries into the lock state.

## Why It Took So Many Stages

Each AP from AP-018 through AP-022 improved lock policy parameters without questioning the
detector layer. The adversarial review in AP-026 was the turning point: it correctly identified
that the root cause was in the detector, not the lock policy.

## Current Status

Night gate: **PASS** (AP-025, `drone_bird_probe_fast`).
The problem is considered closed for the current model+runtime combination.

Next risk: if a new model is trained, the night gate must be re-verified — new models may not
have the same night detection stability properties.

## Related

- [runtime_hardening.md](../concepts/runtime_hardening.md) — all parameter changes
- [lock_policy.md](../concepts/lock_policy.md) — what each parameter does
- [test_clips.md](../entities/test_clips.md) — measurement data
- [models.md](../entities/models.md) — model gate results
