# Codex Automations Conveyor

Этот каталог фиксирует первый рабочий контур автоматизации обучения и intake для GimbalProject.

## Что здесь хранится
- `state/dataset_registry.json` — реестр найденных датасетов на RTX.
- `state/training_ledger.json` — учет прогресса по каждому датасету.
- `state/artifact_manifest.json` — опубликованные training artifacts и их GitHub URLs.
- `state/decision_log.json` — решения Mac-side intake (`promote`, `hold_and_tune`, `reject`).
- `prompts/rtx_training_chunk.md` — шаблон prompt для Codex App Automation на RTX.
- `prompts/mac_intake_gate.md` — шаблон prompt для intake/gate на Mac.

## Принятые правила
- Бинарные артефакты (`.pt`, `.zip`) не попадают в `main`.
- `main` хранит только manifests, ledger и решения.
- Один automation run = один dataset chunk.
- Один intake run = один artifact.
- Источник истины по датасетам — `training_ledger.json`, а не память чата.

## Почему именно так
Официальная документация Codex подтверждает три ключевых факта:
- Codex app `Automations` работают локально в приложении; app должен быть запущен, а project — доступен на диске.
- В Git-репозиториях automation runs используют отдельные background worktrees.
- Для повторяемых сценариев действует правило: skills define the method, automations define the schedule.

Ссылки:
- Codex Automations: https://developers.openai.com/codex/app/automations/
- Best practices / automations: https://developers.openai.com/codex/learn/best-practices/#use-automations-for-repeated-work
- Codex App Server note about CI/jobs: https://developers.openai.com/codex/app-server/

## Шаг 1. Подготовка RTX
1. Открыть проект `GimbalProject` в Codex app на RTX.
2. Убедиться, что Codex app на RTX залогинен и может делать `git pull` / `git push`.
3. Установить GitHub CLI `gh` и выполнить `gh auth login`.
4. Инициализировать state:

```bash
./tracker_env/bin/python python_scripts/training_conveyor.py init --state-dir automation/state
```

5. Просканировать папку с датасетами:

```bash
./tracker_env/bin/python python_scripts/training_conveyor.py scan \
  --dataset-root "C:/Users/PC/Desktop/Обучение" \
  --state-dir automation/state
```

## Шаг 1.1. Создание automation в Codex App на RTX
1. Открыть Codex App -> `Automations` -> `New automation`.
2. Выбрать project `GimbalProject`.
3. Оставить Git mode с отдельным background worktree.
4. Разрешения дать не ниже тех, которые нужны для:
   - `git pull` / `git push`
   - запуска Python
   - сети
   - работы `gh`
5. Открыть `automation/prompts/rtx_training_chunk.md`.
6. Перед вставкой в automation prompt вручную заменить:
   - `{{DATASET_ROOT}}`
   - `{{BASE_CHECKPOINT}}`
   - `{{CHUNK_EPOCHS}}`
7. Вставить уже подставленный prompt в automation.
8. Для первого этапа поставить cadence:
   - либо `Manual`
   - либо редкий повторяемый запуск, который ты контролируешь.
9. Первые несколько запусков смотреть руками через `Automations -> Triage`.

## Шаг 2. Выбор следующего dataset chunk

```bash
./tracker_env/bin/python python_scripts/training_conveyor.py next-chunk \
  --state-dir automation/state \
  --base-checkpoint "runs/detect/runs/rtx_drone_stability_12h_v1/weights/best.pt" \
  --chunk-epochs 12 \
  --write-plan automation/state/next_training_chunk.json \
  --claim
```

Что делает команда:
- берет только датасеты, готовые к обучению (`dataset.yaml` найден);
- исключает архивы и неполные директории;
- учитывает уже пройденные эпохи по ledger;
- предлагает ровно один следующий chunk.

## Шаг 3. Обучение chunk
Automation на RTX должна использовать `automation/state/next_training_chunk.json` как источник:
- `dataset_yaml_path`
- `base_checkpoint`
- `suggested_run_name`
- `target_total_epochs`

Дальше запускается существующий `python_scripts/train_yolo_from_yaml.py`.

Важно:
- automation сама не должна заново изобретать training command;
- prompt должен направлять ее к уже существующим script и state files;
- один automation run = один dataset chunk.

## Шаг 4. Публикация artifact в GitHub
После завершения chunk:

```bash
./tracker_env/bin/python python_scripts/publish_training_artifact.py \
  --zip "exports/<artifact>.zip" \
  --repo "Brounders/gimbalproject" \
  --artifact-id "<artifact_id>" \
  --run-name "<run_name>" \
  --dataset-id "<dataset_id>" \
  --checkpoint-path "<last_or_best_checkpoint>" \
  --epoch-from <from_epoch> \
  --epoch-to <to_epoch>
```

Скрипт:
- загружает zip в GitHub Release `training-artifacts`;
- добавляет запись в `artifact_manifest.json`.

## Шаг 5. Фиксация progress по dataset

```bash
./tracker_env/bin/python python_scripts/training_conveyor.py record-run \
  --state-dir automation/state \
  --dataset-id "<dataset_id>" \
  --run-name "<run_name>" \
  --epochs-done-total <epoch_total_for_dataset> \
  --last-checkpoint "<checkpoint_path>" \
  --artifact-id "<artifact_id>" \
  --status published
```

## Шаг 6. Intake на Mac
Сначала скачать последний published artifact:

```bash
./tracker_env/bin/python python_scripts/fetch_training_artifact.py \
  --manifest automation/state/artifact_manifest.json \
  --output-dir imports
```

Затем benchmark + quality gate с `--model` override.

После решения записать verdict:

```bash
./tracker_env/bin/python python_scripts/training_conveyor.py record-decision \
  --state-dir automation/state \
  --artifact-id "<artifact_id>" \
  --decision hold_and_tune \
  --reason "false_lock regression on night/noise clips"
```

## Шаг 6.1. Создание automation в Codex App на Mac
Это второй этап, не обязательный для первого запуска конвейера.

1. Открыть Codex App -> `Automations` -> `New automation`.
2. Выбрать тот же project `GimbalProject`.
3. Открыть `automation/prompts/mac_intake_gate.md`.
4. При необходимости вписать конкретные benchmark/gate команды проекта без placeholder-синтаксиса.
5. Запускать либо вручную, либо по отдельному cadence после завершения RTX chunk.

На первом этапе допустимо, чтобы intake на Mac запускался вручную обычной командой, а не automation.

## Текущее ограничение
Это первый production-like scaffold, а не окончательный автономный комбайн.

Что уже автоматизируем:
- dataset registry
- training ledger
- artifact manifest
- GitHub Release delivery
- Mac intake download path

Что еще будет усилено в следующей фазе:
- автоматический publish/commit loop внутри Codex Automation
- более умный dataset budgeting
- optional separate artifact repo / release hygiene
- optional second automation на Mac для intake/gate
