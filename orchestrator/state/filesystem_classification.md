# Filesystem Classification Matrix

Дата: 2026-03-11. Источник: REPORT-20260311-007 + REPORT-20260311-008.

## Классы

### `core` — Runtime критично, не трогать без задачи
| Путь | Описание | Допустимые операции |
|---|---|---|
| `src/uav_tracker/` | Вся бизнес-логика трекера | Только через task/Claude |
| `app/` | GUI + CLI оболочки | Только через task/Claude |
| `main_tracker.py` | Основной runtime entrypoint | Нельзя перемещать/удалять |
| `tracker_gui.py` | GUI entrypoint | Нельзя перемещать/удалять |
| `configs/*.yaml` | Операторские пресеты | Изменять только через task |

### `training-tools` — Инструментарий, изменения через task
| Путь | Описание | Допустимые операции |
|---|---|---|
| `python_scripts/` | Все скрипты (benchmark, quality-gate, training, tooling) | Изменения через task |
| `configs/training_curriculum.yaml` | Plan curriculum для RTX | Изменения через task |
| `configs/regression_pack*.csv` | Regression baseline | Изменения через task |

### `datasets-artifacts` — Данные, не удалять без согласования
| Путь | Размер | Допустимые операции |
|---|---|---|
| `datasets/` | 22.9 GB | Никогда не удалять; archive только с явного Human |
| `runs/` | 252.6 MB | Хранить; очистка только старых runs по согласованию |
| `models/` | 112.1 MB | Хранить; checkpoint management через ingest workflow |
| `imports/` | 259.8 MB | Хранить после intake; старые unpacked можно архивировать |

### `observability` — Аналитические артефакты, безопасно читать/писать
| Путь | Описание | Допустимые операции |
|---|---|---|
| `orchestrator/` | Tasks, reports, briefs, state | Полный доступ для Codex/Claude |
| `logs/` | Runtime и training логи | Читать; ротация приемлема |
| `test_videos/` | Тестовые клипы | Читать; добавление новых OK |

### `legacy` — Устаревшее, кандидаты на архивирование
| Путь | Описание | Риск удаления |
|---|---|---|
| `legacy/prototypes/` | Оригинальные прото-скрипты | Низкий (уже заархивированы) |
| `legacy/changesets/` | Cleanup patch artifacts | Низкий |
| `safety_snapshots/` | Git-patch снапшоты перед cleanup | Низкий (можно удалить после verification) |

### `candidate-cleanup` — Можно убрать после P1 верификации
| Путь | Описание | Статус |
|---|---|---|
| `benchmark.py` (root) | Compatibility wrapper → `legacy/prototypes/benchmark.py` | Безопасно убрать после P1 |
| `real_tracker.py` (root) | Compatibility wrapper → `legacy/prototypes/real_tracker.py` | Безопасно убрать после P1 |
| `tracker_final.py` (root) | Compatibility wrapper → `legacy/prototypes/tracker_final.py` | Безопасно убрать после P1 |
| `HYBRID_NIGHT_TRACKER.py` (root) | Compatibility wrapper → `legacy/prototypes/` | Безопасно убрать после P1 |
| `train_script.py` (root) | Compatibility wrapper → `legacy/prototypes/train_script.py` | Безопасно убрать после P1 |
| `arduino_sketches/` | Пустая директория | Безопасно убрать |

## Запрещено трогать (абсолютно)
- `datasets/` — любые операции удаления без явного Human-approve
- `runs/detect/` — текущие тренировочные артефакты, baseline модели
- `tracker_env/` — Python environment (не в дереве инвентаризации, исключён из skip-list)
- `main_tracker.py`, `tracker_gui.py` — runtime entrypoints
- `src/uav_tracker/` — вся бизнес-логика

## Сводка по риску
| Класс | Кол-во путей | Риск | Объём |
|---|---|---|---|
| core | 5 | HIGH | ~500 KB |
| training-tools | 3 | MEDIUM | ~5 MB |
| datasets-artifacts | 4 | HIGH (объём) | ~23.6 GB |
| observability | 3 | LOW | ~2 MB |
| legacy | 2 | LOW | ~1 MB |
| candidate-cleanup | 6 | LOW | ~20 KB |
