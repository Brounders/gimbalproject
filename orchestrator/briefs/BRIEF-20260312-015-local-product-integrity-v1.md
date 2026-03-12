# BRIEF: BRIEF-20260312-015-local-product-integrity-v1

## Context
Аудит `REPORT-20260312-032` подтвердил, что проект уже работоспособен как локальный desktop tracker, но его локальная целостность страдает от трех практических дефектов: незафиксированный источник темы UI, зависимость preset-конфигов от эфемерных путей в `runs/`, и засоренный корень проекта legacy-файлами. Финальный продукт задуман как локальная программа; RTX/GitHub/web-инфраструктура рассматриваются только как временный вспомогательный слой.

## Objective
Укрепить локальный продукт как основной контур проекта: сделать тему UI честной и воспроизводимой, зафиксировать стабильный локальный baseline model path и очистить корень проекта/launch contract без поломки канонических entrypoints.

## Success Metrics
- Тема UI имеет явный и поддерживаемый source of truth в исходном коде.
- Рабочие preset-конфиги больше не зависят от случайных локальных путей внутри `runs/`.
- Корень проекта содержит понятные production entrypoints, а legacy-root scripts больше не вводят в заблуждение.

## Boundaries
- Must do:
  - работать только в локальном desktop-контуре проекта;
  - сохранить совместимость канонических запусков `main_tracker.py` и `tracker_gui.py`;
  - любые модельные пути делать стабильными для локальной программы, а не для web/RTX-конвейера.
- Must not do:
  - не расширять automation / GitHub / RTX tooling;
  - не делать большой рефактор `pipeline.py` и `main_gui.py` в этом цикле;
  - не менять `datasets/` и не запускать новый training cycle.

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- Three focused implementation tasks for local product integrity
- Updated local launch/model/theme contract in repo docs and code
- Review gate before opening deeper architecture refactor tasks
