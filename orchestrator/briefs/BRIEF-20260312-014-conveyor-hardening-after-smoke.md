# BRIEF: BRIEF-20260312-014-conveyor-hardening-after-smoke

## Context
Первый smoke-run training conveyor через GitHub уже доказал, что связка RTX -> GitHub Release -> Mac intake работает. Следующий цикл нужен не для нового обучения, а для устранения системных дефектов, выявленных после первого chunk-run.

## Objective
Сделать training/eval conveyor достаточно устойчивым для регулярного использования: исправить неверную классификацию dataset scene profile, корректно блокировать неполные датасеты и восстановить полный aggregate output в quality-gate.

## Success Metrics
- Dataset registry больше не маркирует `drone-bird-yolo` как `ir`.
- Неполные dataset-каталоги не попадают в `ready`, а получают блокирующий статус с понятной причиной.
- `run_quality_gate.py` снова выдает полный aggregate artifact по regression pack без ручной доборки недостающих клипов.

## Boundaries
- Must do:
  - правки только в conveyor/eval/tooling слое;
  - сохранить уже работающий smoke-run flow;
  - не ломать existing manifests и ledger.
- Must not do:
  - не менять operator runtime и UI;
  - не запускать новый RTX training cycle в этом цикле;
  - не менять `datasets/`, `runs/`, `tracker_env/`.

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- Three focused implementation tasks
- Validation plan for conveyor and quality-gate
- Review gate on Mac before any scheduled automation is enabled
