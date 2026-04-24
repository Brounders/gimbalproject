# Runtime Hardening

> Progressive tuning of lock policy and night detector parameters across AP-018 through AP-025

## Summary

The runtime hardening campaign ran from AP-018 to AP-025 (2026-03-11 to 2026-03-13).
It addressed two distinct failure modes: **false-lock** (locking onto non-targets) and
**ID instability** (frequent target ID changes).

The campaign concluded with **AP-025 achieving the first PASS on the night problem-pack gate
in project history**.

## Progression

### AP-018 (stage 1) — Lock threshold tightening
Target: reduce false-lock on night/IR by raising score thresholds and lock confirmation.

| Parameter | File | Before | After |
|-----------|------|--------|-------|
| `drone_lock_score_min` | `night.yaml` | 0.58 | 0.64 |
| `drone_reacquire_score_min` | `night.yaml` | 0.45 | 0.52 |
| `lock_confirm_frames` | `night.yaml` | 5 | 7 |
| `drone_lock_score_min` | `antiuav_thermal.yaml` | 0.56 | 0.60 |
| `drone_reacquire_score_min` | `antiuav_thermal.yaml` | 0.42 | 0.48 |
| `lock_confirm_frames` | `antiuav_thermal.yaml` | 5 | 7 |

`lock_confirm_frames` first exposed via YAML in AP-018.

### AP-019 (stage 2) — Grace period and spatial gate
Target: reduce tolerance for detection gaps, faster lock release, narrower reacquire gate.

| Parameter | File | Before | After |
|-----------|------|--------|-------|
| `lock_lost_grace` | `night.yaml` | 2 | 1 |
| `lock_mode_release_frames` | `night.yaml` | 6 | 4 |
| `lock_reacquire_dist` | `night.yaml` | 120 | 90 |
| `lock_lost_grace` | `antiuav_thermal.yaml` | 2 | 1 |
| `lock_mode_release_frames` | `antiuav_thermal.yaml` | 6 | 4 |
| `lock_reacquire_dist` | `antiuav_thermal.yaml` | 120 | 90 |

`lock_lost_grace` and `lock_reacquire_dist` first exposed via YAML in AP-019.

### AP-020 (stage 3) — ID switch cooldown
Target: reduce `id_chg/min` on night large-drone scenes.

| Parameter | File | Before | After |
|-----------|------|--------|-------|
| `active_id_switch_cooldown_frames` | `night.yaml` | 30 | 60 |
| `class_ema_alpha` | `night.yaml` | 0.22 | 0.15 |

### AP-021 (stage 4) — Track acquisition hardening
Target: fewer false tracks from indicator lights; ID switch bypass for long losses.

| Parameter | File | Before | After |
|-----------|------|--------|-------|
| `track_state_acquire_frames` | `night.yaml` | 3 | 4 |
| `lock_mode_acquire_frames` | `night.yaml` | 2 | 3 |
| `active_id_switch_allow_if_lost_frames` | `night.yaml` | 6 | 12 |

Results: `night_ground_indicator_lights` bounded; `night_ground_large_drones` still failing
(false_lock=0.722, id_chg/min=48.93).

### AP-022 (stage 4b) — Lock tracker correlation gate
Target: reduce false lock entries via stricter correlation; hold track longer for large drones.

| Parameter | File | Before | After |
|-----------|------|--------|-------|
| `track_state_lost_frames` | `night.yaml` | 8 | 12 |
| `lock_tracker_min_score` | `night.yaml` | 0.42 | 0.52 |

Results: `night_ground_large_drones` still failing (false_lock=0.750, id_chg/min=55.05).
`night_ground_indicator_lights` bounded but false_lock=0.458 still above threshold.

Adversarial review insight: stage-5 should not be a generic lock-policy pass but a targeted
**night detector contract** — expose `NIGHT_MAX_AREA`, `NIGHT_TRACK_DIST`, `NIGHT_LOST_MAX`.

### AP-024 — Night detector knobs exposed
Target: address root cause at detector level, not lock policy.

New YAML keys added to `profile_io.py::apply_overrides` mapping:
`night_max_area`, `night_track_dist`, `night_lost_max`, `night_confirm`, `night_max_ar`.

6-config sweep findings:
- `night_track_dist` is the primary driver of `id_chg/min`
- `night_lost_max` is the primary driver of `false_lock`
- `night_max_area` had no measurable effect on test clips

Final AP-024 config: `night_max_area=220`, `night_track_dist=65`, `night_lost_max=8`

Results:
- `night_ground_large_drones`: id_chg/min=30.58 (−44%), false_lock=0.771 (+0.021 marginal regression)
- Gap reduced from 3.06× to 1.70× vs threshold 18.0 — still FAIL

### AP-025 — night_confirm + NIGHT_MAX_AR exposed → FIRST PASS

New knobs: `night_confirm` (consecutive frames to establish detection), `night_max_ar`.

Key finding: `lock_lost_grace=2` caused id_chg/min regression; kept at 1.

**Final config: `night_confirm=5`, `night_track_dist=65`, `lock_lost_grace=1`**

Results:
- `night_ground_large_drones`: false_lock=**0.510** (was 0.771, −34%), id_chg/min=**12.23** (was 30.58, −60%) → **PASS**
- `night_ground_indicator_lights`: false_lock=**0.121** (was 0.458, −79%), id_chg/min=0.00 → **PASS**

**Night problem-pack gate: FIRST PASS in project history.**

Mechanism: `night_confirm=5` filtered transient false positives at detector level before
they could propagate to the lock policy layer.

## Key Lessons

1. Lock policy tuning alone cannot fix detector-level instability — must address root cause.
2. `night_confirm` (continuity gating at detector) is the dominant lever for large-target night.
3. `lock_lost_grace` at value 2 causes id_chg regression — always use 1 for night.
4. `night_track_dist=65` (vs default 42) needed for fast large targets; don't go lower.
5. `night_max_area` had no measurable effect in the tested clip set.

## Related

- [lock_policy.md](lock_policy.md) — parameter reference
- [night_defect_history.md](../synthesis/night_defect_history.md) — measurement timeline
- [test_clips.md](../entities/test_clips.md) — problem clip descriptions
