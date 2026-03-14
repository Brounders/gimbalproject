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

## Per-Context Model Slots

Когда для каждого контекста обучена и принята специализированная модель, она устанавливается
в именованный slot. Пресет YAML автоматически берёт модель из своего slot-файла.

| Slot файл | Контекст | Пресет YAML | Статус |
|-----------|----------|-------------|--------|
| `models/baseline.pt` | Universal (все контексты) | все пресеты | **Установлен** (AP-025) |
| `models/night_model.pt` | Night visible-light | `configs/night.yaml` | Ожидает обучения |
| `models/ir_model.pt` | IR/thermal | `configs/antiuav_thermal.yaml` | Ожидает обучения |
| `models/day_model.pt` | Day visible-light | `configs/default.yaml` | Ожидает обучения |

**Правила:**
- Slot-файл = принятая production-модель для данного контекста
- Пока специализированная модель не обучена — пресет указывает на `models/baseline.pt`
- Кандидаты передаются через `--model <path>` в gate-скриптах (произвольный путь)
- После acceptance: `install_baseline.py --context night|ir|day` устанавливает в slot

---

## Baseline artifacts

| Файл | Назначение |
|------|------------|
| `models/baseline.pt` | Принятая universal production-модель (не хранится в git) |
| `models/baseline_manifest.json` | Metadata: источник, sha256, дата установки, ссылка на gate report |
| `models/night_manifest.json` | Metadata для night_model.pt (создаётся при install --context night) |
| `models/ir_manifest.json` | Metadata для ir_model.pt (создаётся при install --context ir) |
| `models/day_manifest.json` | Metadata для day_model.pt (создаётся при install --context day) |

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
