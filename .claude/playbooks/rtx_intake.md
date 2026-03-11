# RTX Intake Playbook

## Когда использовать
- Human прислал статус RTX.
- Нужно понять: обучение идет, упало, было прервано, реально ли resume.
- Нужно принять решение: продолжать, остановить, повторить, принять артефакты.

## Обязательные поля статуса
- `status`
- `run_name`
- `run_dir`
- `checkpoint_used`
- `train_proc_count`
- `gpu_temp`
- `cpu_temp`
- `epochs_done_total`
- `epoch_current`
- `epoch_target`
- `epoch_progress_pct`
- `resume_mode`
- `exit_reason`
- `best_pt`
- `last_pt`
- `log_path`
- `download_url`
- `tail_log_20`

## Правила разбора
- `^C` в tail -> это `manual_interrupt`, а не обычный model failure.
- `train_proc_count=2` может быть нормальной парой `launcher + child`, это не всегда duplicate training.
- Решающий индикатор прогресса между сессиями: `epochs_done_total` из `results.csv`.
- Если лог выглядит как `1/N`, но `epochs_done_total` растет, нужно проверять, true ли это resume по факту run artifacts.
- Если CPU temp не читается, писать `cpu_temp=unavailable`, а не делать вывод, что перегрева нет.

## Что считать проблемой
- Нет `epochs_done_total`.
- Нет `exit_reason`.
- Неясно, resume или restart.
- `status=fail`, но хвост лога указывает на ручное прерывание.
