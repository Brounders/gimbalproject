# Реестр python_scripts

Дата статуса: 2026-05-17

`python_scripts/` — это набор рабочих инструментов проекта, а не runtime-пакет.
Источник права на запуск — `orchestrator/state/active_plan.md`; скрипты отсюда
нужно запускать только когда активная задача или runbook явно называют workflow.

## Правила работы

- Не запускать долгие обучения из этой папки, если `open_training.md` или
  активная задача явно не разрешают обучение.
- `runs/**`, contact sheets, model artifacts и локальные caches считать
  выходными артефактами, а не источником правды.
- Не удалять и не перемещать скрипты только из-за малого числа ссылок. Сначала
  нужна proof-table в TASK-20260517-111.
- Если есть готовый wrapper, использовать его вместо разовых команд.

## Реестр

| Зона | Скрипты | Текущий статус | Примечание |
|------|---------|----------------|------------|
| Quality gates | `run_quality_gate.py`, `run_quick_kpi_smoke.py`, `run_problem_pack_gate.py`, `run_action_policy_gate.py`, `compare_kpi_snapshots.py` | Active | Основные regression/smoke entry points. Держать в `RUNBOOK.md`. |
| Offline tracking eval | `run_offline_benchmark.py`, `run_model_battle.py`, `run_scenario_sweep.py`, `run_ultralytics_tracking_eval.py` | Active/research | Сравнение tracker/model. Запускать только с явным pack/task. |
| Target Lab / GT diagnostics | `run_tracking_gt_diagnostics.py`, `validate_tracking_gt.py`, `import_regression_pack_gt.py`, `build_detector_evidence_pack.py`, `build_gt_yolo_pack.py`, `render_yolo_pack_contact_sheets.py`, `render_ir_detection_contact_sheets.py` | Active | На них держится текущий tracker-evolution loop. |
| Dataset preparation | `dataset_audit.py`, `convert_antiuav_rgbt_to_yolo.py`, `sanitize_yolo_pairs.py` | Active | Безопасная инспекция и конвертация данных. |
| Dataset preparation candidates | `build_mixed_dataset.py` | Needs proof | Кандидат на архив из аудита; не двигать и не удалять до TASK-20260517-111. |
| Training control | `train_yolo_from_yaml.py`, `train_drone_bird.py`, `training_conveyor.py`, `check_training_status.py`, `watch_training_progress.py` | Active/controlled | RTX/local training должен идти только по активному training contract. |
| Long-run shell wrappers | `run_six_hour_training_*.sh` | Active/legacy controlled | Сохранить до замены или явного признания obsolete в RTX workflow. |
| Long-run monitor candidates | `monitor_six_hour_session.py` | Needs proof | Кандидат на архив; сначала проверить ссылки и owner. |
| Operator annotations / DTS | `export_operator_annotations_to_yolo.py`, `stage_operator_training_pack.py`, `replay_frame_telemetry.py` | Active | Материал от оператора, DTS и telemetry replay. |
| Model lifecycle | `run_intake.py`, `install_baseline.py`, `fetch_training_artifact.py`, `publish_training_artifact.py`, `verify_baseline.py` | Active/controlled | Promotion/artifact movement — gated workflow, не casual utility. |
| Diagnostics | `build_diagnostics_report.py`, `run_backend_parity.py` | Active | Отчеты и parity checks. |
| IR diagnostic candidates | `diagnose_ir_hotspot_oracle.py`, `diagnose_ir_sensitivity.py` | Needs proof | Кандидаты на архив; держать до proof-table TASK-20260517-111. |
| Batch helpers | `run_dataset_batch.py` | Active/research | Batch execution helper. |
| Batch helper candidates | `summarize_batch_reports.py` | Needs proof | Кандидат на архив; проверить ссылки перед move/delete. |
| QML smoke | `smoke_qml_mvp.py` | Active | UI sanity helper для QML flow. |

## Открытые вопросы владения

- Какие training scripts останутся каноническими после финализации RTX sync?
- Какие research-only diagnostics нужно перенести в archive/tools?
- Какие wrappers нужно поднять до documented runbook commands?

Эти вопросы относятся к TASK-20260517-111 и следующим этапам stabilization.
