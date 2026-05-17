# REPORT-TASK-118-NO-TRAINING-DETECTOR-STRATEGY-20260517

Дата: 2026-05-17
Владелец: Codex Mac
Статус: Accepted locally

## Scope

Human отложил RTX/training: обучение будет рутинной работой позже, если оно не
нужно прямо сейчас.

TASK-20260517-118 должна определить следующий bounded local step без обучения.

## Evidence

Weak4 failure modes остаются разными:

| Clip | Evidence | No-training implication |
|------|----------|-------------------------|
| `1_minie3_range_close` | YOLO signal exists at low confidence: Hit@0.1 `0.5312` for `yolo@0.05`; runtime recall still `0.000`. | Возможна runtime threshold/ranking диагностика, но wide strip labels делают training pack unsafe. |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | YOLO signal strong at low confidence: Hit@0.1 `0.9543`; runtime recall `0.412`. | Вероятен source selection / confirmation / off-target problem, not pure detector absence. |
| `9_dji2_range_medium` | YOLO effectively absent; best thermal peak Hit@0.1 `0.2171`. | Без обучения улучшение возможно только через thermal/night source semantics and candidate handling. |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | YOLO effectively absent; best thermal peak Hit@0.1 `0.3333`. | Training eventually needed, but local no-training evidence gate can test whether night source is being under-promoted. |

Prior tracking-tools audit also noted:

- `DetectionSource.NIGHT` is not a primary source;
- `has_confirmed_drone_lock()` refuses non-primary active targets;
- when night is correct but no primary source confirms it, promotion semantics can
  remain fragile.

## Decision

Training is not required for the next step.

Do not run RTX. Do not start YOLO26 smoke now.

Next bounded step should be a local A/B evidence gate for IR/night source
authority:

1. measure current weak4 behavior with existing configs;
2. test a guarded candidate where night/thermal source can be treated as
   primary/confirmable only in IR/night contexts;
3. reject if protected clips, airplane/noise/bird gates regress;
4. only then decide whether runtime code change is justified.

## Open TASK-20260517-119

Task: Night-source authority A/B gate.

Goal:

- determine whether local runtime semantics can improve weak IR clips without
  training;
- specifically test whether `night` source under-promotion is part of the
  remaining ceiling.

Constraints:

- no model training;
- no RTX;
- no production model replacement;
- runtime code changes only if tests and A/B gate show a bounded safe diff.

## Non-Changes

- Runtime code was not changed in this decision gate.
- Training was not started.
- RTX was not used.
