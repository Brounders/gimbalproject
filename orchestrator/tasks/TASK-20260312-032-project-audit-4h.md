# TASK: TASK-20260312-032-project-audit-4h

Task ID: TASK-20260312-032
Owner: Claude Mac
Priority: P1
Status: Open

## Goal
Провести полный инженерный аудит проекта GimbalProject с бюджетом времени до 4 часов и выдать рабочий план дальнейшей эволюции на основе фактов из кода, workflow и файловой системы.

## Scope
- In scope:
  - архитектура проекта от идеи до текущей реализации;
  - runtime tracking layer, UI layer, training/eval layer, orchestration layer;
  - файловая система и жизненный цикл артефактов;
  - запускные точки, validation flow, benchmark/quality-gate flow;
  - сильные стороны, слабые точки, противоречия, технический долг;
  - итоговый roadmap с приоритетами.
- Out of scope:
  - любые изменения runtime/UI/training кода;
  - рефакторы;
  - создание новых implementation tasks в этом цикле;
  - правки `tracker_env/`, `datasets/`, `runs/`.

## Constraints
- No code changes to runtime/UI/training files
- Analysis only; no implementation
- Full command/tool access for this session without asking Human between steps
- Non-destructive git only
- Minimal repo noise
- Keep UI/business/runtime separation in recommendations
- If plugin auto-activation matters, use exact trigger words instead of synonyms:
  - Context7: `как использовать`, `документация`, `пример кода`, `API`, `версия`, `how to use`, `docs`, `latest API`, `library reference`, `sdk`, `library`, `dependency`, `docs`, `api`, `integration`
  - Frontend-design: `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Inputs
- Files:
  - `AGENTS.md`
  - `PROJECT_ARCHITECTURE.md`
  - `RUNBOOK.md`
  - `DEVELOPMENT_NEXT_STEPS.md`
  - `orchestrator/state/*`
  - `orchestrator/tasks/*`
  - `orchestrator/reports/*`
  - `src/`
  - `app/`
  - `python_scripts/`
  - `configs/`
- Context:
  - stabilization-first project phase
  - day/night/IR UAV tracking mission
  - current baseline model and training conveyor already exist

## Implementation Steps
1. Build a repository inventory and identify canonical entrypoints, major layers, and lifecycle zones.
2. Audit architecture boundaries:
   - UI vs business logic
   - runtime vs IO
   - training vs evaluation
   - orchestration vs execution
3. Audit execution workflows:
   - operator startup flow
   - training/evaluation flow
   - GitHub/orchestration flow
   - Codex automation flow
4. Audit filesystem structure:
   - canonical vs legacy vs derived directories
   - artifact placement
   - ambiguity and technical debt hotspots
5. Produce one report with:
   - strengths
   - prioritized findings (`P0/P1/P2`)
   - contradictions/risks
   - recommended roadmap

## Acceptance Criteria
- [ ] A single primary audit report exists at `orchestrator/reports/REPORT-20260312-032.md`
- [ ] Report covers architecture, execution workflows, and filesystem structure
- [ ] Findings are evidence-based and prioritized (`P0/P1/P2`)
- [ ] Report includes a concrete next-step roadmap
- [ ] No runtime code is modified in this cycle

## Validation
- Commands:
  - `python3 -m compileall -q python_scripts src app orchestrator tests`
  - `bash -lc 'if command -v pytest >/dev/null 2>&1 && find . -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then pytest -q; else echo "No pytest suite configured"; fi'`
  - inspection commands as needed: `git status`, `git log`, `rg`, `find`, `du`, `ls`, `sed`, `cat`
- Expected result:
  - validation commands still pass
  - report exists and is reviewable
  - no unintended code diff outside report/state artifacts

## Risks
- Risk: audit becomes too broad and turns into vague commentary
- Mitigation: one primary report, prioritized findings, explicit roadmap
- Risk: accidental implementation during analysis
- Mitigation: keep scope analysis-only and reject code changes
