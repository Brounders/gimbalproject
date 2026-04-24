# Quality Gates

> Thresholds and tooling that define "promotable" vs "reject" for model candidates and runtime configs

## Gate Contract (current accepted, AP-025 runtime)

| Context | Metric | Threshold | Status |
|---------|--------|-----------|--------|
| Night | `false_lock_rate` | < 0.55 | Enforced |
| Night | `id_chg/min` | < 18.0 | Enforced |
| Night-noise | `id_chg/min` | separate `--max-noise-id-changes-per-min` | Enforced (AP-021) |
| IR | `false_lock_rate` | — | Known failing, open issue |
| Day | `false_lock_rate` | structural | Day clip false_lock=1.000 across all models — not a discriminator |

> ❓ OPEN: IR gate threshold not yet formally defined. Baseline installs with IR gate measured as reference only.

> ⚠️ CONTRADICTION: Day gate false_lock=1.000 universally — the day regression pack clip causes
> this regardless of model. Not a real discriminator until a better day clip is sourced.

## Gate Scripts

| Script | Purpose |
|--------|---------|
| `python_scripts/run_quality_gate.py` | Full quality gate; `--context day\|night\|ir` routing |
| `python_scripts/run_offline_benchmark.py` | Offline benchmark with report metadata |
| `python_scripts/run_problem_pack_gate.py` | Short problem-pack mini-gate |
| `python_scripts/run_quick_kpi_smoke.py` | Quick KPI smoke (180 frames per clip) |
| `python_scripts/compare_kpi_snapshots.py` | A/B evidence comparison |
| `python_scripts/install_baseline.py` | Install accepted model + write manifest |

## Regression Packs

| File | Context | Clips |
|------|---------|-------|
| `configs/regression_pack.csv` | General | All clips |
| `configs/regression_pack_problem_night.csv` | Night | Problem clips only |
| `configs/regression_pack_problem_ir.csv` | IR | Problem clips only |

## Decision Artifact

Gate decisions are written to `automation/state/decision_log.json`.
Format per entry: `decision_id`, `dataset_id`, `decision`, `runtime_state`, `reason`, `gate_reports`.

Valid decisions: `promote`, `hold_and_tune`, `reject_and_reset_training_strategy`, `install_as_baseline`.

## Canonical Local Flow (from RUNBOOK.md)

```
quick smoke → benchmark → quality-gate → decision
```

For problem-clip loop:
```
run_problem_pack_gate.py (night) → compare_kpi_snapshots.py → tune → repeat
```

## Baseline Governance

- `models/baseline.pt` — canonical local model contract (not tracked in git; must be installed manually)
- `models/baseline_manifest.json` — traceability: SHA256, source, gate results, runtime_state
- `models/README.md` — defines roles: `baseline`, `candidate`, `hold_and_tune`, `reject`
- `python_scripts/install_baseline.py` — installs a model and writes the manifest

> `baseline.pt` was formally installed as `drone_bird_probe_fast` (AP-026 autonomous session).
> SHA256: `bedc77fe7b899de1ac68ae654f49fcee6301a9d3f8a61e9eff5c1e8d66641d44`

## Related

- [models.md](../entities/models.md) — model statuses and gate results
- [test_clips.md](../entities/test_clips.md) — what clips are in each regression pack
- [model_decisions.md](../decisions/model_decisions.md) — formal decision log
