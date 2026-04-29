# REPORT-20260429: Tracker A/B — Template Lock vs ByteTrack (Night)

**Date:** 2026-04-29  
**Status:** ACCEPTED  
**Experiment:** Compare `LOCK_TRACKER_ENABLED=True` (template lock) vs `LOCK_TRACKER_ENABLED=False` (ByteTrack-only) on night quality gate.

---

## Setup

- Model: `models/baseline.pt` (drone_bird_probe_fast)
- Clip: `test_videos/night_ground_large_drones.mp4` (scene=night)
- Gate thresholds: `false_lock ≤ 0.55`, `id_chg/min ≤ 18.0`
- Flag: `--lock-tracker on/off` (added in infra commit 2b3a9ff)

---

## Results

| Configuration | id_chg/min | false_lock | fps | Gate PASS |
|---------------|-----------|------------|-----|-----------|
| Template lock ON (`--lock-tracker on`) | **12.23** | 0.510 | 28.0 | ✅ YES |
| Template lock OFF (`--lock-tracker off`) | **36.70** | 0.531 | 26.2 | ❌ NO |

---

## Finding

Template lock is **critical** for night scene gate compliance.

Disabling it causes `id_chg/min` to increase **3×** (12.23 → 36.70), far exceeding the 18.0 threshold. The Ultralytics `persist=True` ByteTrack does not retain small low-contrast night targets reliably across frames.

`false_lock` is largely unaffected (0.510 → 0.531), confirming that the lock precision is not the problem — identity continuity is.

---

## Decision

**Do NOT disable template lock for night scenes.** Template lock is the primary ID-stability mechanism for night tracking.

Any future ByteTrack migration (ALG-001 from master plan) must demonstrate `id_chg/min ≤ 18.0` on this clip before the template lock can be retired.

---

## Next Step

**YOLOv11 benchmark** — model intake with SHA256 + gate validation against baseline.  
`models/yolo11n.pt` is already present. Run: quality gate comparison baseline.pt vs yolo11n.pt.
