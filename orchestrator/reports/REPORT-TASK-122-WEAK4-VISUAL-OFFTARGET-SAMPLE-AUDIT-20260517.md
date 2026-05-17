# REPORT-TASK-122-WEAK4-VISUAL-OFFTARGET-SAMPLE-AUDIT-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted locally

## Scope

TASK-20260517-122 требовала render and classify weak4 visual error samples перед
новыми runtime tweaks.

## Run

Output:

- `runs/evaluations/tracking_gt_diagnostics/task122_visual_baseline__20260517_172304`

Command:

- `python_scripts/run_tracking_gt_diagnostics.py` on four weak4 GT CSV files,
  preset `antiuav_thermal_peak`, `--render-errors --max-error-samples 8`.

## Visual Findings

| Clip | Visual classification | Decision |
|------|----------------------|----------|
| `1_minie3_range_close` | GT is a wide thermal ground/terrain strip; tracker follows a small bright object elsewhere. | Do not tune runtime to match this label. This is label/GT geometry mismatch for compact UAV tracking. |
| `9_dji2_range_medium` | Night detector can match the target; off-target samples are near-target/box-placement misses, not OSD. | Potential later lever: peak box sizing/scoring, but not first priority. |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | YOLO/lock starts on top-left OSD text (`俯仰 0.55`) while GT target is on the building. Current ignore zone misses this OSD area. | Strong no-training lever: wider OSD ignore zone candidate. |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | Early frames match well; later lock drifts to nearby empty/thermal patch. | Potential later lever: lock drift release/validation, but protected regression risk is high. |

## Decision

The next bounded no-training candidate should be OSD ignore-zone widening for
thermal/RGBT presets, not another source-authority tweak.

## Open TASK-20260517-123

Task: Thermal OSD ignore-zone A/B gate.

Constraints:

- no RTX;
- no training;
- candidate preset only;
- production presets unchanged unless A/B passes.

## Non-Changes

- Runtime code was not changed in this task.
- Training was not started.
- No candidate was promoted.
