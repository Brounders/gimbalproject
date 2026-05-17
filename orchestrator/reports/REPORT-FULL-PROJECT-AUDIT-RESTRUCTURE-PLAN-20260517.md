# Full Project Audit Restructure Plan Intake

Date: 2026-05-17
Source: Claude audit summary provided by Human
Status: Accepted as restructure planning intake

## Principle

Do not physically restructure the repository first.  The first step is an
ownership and migration backlog that preserves runtime behavior and active
orchestrator state.

## Three-Track Plan

### Now

Build the project map and ownership layer:

- script registry for `python_scripts/`;
- runbook declaring primary operator UI;
- documentation for `ui_web/`;
- `automation/state/` status decision;
- commit-boundary review before push.

### Next

Prepare reversible cleanup:

- archive candidates only after reference proof;
- ignore generated artifacts and AppleDouble files;
- identify stale automation/model/run artifacts;
- add unit tests for high-risk untested mechanisms.

### Later

Physical folder migration:

- move scripts into `tools/training`, `tools/evaluation`, `tools/diagnostics`, `tools/data`, `tools/maintenance`;
- split configs into presets/gates/datasets;
- split tests into unit/integration/smoke only after import-safe migration;
- introduce docs architecture/operations/archive structure.

## Proposed Target Shape

```text
GimbalProject/
  app/
  src/uav_tracker/
  configs/
    presets/
    gates/
    datasets/
  tools/
    training/
    evaluation/
    diagnostics/
    data/
    maintenance/
  orchestrator/
    state/
    reports/
    tasks/
    training/
    briefs/
  datasets/
    gt/
    manifests/
    examples/
  models/
    production/
    candidates/
    external/
  runs/
  tests/
    unit/
    integration/
    smoke/
  docs/
    architecture/
    operations/
    archive/
```

## Guardrails

- No physical moves in stabilization intake.
- No deletes without owner decision and reference proof.
- No detector training until structure stabilization decides ownership and pack policy.
- `orchestrator/state/active_plan.md` remains execution authority.
- `TASK-20260517-108` is paused/deferred, not cancelled.

## Immediate Migration Backlog

1. `TASK-20260517-109`: Project structure stabilization intake.
2. `TASK-20260517-110`: Script registry and ownership map.
3. `TASK-20260517-111`: UI ownership decision and runbook.
4. `TASK-20260517-112`: Archive-candidate proof table.
5. `TASK-20260517-113`: Night detector unit-test plan.
