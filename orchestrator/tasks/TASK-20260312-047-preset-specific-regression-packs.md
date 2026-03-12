# TASK: TASK-20260312-047-preset-specific-regression-packs

Task ID: TASK-20260312-047
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Разделить regression clips минимум на `day`, `night`, `ir`, чтобы локальный benchmark и quality-gate перестали скрывать preset-specific регрессии внутри одного общего агрегата.

## Scope
- In scope:
  - `configs/regression_pack.csv`
  - scene-aware pack files или equivalent config contract
  - `RUNBOOK.md`
  - при необходимости `python_scripts/run_offline_benchmark.py` и `python_scripts/run_quality_gate.py` только в части выбора pack/scenario
- Out of scope:
  - изменение runtime tracking logic
  - добавление новых клипов в `test_videos/`
  - новый training cycle

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `configs/regression_pack.csv`
  - `RUNBOOK.md`
  - `python_scripts/run_offline_benchmark.py`
  - `python_scripts/run_quality_gate.py`
- Context:
  - текущий общий regression pack мешает видеть, где именно ломается `day`/`night`/`ir`.

## Implementation Steps
1. Разделить regression contract на минимум три сценарных пакета: `day`, `night`, `ir`.
2. Обновить tooling/docs так, чтобы benchmark и quality-gate можно было запускать по конкретному pack/preset.
3. Зафиксировать это в `RUNBOOK.md` как канонический локальный evaluation flow.

## Acceptance Criteria
- [ ] Есть отдельные regression pack contracts для `day`, `night`, `ir`
- [ ] Benchmark/gate можно запускать по конкретному сценарию без ручной правки файлов
- [ ] Документация объясняет, когда использовать какой pack

## Validation
- Commands:
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_offline_benchmark.py --help`
  - `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quality_gate.py --help`
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
- Expected result:
  - per-scenario contract exists
  - help/compile still work

## Risks
- Risk: packs будут разведены формально, но tooling все равно останется завязанным на один общий csv
- Mitigation: acceptance считать выполненной только если tooling и docs реально отражают split
