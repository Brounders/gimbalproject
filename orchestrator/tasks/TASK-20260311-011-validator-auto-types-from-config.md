# TASK: TASK-20260311-011-validator-auto-types-from-config

Task ID: TASK-20260311-011
Owner: Claude Mac
Priority: P2
Status: Open

## Goal
Устранить дублирование типовых правил в `validate_profile_presets.py`:
заменить ручной `_TYPE_RULES` на авто-вывод типов из `dataclasses.fields(Config)`.

Текущая проблема: `_TYPE_RULES` содержит ~80 пар `key → (type,)`, скопированных
вручную из `Config`. При добавлении нового поля в `Config` валидатор не обновляется
автоматически → риск ложных PASS при неверном типе в YAML.

## Scope
- In scope:
  - изменить `validate_profile_presets.py`: добавить функцию `_build_type_rules_from_config()`
    которая читает `Config` через `dataclasses.fields()`, берёт тип поля (через type hints),
    строит `{yaml_key: (python_type,)}` маппинг;
  - удалить или значительно сократить ручной `_TYPE_RULES`;
  - обновить тесты в `tests/test_validate_profile_presets.py` если изменится интерфейс.
- Out of scope:
  - изменение `Config`, `profile_io.py`, runtime-кода.
  - GUI, CLI поведение валидатора не меняется.

## Constraints
- Без новых зависимостей (только stdlib: `dataclasses`, `typing`).
- Нельзя импортировать `cv2`, `ultralytics`, `torch` транзитивно.
- Если `Config` недоступен (нет PYTHONPATH), валидатор должен деградировать
  до проверки только unknown keys (type check пропускается с предупреждением).
- Поведение CLI (флаги, exit codes, stdout формат) не меняется.

## Inputs
- `python_scripts/validate_profile_presets.py`
- `tests/test_validate_profile_presets.py`
- `src/uav_tracker/config.py` — источник типовой схемы
- `src/uav_tracker/profile_io.py` — маппинг yaml_key → Config_attr

## Implementation Hint
`profile_io.py` содержит `mapping: dict[str, str]` — `{yaml_key: CONFIG_ATTR}`.
`Config` — датакласс с typed fields. Алгоритм:
1. Загрузить маппинг из `profile_io.py` через ast (уже есть extract_mapping_keys).
2. Также через ast (или optional import) получить `{CONFIG_ATTR: python_type}`.
3. Построить обратный маппинг `{CONFIG_ATTR: yaml_key}`.
4. Для каждого field в Config — найти yaml_key через обратный маппинг → добавить в type rules.
5. Обработать `Optional[T]`, `Union[T, None]` через `typing.get_args()`.

Если `import Config` завершается ошибкой — продолжить без type-check, вывести warning.

## Validation
- `python3 -m compileall -q python_scripts src app tests`
- `PYTHONPATH=src ./tracker_env/bin/python -m unittest -v tests.test_validate_profile_presets`
- `PYTHONPATH=src ./tracker_env/bin/python python_scripts/validate_profile_presets.py --configs-dir configs`
  → должен выдавать `OK: 10 preset(s) valid.`
- Без PYTHONPATH: warning + продолжение без type-check.

## Acceptance Criteria
- [ ] `_TYPE_RULES` удалён или сокращён до edge-cases.
- [ ] Авто-вывод типов работает при наличии `PYTHONPATH=src`.
- [ ] Graceful degradation при отсутствии `PYTHONPATH`.
- [ ] Все 10 пресетов проходят валидацию.
- [ ] Тесты зелёные.
