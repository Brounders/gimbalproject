# TASK-20260517-107 Weak4 Label And Pack Audit

Date: 2026-05-17
Owner: Codex Mac

## Result

Contact sheets were rendered for the weak4 training pack:

- `runs/evaluations/yolo_pack_contact_sheets/weak4_103h_20260517/index.md`
- `runs/evaluations/yolo_pack_contact_sheets/weak4_103h_20260517/yolo_low_conf_positive.jpg`
- `runs/evaluations/yolo_pack_contact_sheets/weak4_103h_20260517/yolo_absent_thermal_positive.jpg`
- `runs/evaluations/yolo_pack_contact_sheets/weak4_103h_20260517/ir_airplane_hard_negative.jpg`
- `runs/evaluations/yolo_pack_contact_sheets/weak4_103h_20260517/bird_hard_negative.jpg`
- `runs/evaluations/yolo_pack_contact_sheets/weak4_103h_20260517/invisible_background_negative.jpg`

Added reusable renderer:

- `python_scripts/render_yolo_pack_contact_sheets.py`

Runtime tracker/UI code was not changed.

## Findings

The pack is not just "weak positives plus negatives"; it contains incompatible
positive geometries inside the same class:

1. `1_minie3_range_close` contributes very wide, thin horizontal boxes across a
   thermal ground/terrain band.  These labels are visually unlike a compact UAV
   detector target and can teach the detector to look for broad horizon/ground
   strips.
2. `antiuav_rgbt_train_20190925_205804_1_2_infrared` contributes large,
   aircraft-shaped thermal silhouettes.  This is a different scale/geometry
   regime from the small hotspot clips.
3. `yolo_absent_thermal_positive` is visually closer to the desired small
   thermal target regime: compact boxes around small hotspots.

This explains the observed behavior:

- Micro3 can move some weak clips, but the model forgets or distorts the
  already-strong protected clip.
- V2/V3 lower-risk training fails because the data mixture itself is not clean
  enough; changing LR/freeze does not fix label geometry conflicts.

## Decision

Do not run more blind fine-tune variants from the current weak4 pack.

The next pack must be source/scale aware:

- small-hotspot positives should be trained as a coherent regime;
- large silhouette/strip-like labels must be separated as gate material or
  relabeled before they are used for training;
- protected clips must remain a gate until the pack no longer causes forgetting.

## Next Step

Open `TASK-20260517-108`: build a scale/source-aware weak4 pack and rerun a
single bounded candidate.

Initial rules:

1. Exclude or quarantine `1_minie3_range_close` wide strip labels until manually
   corrected or separately represented.
2. Keep `antiuav_rgbt_train` as protected gate, not ordinary training pressure.
3. Train first on compact thermal positives plus hard negatives.
4. Accept only if `9_dji2_range_medium` or `antiuav_rgbt_20190925_200805`
   improves without causing protected-gate regression.
