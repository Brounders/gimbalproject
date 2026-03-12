# models/ — Local Model Governance Contract

> Canonical source of truth for model states, artifacts, and decision rules.

---

## Model states

| State | Описание | Local artifact |
|-------|----------|----------------|
| `baseline` | Принятая production-модель, установленная в desktop-продукт | `models/baseline.pt` + `models/baseline_manifest.json` |
| `candidate` | Прошла training, проходит quality evaluation | любой path; передаётся через `--model <path>` в evaluation скрипты |
| `hold_and_tune` | Не прошла quality gate, но в пределах tunable range | нет фиксированного path; решение фиксируется в orchestrator-отчёте |
| `reject` | Не прошла quality gate с регрессом за границы tolerance | нет фиксированного path; решение фиксируется в orchestrator-отчёте |

---

## State transition rules

```
candidate
  ├── ВСЕ три context-gate PASS (day + night + ir)  →  baseline  (install via install_baseline.py)
  ├── любой context-gate FAIL, метрики tunable      →  hold_and_tune
  └── любой context-gate FAIL, регресс за tolerance →  reject
```

Context-gate команды:
```bash
python_scripts/run_quality_gate.py --context day    # preset=default
python_scripts/run_quality_gate.py --context night  # preset=night
python_scripts/run_quality_gate.py --context ir     # preset=antiuav_thermal
```

Quality gate thresholds: `python_scripts/run_quality_gate.py --help`
Operator tolerance boundaries: `OPERATOR_BASELINE.md → Граница baseline`

---

## Baseline artifacts

| Файл | Назначение |
|------|------------|
| `models/baseline.pt` | Принятая production-модель (бинарный, не хранится в git) |
| `models/baseline_manifest.json` | Metadata: источник, sha256, дата установки, ссылка на gate report |

### baseline_manifest.json format

```json
{
  "installed_at": "2026-03-12T00:00:00Z",
  "source_path": "/absolute/path/to/accepted_candidate.pt",
  "source_sha256": "abc123...",
  "notes": "Accepted after gate on all context-gates",
  "gate_report_path": "/absolute/path/to/runs/evaluations/quality_gate/<tag>quality_gate_night.json",
  "preset_gate_reports": {
    "day":   "/absolute/path/to/runs/evaluations/quality_gate/<tag>quality_gate_default.json",
    "night": "/absolute/path/to/runs/evaluations/quality_gate/<tag>quality_gate_night.json",
    "ir":    "/absolute/path/to/runs/evaluations/quality_gate/<tag>quality_gate_antiuav_thermal.json"
  }
}
```

---

## Install flow

```bash
# Install accepted candidate as new baseline (with traceability)
source tracker_env/bin/activate
PYTHONPATH=src python python_scripts/install_baseline.py \
    --source <path_to_accepted.pt> \
    --notes "Accepted YYYYMMDD: <brief description>" \
    --gate-report runs/evaluations/quality_gate/<tag>_quality_gate_<preset>.json

# Dry run (verify before copying)
PYTHONPATH=src python python_scripts/install_baseline.py \
    --source <path_to_accepted.pt> --dry-run
```

See also: `RUNBOOK.md → Baseline model`
