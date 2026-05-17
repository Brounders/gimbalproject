# TASK-20260517-104 Weak4 Training Preparation

Date: 2026-05-17
Owner: Codex Mac

## Result

TASK-20260517-104 is complete.  A reproducible GT-to-YOLO pack builder was
added and used to create the first weak4 targeted detector pack.

Runtime tracker/UI code was not changed.

## Generated Pack

Output directory:

- `runs/training_packs/weak4_103h_20260517`

Key files:

- `runs/training_packs/weak4_103h_20260517/data.yaml`
- `runs/training_packs/weak4_103h_20260517/manifest.json`
- `runs/training_packs/weak4_103h_20260517/manifest.csv`
- `runs/training_packs/weak4_103h_20260517/report.md`

The pack is runtime output and remains ignored by git.  It is reproducible from
the committed builder script and committed GT CSV inputs.

## Composition

| Metric | Count |
|---|---:|
| Total OK samples | 783 |
| Train images | 627 |
| Val images | 156 |
| Drone positives | 603 |
| Hard negative class samples | 178 |
| Background negatives | 2 |
| Skipped source/frame/invalid | 0 |

| Group | Count |
|---|---:|
| YOLO-low-confidence positives | 271 |
| YOLO-absent thermal positives | 332 |
| IR airplane hard negatives | 65 |
| Bird hard negatives | 113 |
| Invisible background negatives | 2 |

## Training Intent

This pack is not a full production dataset.  It is a targeted smoke and
micro-training pack for the exact Act5 ceiling:

- raise confidence/fit on weak positives where YOLO already has low-confidence
  signal;
- add explicit training pressure on thermal/medium positives where YOLO is
  effectively absent;
- keep negative pressure from airplane and bird clips so a quick improvement
  does not simply become an FP generator.

## Next Gate

Open `TRAIN-20260517-002` as the only active RTX job.  It is a smoke run, not a
quality claim.  Success means:

- training initializes;
- log is captured;
- `results.csv` is written;
- `weights/last.pt` is written;
- exit reason and epoch accounting are reported.

Only after that can a longer targeted detector run be considered.
