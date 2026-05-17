# Detector Evidence Weak4 Gate

Date: 2026-05-17
Owner: Codex Mac
Task: TASK-20260516-100

## Summary

The Act5 selector/reacquire series is closed for now.  The remaining weak clips
are no longer primarily a selector problem.  The weak4 detector evidence pack
shows two different detector failure modes:

1. YOLO signal exists but is below the current operating confidence on
   `1_minie3_range_close` and `antiuav_rgbt_train_20190925_205804_1_2_infrared`.
2. YOLO signal is effectively absent on `9_dji2_range_medium` and
   `antiuav_rgbt_20190925_200805_1_2_infrared`; thermal peak has weak but real
   overlap and should inform targeted training data.

Generated evidence is under ignored runtime output:

- `runs/evaluations/detector_evidence_pack/weak4_20260517/summary.csv`
- `runs/evaluations/detector_evidence_pack/weak4_20260517/summary.json`
- `runs/evaluations/detector_evidence_pack/weak4_20260517/report.md`

## Evidence

| Clip | Visible frames | Best source | Hit@0.1 | Diagnosis |
|---|---:|---|---:|---|
| `1_minie3_range_close` | 96 | `yolo@0.05` | 0.5312 | `yolo_signal_exists_tune_or_train` |
| `9_dji2_range_medium` | 152 | `antiuav_thermal_peak` | 0.2171 | `weak_detector_training_needed` |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | 180 | `antiuav_thermal_peak` | 0.3333 | `weak_detector_training_needed` |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | 175 | `yolo@0.05` | 0.9543 | `yolo_signal_exists_tune_or_train` |

## Decision

Closed:

- Act5 universal selector/reacquire behavior through 103a-103f.
- `TASK-20260516-100` as the high-level detector/training decision gate.
- The invalid YOLO26 smoke attempt remains excluded from evidence because it
  produced only `args.yaml` and no `results.csv`, `weights/best.pt`, or
  `weights/last.pt`.

Not closed:

- Targeted detector training scope for the two YOLO-absent weak clips.
- Confidence/threshold policy for clips where YOLO already sees the target at
  low confidence.
- Any production model replacement.

## Next Bounded Step

Open `TASK-20260517-104` as the 103h detector/training preparation step:

1. Build a small training manifest from the weak4 GT material and hard negatives.
2. Split it by failure mode:
   - YOLO-low-confidence positives: `1_minie3_range_close`,
     `antiuav_rgbt_train_20190925_205804_1_2_infrared`;
   - YOLO-absent thermal/medium positives: `9_dji2_range_medium`,
     `antiuav_rgbt_20190925_200805_1_2_infrared`;
   - hard negatives from OSD/airplane/noise/bird clips already represented in
     Target Lab material.
3. Before any long run, execute a strict smoke run whose only success criteria
   are artifacts and resumeability:
   - tiny verified subset;
   - `epochs=1`;
   - `workers=0`;
   - `save_period=1`;
   - log captured with `tee` into the run directory;
   - external timeout 45-60 minutes;
   - required artifacts: `results.csv` and `weights/last.pt`.

## Smoke Failure Hypothesis

The stopped YOLO26 smoke is not model evidence.  The most likely problem is not
training quality but governance: no external timeout/checkpoint policy and no
artifact contract.  A corrected smoke must first prove the RTX training command
can initialize, write logs, save a checkpoint, and survive resume accounting.
