# Project Physical Restructure Proposal

Дата статуса: 2026-05-17

Это итог TASK-20260517-113. Файлы не перемещались. Цель документа — дать схему,
по которой проект можно привести к порядку без поломки imports, tests, runbooks,
RTX sync и operator workflows.

## Принцип

Физическая реструктуризация делается только после proof и с compatibility
wrappers. Нельзя просто перенести `python_scripts/` или `configs/`, потому что
на эти пути ссылаются RUNBOOK, automation prompts, shell wrappers, tests и
человеческие workflows.

## Целевая карта

| Зона | Текущий статус | Целевое состояние |
|------|----------------|-------------------|
| `src/uav_tracker/` | Runtime package | Оставить runtime-only. Не складывать туда одноразовые scripts. |
| `app/` | Desktop UI runtime: QML primary + PySide6 fallback | Оставить как UI/runtime layer. QML primary зафиксирован в RUNBOOK. |
| `python_scripts/` | Смешаны gates, training, datasets, diagnostics, lifecycle | Оставить top-level CLI compatibility wrappers. Постепенно переносить реализацию в typed submodules или subfolders. |
| `python_scripts/evaluation/` | Уже существует | Сделать домом для reusable evaluation helpers, не обязательно CLI wrappers. |
| `python_scripts/training/` | Уже существует | Сделать домом для training helpers, но CLI entrypoints оставить совместимыми. |
| `python_scripts/tools/` | Уже существует | Использовать для shared script utilities. |
| `python_scripts/archive/` | Не создан | Создавать только после owner approval для low-risk research scripts. |
| `configs/` | Смешаны presets, regression packs, contracts, trackers | Разделять только через migration phase: `presets/`, `packs/`, `contracts/`, `trackers/`, `training/`. |
| `docs/` | Project docs + new stabilization policies | Оставить source-controlled docs. Runbooks можно выделить позже в `docs/runbooks/`. |
| `orchestrator/` | Execution authority and reports | Не смешивать с runtime docs. State/reports остаются authority layer. |
| `automation/state/` | Historical JSON plus active tooling paths | Сначала refresh/deprecation decision, потом физический move. |
| `ui_web/` | Buildable but unowned | Не переносить до owner decision. |

## Migration Order

### Phase 0 — Freeze and Gate

Перед любыми moves:

1. `python3 orchestrator/scripts/check_orchestration_state.py`
2. `python3 -m compileall -q python_scripts src app orchestrator tests`
3. `pytest -q`
4. `git diff --check`
5. documented rollback branch/commit.

### Phase 1 — Scripts Without Breaking Paths

1. Оставить существующие `python_scripts/*.py` как CLI entrypoints.
2. Для крупных scripts выделять reusable logic в existing subfolders:
   - `python_scripts/evaluation/`;
   - `python_scripts/training/`;
   - `python_scripts/tools/`.
3. Entry wrappers должны продолжать принимать те же CLI args.
4. После каждого wrapper split запускать targeted tests и `--help` smoke.

### Phase 2 — Config Split With Compatibility

Порядок будущего split:

1. `configs/presets/` — `default.yaml`, `night*.yaml`, `small_target.yaml`,
   `antiuav_thermal*.yaml`, `tracking_live_auto.yaml`, hardware presets.
2. `configs/packs/` — `regression_pack*.csv`, `action_policy_*_pack.csv`,
   `gt_*_pack*.csv`.
3. `configs/contracts/` — `problem_pack_gate_contract.json`,
   `promotion_contract.yaml`, `dataset_contract.yaml`.
4. `configs/trackers/` — оставить текущий tracker config subtree.

Move делать только после поиска всех references и добавления compatibility
resolution в scripts/config loader.

### Phase 3 — Archive With Proof

Archive candidates на входе:

- `python_scripts/diagnose_ir_hotspot_oracle.py`;
- `python_scripts/diagnose_ir_sensitivity.py`;
- `python_scripts/summarize_batch_reports.py`, если batch workflow признан dead;
- `python_scripts/monitor_six_hour_session.py`, если six-hour flow replaced.

Правило: archive move допустим только если `rg`, runbook review и owner decision
согласованы в отдельном report.

### Phase 4 — Automation State Decision

Для `automation/state/*.json` сначала выбрать:

1. refresh as current RTX automation state;
2. keep as historical evidence;
3. migrate to archive with compatibility notes.

Пока `training_conveyor.py`, publish/fetch scripts и automation prompts читают
эти paths, move запрещен.

## Validation Gates For Any Future Move

- `rg` по старому пути должен показать только compatibility wrapper/docs или
  expected references.
- `python3 -m compileall -q python_scripts src app orchestrator tests`
- `pytest -q`
- `python3 orchestrator/scripts/check_orchestration_state.py`
- CLI smoke for moved script: `python <wrapper> --help`
- Quality/tooling smoke when relevant:
  - `PYTHONPATH=src python python_scripts/run_quality_gate.py --help`
  - `PYTHONPATH=src python python_scripts/build_detector_evidence_pack.py --help`
  - `PYTHONPATH=src python python_scripts/run_tracking_gt_diagnostics.py --help`

## Rollback

Каждый physical move должен быть отдельным commit. Rollback path:

1. revert the move commit;
2. rerun validation gates;
3. leave the proof report intact if it still helps decision-making.

## Recommendation

Следующий практический шаг — не physical move. Сначала выполнить
TASK-20260514-093 commit boundary review, потому что ветка сильно ahead и нужно
понять, какие локальные commits/артефакты готовы к синхронизации, а какие должны
остаться локальными.
