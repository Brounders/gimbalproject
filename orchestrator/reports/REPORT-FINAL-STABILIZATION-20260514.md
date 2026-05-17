# REPORT-FINAL-STABILIZATION-20260514

## Цель

Зафиксировать состояние проекта после перехода на QML-операторский слой, DTS-кандидатов и безопасный training loop, чтобы дальше работать в режиме дообучения модели без смешивания исходников и артефактов.

## Обязательные исходники текущего цикла

### QML runtime

- `app/main_qml.py`
- `app/qml/**`
- `app/qml_bridge/**`
- `app/state/operator_settings.json`
- `python_scripts/smoke_qml_mvp.py`

### DTS и обучение кандидата

- `app/training_desk_data.py`
- `app/training_desk_quality.py`
- `app/dts_candidate_gate.py`
- `app/dts_training_loop.py`
- `python_scripts/stage_operator_training_pack.py`
- `tests/test_training_desk_data.py`
- `tests/test_training_desk_quality.py`
- `tests/test_dts_candidate_gate.py`
- `tests/test_dts_training_loop.py`
- `tests/test_stage_operator_training_pack.py`

### Backend contract

- `src/uav_tracker/display/frame_result.py`
- `src/uav_tracker/domain/**`
- `src/uav_tracker/tracking/operator_workflow.py`
- `src/uav_tracker/pipeline.py`
- `app/workers.py`
- `app/qml_bridge/tracker_bridge.py`
- `tests/test_domain_telemetry.py`
- `tests/test_operator_workflow.py`
- `tests/test_operator_override.py`
- `tests/test_worker_operator_override.py`

## Артефакты, которые не должны попадать в git

- `models/candidates/**/*.pt`
- `models/candidates/**/*.hef`
- `models/candidates/**/*.zip`
- `.DS_Store`
- `__pycache__/`
- `.pytest_cache/`
- `.claude/worktrees/`
- `runs/`
- `datasets/`
- `tracker_env/`

## Текущий контракт кандидата

1. Оператор кликает цель на видео.
2. Backend создает operator-seeded candidate в DTS.
3. Оператор принимает запись в DTS.
4. `СОБРАТЬ` создает training pack из принятых записей.
5. `ОБУЧИТЬ` создает воспроизводимый training job, но не заменяет production-модель.
6. `СРАВНИТЬ` запускает smoke gate baseline vs candidate.
7. `ПРИНЯТЬ` сохраняет candidate в безопасную папку accepted только после PASS.
8. Production promotion разрешен только отдельным full gate day/night/ir.

## Следующий режим работы

После этой стабилизации основной фокус должен перейти на сбор новых кликов/кадров, подготовку training pack, обучение candidate и сравнение через gate. Новый UI-функционал добавлять только если он напрямую помогает сбору качественных данных или снижает риск принять плохую модель.
