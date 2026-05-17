# REPORT-TASK-121-WEAK4-OFFTARGET-GEOMETRY-AUDIT-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted locally

## Scope

TASK-20260517-121 анализировала baseline weak4 geometry после rejection of
night-primary candidate. Цель: понять следующий no-training рычаг.

Input:

- `runs/evaluations/tracking_gt_diagnostics/task120_baseline__20260517_171712`

## Findings

| Clip | Geometry / source evidence | Interpretation |
|------|----------------------------|----------------|
| `1_minie3_range_close` | active presence `0.981`, source mostly `night`, recall `0.000`, center error p95 `247.6`, scale ratio p95 `0.049`, bbox area CV `0.0`. | Night detector is active but tracks a stable wrong/tiny geometry relative to GT. This is not solved by source authority. |
| `9_dji2_range_medium` | active presence `0.310`, source `night`, recall `0.275`, avg IoU `0.348`, center error p95 `43.4`. | When night proposal appears, it can be useful. Problem is proposal frequency/coverage, not primary authority. |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | active presence `1.000`, recall `0.000`, center error p95 `341.4`, scale ratio p95 `14.9`, sources `yolo/lock/local`; night proposal rate only `0.002`. | Tracker is confidently locked on wrong large/remote geometry. Night source is almost absent. |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | active presence `1.000`, recall `0.387`, median IoU `0.0`, center error p95 `399.9`, sources mostly `lock/local`; night proposal rate `0.003`. | Protected clip is partially good but unstable/off-target for many frames. Any runtime lever can easily regress it. |

## Decision

Do not add another policy/source-authority tweak now.

The next bounded no-training step is visual error-sample audit from the same
diagnostic runner:

- render matched/missed/off-target samples for baseline weak4;
- classify off-targets into wrong object, wrong scale, OSD/edge, lock drift, and
  GT geometry mismatch;
- only after visual classification choose between:
  - peak-box sizing/threshold experiment;
  - geometry filter for large/remote false active bbox;
  - telemetry enhancement;
  - deferring to data/training.

## Open TASK-20260517-122

Task: Weak4 visual off-target sample audit.

Constraints:

- no RTX;
- no training;
- no runtime code changes until visual categories are known.

## Non-Changes

- Runtime code was not changed in this task.
- Training was not started.
- Candidate preset was not promoted.
