# TASK-20260517-106 Weak4 V2/V3 Protected Gate

Date: 2026-05-17
Owner: Codex Mac

## Goal

Run the next concrete step after Micro3: try a protected training strategy that
improves weak clips without regressing the already-strong
`antiuav_rgbt_train_20190925_205804_1_2_infrared` gate clip.

No runtime tracker/UI code was changed.

## Candidates

### V2 Protected Holdout

Pack:

- `runs/training_packs/weak4_v2_protected_20260517`

Composition:

- total OK samples: 607;
- train: 494;
- val: 113;
- drone positives: 428;
- hard negative class samples: 178;
- background negatives: 1;
- protected `antiuav_rgbt_train` removed from training pressure.

Training:

- run: `runs/detect/train/yolo26_weak4_v2_protected_freeze10_lr8e4_20260517`
- model: `models/yolo26n.pt`
- epochs: 3
- lr0: 0.0008
- freeze: 10
- device: mps
- exit: 0

Decision: rejected.  Freeze plus lower LR prevented the candidate from moving
the weak clips; best-source metrics fell back to night/thermal heuristics.

### V3 Replay Lower LR

Pack:

- `runs/training_packs/weak4_103h_20260517`

Training:

- run: `runs/detect/train/yolo26_weak4_v3_replay_lr8e4_20260517`
- model: `models/yolo26n.pt`
- epochs: 3
- lr0: 0.0008
- freeze: 0
- device: mps
- exit: 0

Decision: rejected.  Replay plus lower LR was safer than V2 but did not recover
the Micro3 breakthrough and still relied on night fallback for protected
material.

## Evidence Comparison

| Clip | Baseline best Hit@0.1 | Micro3 best Hit@0.1 | V2 best Hit@0.1 | V3 best Hit@0.1 |
|---|---:|---:|---:|---:|
| `1_minie3_range_close` | 0.5312 | 1.0000 | 0.0312 | 0.1875 |
| `9_dji2_range_medium` | 0.2171 | 0.5855 | 0.2171 | 0.2171 |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | 0.3333 | 0.3333 | 0.3333 | 0.3333 |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | 0.9543 | 0.8514 | 0.8514 | 0.8514 |

Evidence directories:

- baseline: `runs/evaluations/detector_evidence_pack/weak4_20260517`
- Micro3: `runs/evaluations/detector_evidence_pack/weak4_micro3_20260517`
- V2: `runs/evaluations/detector_evidence_pack/weak4_v2_protected_20260517`
- V3: `runs/evaluations/detector_evidence_pack/weak4_v3_replay_20260517`

## Decision

Do not promote V2 or V3.

The useful signal remains Micro3: it proves the detector ceiling can move on
`1_minie3_range_close` and `9_dji2_range_medium`.  The failure is that the
training pack/gate design does not yet preserve the strong protected clip and
does not move `antiuav_rgbt_20190925_200805`.

## Next Step

Open `TASK-20260517-107`: visual label and pack-composition audit before more
training.

Concrete work:

1. Render contact sheets from weak4 pack images with YOLO boxes overlaid.
2. Split samples into:
   - valid positive;
   - too-large/ambiguous bbox;
   - off-target/OSD contaminated;
   - hard negative;
   - protected holdout.
3. Rebuild the next pack only after rejecting bad labels and separating
   training material from gate material.
