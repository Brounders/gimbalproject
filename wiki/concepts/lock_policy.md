# Lock Policy

> Isolated decision layer: when to confirm, hold, reacquire, or release a tracking lock

## States

```
SCAN → ACQUIRE → LOCK-FOCUS → (REACQUIRE or SCAN)
```

- **SCAN**: no confirmed target; system scanning all detections
- **ACQUIRE**: candidate target accumulating confirmation frames
- **LOCK-FOCUS**: confirmed lock; secondary targets suppressed
- **REACQUIRE**: primary target temporarily lost; spatial gate active

## Key Decisions

| Decision | Parameter | Meaning |
|----------|-----------|---------|
| Enter LOCK | `lock_confirm_frames` | Consecutive frames needed to confirm lock |
| Enter LOCK | `drone_lock_score_min` | Min detection score to enter lock |
| Hold LOCK | `lock_lost_grace` | Grace frames before lock considered lost |
| Exit LOCK | `lock_mode_release_frames` | Frames before releasing lock state |
| Reacquire | `drone_reacquire_score_min` | Min score for reacquire |
| Reacquire | `lock_reacquire_dist` | Base spatial gate (px); effective = base + speed_bonus (up to +90 px) |
| Track acquisition | `track_state_acquire_frames` | Detections needed to establish track |
| Track loss | `track_state_lost_frames` | Frames before track → LOST state |
| Lock acquisition | `lock_mode_acquire_frames` | Confirm-frames to enter lock mode |

## ID Stability Parameters

These control `active_id_changes_per_min`:

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `active_id_switch_cooldown_frames` | 30 | Minimum frames between ID switches |
| `active_id_switch_allow_if_lost_frames` | 6 | Lost frames before cooldown bypass |
| `class_ema_alpha` | 0.18 | Drone score EMA alpha (lower = slower/stabler) |
| `lock_tracker_min_score` | 0.42 | Min correlation score for lock tracker |

## False Lock

`false_lock_rate` = fraction of LOCK frames where no real target is present.
This is the primary quality metric for night and IR contexts.

**Key insight from AP-025**: The dominant cause of false-lock on night large-target clips
was transient false positives at the **night detector level**, not the lock policy layer.
Fixing `night_confirm=5` (forcing 5 consecutive detections) reduced false_lock from 0.771 → 0.510
and id_chg/min from 30.58 → 12.23 — crossing the gate threshold.

## Accepted Night Runtime Contract (AP-025)

| Parameter | Value | vs Default |
|-----------|-------|-----------|
| `lock_confirm_frames` | 7 | +2 |
| `lock_lost_grace` | 1 | −1 (AP-025 reverted to 1; was tried at 2 but caused regression) |
| `lock_mode_release_frames` | 4 | −2 |
| `lock_reacquire_dist` | 90 | −30 |
| `drone_lock_score_min` | 0.64 | +0.02 |
| `drone_reacquire_score_min` | 0.52 | +0.04 |
| `track_state_acquire_frames` | 4 | +1 |
| `lock_mode_acquire_frames` | 3 | +1 |
| `active_id_switch_cooldown_frames` | 60 | ×2 |
| `active_id_switch_allow_if_lost_frames` | 12 | ×2 |
| `track_state_lost_frames` | 12 | +4 |
| `lock_tracker_min_score` | 0.52 | +0.10 |
| `night_confirm` | 5 | +2 (key fix) |
| `night_track_dist` | 65 | +23 |

## Related

- [detection_pipeline.md](detection_pipeline.md) — where lock policy sits in the flow
- [runtime_hardening.md](runtime_hardening.md) — how these values were arrived at
- [presets.md](../entities/presets.md) — per-preset values
- [night_defect_history.md](../synthesis/night_defect_history.md) — full history of night fixes
