# Приложение B — План реструктуризации и миграции

**Дата:** 2026-05-17
**Статус:** Draft / требует решения Human/Codex перед выполнением
**Цель:** упорядочить структуру репозитория без риска для runtime

---

## Принципы

1. Не переносить CORE файлы без полного compile + test гейта.
2. Сначала — безопасные шаги (rename/gitignore), потом — import-фиксы.
3. Каждый шаг должен быть отдельным коммитом с понятным сообщением.
4. Нельзя делать несколько структурных изменений в одном PR.

---

## Целевое дерево папок

```
GimbalProject/
├── src/
│   └── uav_tracker/          # Ядро трекера (без изменений)
│       ├── config.py
│       ├── pipeline.py       # Монолит → декомпозиция в Phase 3
│       ├── tracking/
│       ├── detectors/
│       ├── display/
│       ├── domain/
│       ├── runtime/
│       └── pipeline_control/
├── app/
│   ├── ui/                   # PySide6 виджеты (без изменений)
│   ├── qml_bridge/           # QML bridge (без изменений)
│   ├── qml/                  # QML файлы (без изменений)
│   ├── main_gui.py           # Монолит → декомпозиция в Phase 3
│   ├── main_qml.py
│   ├── main_cli.py
│   └── ...                   # Остальные app/*.py
├── tools/                    # NEW: переименовать python_scripts/ (Phase 2)
│   ├── evaluation/
│   ├── training/
│   ├── gt/                   # NEW: GT-инструменты
│   ├── diagnostics/          # NEW: диагностические скрипты
│   └── ...
├── configs/                  # Без изменений
├── tests/                    # Без изменений
├── models/                   # Без изменений
├── orchestrator/             # Без изменений
├── legacy/                   # Без изменений (явно устаревшее)
├── docs/                     # Без изменений
├── automation/               # Без изменений
├── ui_web/                   # Без изменений до решения Human/Codex
├── main_tracker.py           # Корневой entrypoint → оставить
├── tracker_gui.py            # Корневой entrypoint → оставить
├── pyproject.toml
├── requirements.txt
└── CLAUDE.md / AGENTS.md
```

---

## Phase 0 — Безопасные gitignore/cleanup шаги (без import-фиксов)

**Риск: МИНИМАЛЬНЫЙ. Нет изменений кода.**

### 0.1 Добавить configs/antiuav_02_1610_demo.yaml в gitignore или удалить

- Файл: `configs/antiuav_02_1610_demo.yaml`
- Доказательство устаревания: 0 ссылок в .py/.md/.yaml файлах
- Действие: добавить в .gitignore или удалить
- Риск: НИЗКИЙ — нет ссылок в коде

**Верификация:**
```bash
rg "antiuav_02_1610_demo" . --type py --type yaml --type md
# Должен вернуть 0 результатов
```

### 0.2 Проверить automation/state/ на актуальность

- `automation/state/artifact_manifest.json` — содержит Windows-пути, последнее обновление 2026-03-13
- `automation/state/dataset_registry.json` — Windows-пути, не обновлялся с 2026-03-12
- Действие: добавить комментарий к README что пути актуальны только для RTX-машины

**Риск: НУЛЕВОЙ — только документация**

---

## Phase 1 — Кандидаты на архив в python_scripts/

**Риск: НИЗКИЙ. Скрипты без тестов и без ссылок в активных задачах.**

Кандидаты для переноса в `python_scripts/archive/`:

| Файл | Обоснование |
|------|-------------|
| `diagnose_ir_hotspot_oracle.py` | 0 ссылок; нет тестов; функция покрыта build_detector_evidence_pack.py |
| `diagnose_ir_sensitivity.py` | 0 ссылок; нет тестов; покрыта аналогично |
| `monitor_six_hour_session.py` | 1 ссылка (BRIEF); специфичен для RTX сессий; не используется в Mac цикле |
| `summarize_batch_reports.py` | 1 ссылка; batch отчёты → заменён run_tracking_gt_diagnostics.py |
| `build_mixed_dataset.py` | 1 ссылка; смешанный dataset не используется в текущем weak4 цикле |

**Действие:** создать `python_scripts/archive/README.md` с пояснением, переместить файлы.
**НЕ удалять** — только архив.

**Верификация:**
```bash
python3 -m compileall -q python_scripts src app orchestrator tests
```

---

## Phase 2 — Переименование python_scripts/ → tools/ (NEEDS_OWNER_DECISION)

**Риск: СРЕДНИЙ. Требует обновления всех ссылок.**

Текущие внешние ссылки на `python_scripts`:
- `app/ui/training_desk.py` — вызывает `stage_operator_training_pack.py` через subprocess
- `orchestrator/reports/*.md` — упоминают пути
- `RUNBOOK.md` — содержит пути
- `.github/workflows/ci.yml` — `compileall` проверяет `python_scripts`

