# Quality Gate Playbook

## Когда использовать
- Нужно сравнить baseline и candidate.
- Нужно решить, можно ли принимать новую модель/пресет.
- Нужно интерпретировать benchmark/KPI.

## Базовые принципы
- Не принимать candidate только потому, что улучшилась одна усредненная метрика.
- Приоритет: стабильность lock/ID, затем ложные lock, затем FPS.
- Если ключевой KPI деградировал, решение по умолчанию: `RETUNE` или `FAIL`, не `PASS`.

## Рабочий контур
- `python_scripts/run_quick_kpi_smoke.py` — быстрый smoke, если есть.
- `python_scripts/run_offline_benchmark.py` — офлайн пакет.
- `python_scripts/run_quality_gate.py` — решение baseline vs candidate.

## Формат решения
- `PASS` — candidate безопасен к приему.
- `FAIL` — candidate отклонен.
- `RETUNE` — candidate частично promising, но unsafe для приема.
