# REPORT-TASK-120-NIGHT-PRIMARY-CANDIDATE-GATE-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Rejected candidate

## Scope

TASK-20260517-120 проверяла candidate config без RTX и без обучения:

- baseline: `antiuav_thermal_peak`;
- candidate: `antiuav_thermal_peak_night_primary`;
- единственное поведенческое отличие candidate: `night_primary_source_enabled`
  включен, чтобы `night` target мог быть confirmable primary source.

## Runs

Baseline:

- `runs/evaluations/tracking_gt_diagnostics/task120_baseline__20260517_171712`

Candidate:

- `runs/evaluations/tracking_gt_diagnostics/task120_candidate__20260517_171712`

Inputs:

- `1_minie3_range_close`
- `9_dji2_range_medium`
- `antiuav_rgbt_20190925_200805_1_2_infrared`
- `antiuav_rgbt_train_20190925_205804_1_2_infrared`

## Result

| Clip | Baseline recall@0.1 | Candidate recall@0.1 | Decision |
|------|--------------------:|---------------------:|----------|
| `1_minie3_range_close` | 0.000 | 0.000 | no improvement |
| `9_dji2_range_medium` | 0.275 | 0.246 | worse |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | 0.000 | 0.000 | no improvement |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | 0.387 | 0.387 | unchanged |

Additional risk:

- `9_dji2_range_medium` false-lock rate increased from `0.036` to `0.071`.

## Decision

Reject candidate preset.

Do not enable `night_primary_source_enabled` in operator/runtime presets.

The default-off mechanism remains available for controlled experiments, but the
first A/B gate did not justify promotion.

## Interpretation

The remaining weak-clip ceiling is not solved by simply allowing `night` source
to become confirmable primary. The issue is more likely candidate geometry /
detector proposal quality:

- `1_minie3_range_close` remains off-target despite active bbox frames;
- `antiuav_rgbt_20190925` remains fully off-target;
- `9_dji2` loses matched frames when night source authority is increased.

## Next Step

Open TASK-20260517-121:

- analyze off-target geometry on weak4 diagnostics;
- compare active bbox vs GT center/scale for baseline;
- identify whether the next no-training lever is bbox geometry filtering,
  peak-box sizing, or detector proposal scoring;
- still no RTX/training.

## Non-Changes

- RTX was not used.
- Training was not started.
- Production presets were not changed.
- Candidate config was not retained after rejection.
