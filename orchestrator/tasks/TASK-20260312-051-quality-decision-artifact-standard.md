# TASK: TASK-20260312-051-quality-decision-artifact-standard

Task ID: TASK-20260312-051
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Стандартизировать локальный quality decision artifact, чтобы решение по baseline/candidate было зафиксировано в одном понятном формате, а не оставалось только в текстовых обсуждениях.

## Scope
- In scope:
  - `RUNBOOK.md`
  - `OPERATOR_BASELINE.md`
  - `python_scripts/run_quality_gate.py` or adjacent local tooling only if needed
  - local artifact/decision format and path contract
- Out of scope:
  - изменение tracking runtime behavior
  - обучение новой модели
  - расширение GitHub/RTX automation как основного decision layer

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `RUNBOOK.md`
  - `OPERATOR_BASELINE.md`
  - `python_scripts/run_quality_gate.py`
  - existing evaluation outputs in `runs/evaluations/quality_gate/`
- Context:
  - локальный quality flow уже описан, но решение по candidate/baseline еще не имеет жесткого artifact contract.

## Implementation Steps
1. Определить один локальный decision artifact format/path для baseline/candidate decisions.
2. При необходимости минимально доработать local tooling или docs, чтобы этот contract был исполним.
3. Зафиксировать, как operator/developer читает и интерпретирует этот decision artifact.

## Acceptance Criteria
- [ ] Есть один явный local quality decision artifact contract
- [ ] Decision artifact можно связать с baseline/candidate flow без устной интерпретации
- [ ] Docs/tooling не противоречат этому contract

## Validation
- Commands:
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quality_gate.py --help`
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `rg -n "decision|quality gate|baseline|candidate" RUNBOOK.md OPERATOR_BASELINE.md python_scripts/run_quality_gate.py`
- Expected result:
  - decision artifact contract is explicit and traceable
  - tooling remains callable

## Risks
- Risk: standard будет описан только в docs, но не будет связан с фактическими gate outputs
- Mitigation: привязать contract к реальным local output paths or script flags
