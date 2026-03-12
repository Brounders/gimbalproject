# TASK: TASK-20260312-035-quality-gate-aggregate-fix

Task ID: TASK-20260312-035
Owner: Claude Mac
Priority: P1
Status: Accepted

## Goal
Исправить tooling quality-gate так, чтобы полный прогон regression pack снова давал завершенный aggregate result и не требовал ручной доборки недостающих клипов.

## Scope
- In scope:
  - `python_scripts/run_quality_gate.py`
  - при необходимости связанный benchmark/output handling в `python_scripts/run_offline_benchmark.py`
  - короткая воспроизводимая validation на current regression pack.
- Out of scope:
  - пересмотр quality thresholds;
  - изменение runtime tracking behavior;
  - изменение video pack content.

## Constraints
- Minimal reversible diff
- No runtime-wide rewrite
- Keep UI/business/runtime separation
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `python_scripts/run_quality_gate.py`
  - `python_scripts/run_offline_benchmark.py`
  - `configs/regression_pack.csv`
- Context:
  - candidate recheck produced incomplete per-clip outputs and no reliable aggregate artifact

## Implementation Steps
1. Найти причину неполного aggregate output.
2. Исправить сбор результатов так, чтобы quality-gate корректно обрабатывал весь pack.
3. Повторно прогнать full pack на short validation path и зафиксировать aggregate artifact.

## Acceptance Criteria
- [ ] Full regression pack produces aggregate JSON/CSV deterministically
- [ ] Не требуется ручная доборка missing clip
- [ ] Existing CLI behavior remains compatible

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `python3 python_scripts/run_quality_gate.py --pack-file configs/regression_pack.csv ...`
- Expected result:
  - aggregate output files created
  - per-clip coverage matches pack entries

## Risks
- Risk: фикс quality-gate заденет established benchmark flow
- Mitigation: менять только aggregate/output path, не runtime semantics
