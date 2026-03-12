# legacy/

Архив скриптов, которые не являются частью production launch workflow.

Эти файлы присутствовали в корне проекта на ранних этапах разработки, но не относятся
к каноническим точкам запуска desktop-программы.

## Содержимое

| Файл | Описание |
|------|----------|
| `benchmark.py` | M1 matmul + YOLO performance benchmark (разовый инструмент) |
| `real_tracker.py` | Ранний прототип camera tracker (до архитектуры `src/uav_tracker/`) |
| `train_script.py` | Ранний training harness (заменён `python_scripts/train_yolo_from_yaml.py`) |

## Канонические точки входа

Используйте вместо этих файлов:

- `tracker_gui.py` — GUI (`app/main_gui.py`)
- `main_tracker.py` — CLI (`app/main_cli.py`)

Подробности: [RUNBOOK.md](../RUNBOOK.md)