**Шаги (если одобрено):**
1. `git mv python_scripts tools`
2. Обновить `app/ui/training_desk.py` (строка с `str(self.root / 'python_scripts' / ...)`)
3. Обновить `pyproject.toml` если нужно
4. Обновить `.github/workflows/ci.yml`
5. Обновить RUNBOOK.md
6. Запустить compile check
7. Запустить pytest

**НЕ ДЕЛАТЬ** без явного разрешения Human/Codex.

---

## Phase 3 — Декомпозиция монолитов (NEEDS_OWNER_DECISION)

**Риск: ВЫСОКИЙ. Требует полного test гейта после каждого шага.**

### 3.1 pipeline.py: извлечь display функции

Уже задокументировано в `orchestrator/state/monolith_slicing_stage0.md`.
Цель: создать `src/uav_tracker/draw.py` с `draw_frame`, `_draw_target`, `_draw_active_reticle`.

**Оценка LOC до/после:**
- `pipeline.py` сейчас: ~57 KB / ~1400 строк (оценочно)
- После Phase 3.1: ~1260 строк

**Верификация:**
```bash
python3 -m compileall -q src
PYTHONPATH=src python3 -c "from uav_tracker.pipeline import TrackerPipeline; print('ok')"
python3 -m pytest tests/ -q --tb=short
```

### 3.2 pipeline.py: извлечь VideoSession + runner

Цель: создать `src/uav_tracker/runner.py`.
Оценка: pipeline.py → ~1010 строк.

### 3.3 main_gui.py: workers.py уже извлечён

`app/workers.py` уже содержит `TrackerWorker` и `EvaluationWorker` — это выполнено.

### 3.4 main_gui.py: дополнительная декомпозиция

Согласно `monolith_slicing_stage0.md` — operators, expert_dialog, stats — частично выполнено.
Текущий main_gui.py: ~32 KB (значительно меньше чем первоначальные 1783 строк).

---

## Phase 4 — ui_web/ решение (NEEDS_OWNER_DECISION)

**ui_web/ содержит TypeScript/React код (~26 файлов). Цель/интеграция неизвестны.**

Варианты:
1. **Принять как sub-project** — добавить README.md с описанием назначения
2. **Переместить в отдельный репозиторий** — если это standalone web UI
3. **Заморозить** — оставить как есть, добавить в .claudeignore

**Требует решения Human/Codex. Не трогать до решения.**

---

## Phase 5 — .gitignore audit

**Нужно проверить:**

| Риск | Элемент |
|------|---------|
| НИЗКИЙ | `automation/state/next_training_chunk.json` уже в .gitignore |
| НИЗКИЙ | `models/*.pt` уже в .gitignore |
| UNKNOWN | `configs/gt_minipack/generated/` — нет в .gitignore, но runtime создаёт файлы туда |
| UNKNOWN | `runs/` — уже в .gitignore |

**Действие для gt_minipack/generated/:**
```bash
rg "gt_minipack" .gitignore
# Если не найдено — добавить: configs/gt_minipack/generated/
```

---

## Сводная таблица приоритетов

| Phase | Действие | Риск | Статус |
|-------|----------|------|--------|
| 0.1 | Удалить/archive antiuav_02_1610_demo.yaml | НИЗКИЙ | Одобрить |
| 0.2 | Документировать automation/state/ | НУЛЕВОЙ | Одобрить |
| 1 | Архивировать 5 python_scripts | НИЗКИЙ | Одобрить |
| 2 | Переименовать python_scripts → tools | СРЕДНИЙ | NEEDS_OWNER_DECISION |
| 3.1 | Извлечь draw.py из pipeline.py | ВЫСОКИЙ | NEEDS_OWNER_DECISION |
| 3.2 | Извлечь runner.py из pipeline.py | ВЫСОКИЙ | NEEDS_OWNER_DECISION |
| 4 | ui_web/ решение | UNKNOWN | NEEDS_OWNER_DECISION |
| 5 | .gitignore audit | НИЗКИЙ | Одобрить |

---

## Верификационные команды (после каждой фазы)

```bash
# Компиляция
python3 -m compileall -q python_scripts src app orchestrator tests

# Импорт санити
PYTHONPATH=src python3 -c "
from uav_tracker.config import Config
from uav_tracker.pipeline import TrackerPipeline
from app.main_gui import MainWindow
print('imports ok')
"

# Тесты (требует PySide6 и зависимостей)
python3 -m pytest tests/ -q --tb=short

# QML санити
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 - << 'PY'
from PySide6.QtWidgets import QApplication
from app.main_gui import MainWindow
app = QApplication([])
win = MainWindow()
print(type(win).__name__, "ok")
PY
```

---

*Конец плана реструктуризации. Создано 2026-05-17.*
