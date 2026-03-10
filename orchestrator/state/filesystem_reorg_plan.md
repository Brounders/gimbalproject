# Filesystem Reorg Plan (Phased, Safe)

Дата: 2026-03-11. Источник: REPORT-20260311-008 (классификация).

## Принципы
- Никаких деструктивных операций в Phase 1.
- Каждый шаг содержит dry-run команду, rollback и критерий успеха.
- Физическое удаление только после явного Human-approve в Phase 3.
- datasets/, runs/, tracker_env/, src/, app/, main_tracker.py, tracker_gui.py — ЗАПРЕЩЕНО ТРОГАТЬ.

---

## Phase 1 — Аудит и верификация (только чтение, без перемещений)

### Шаг 1.1 — Верифицировать, что root-wrapper файлы не импортируются из runtime
**Цель:** убедиться, что `benchmark.py`, `real_tracker.py`, `tracker_final.py`,
`HYBRID_NIGHT_TRACKER.py`, `train_script.py` не используются активным кодом.

**Команда (dry-run, только анализ):**
```bash
grep -r "import benchmark\|from benchmark\|real_tracker\|tracker_final\|HYBRID_NIGHT\|train_script" \
  src/ app/ python_scripts/ main_tracker.py tracker_gui.py --include="*.py" -l
```
**Ожидаемый результат:** пустой вывод (нет импортов).

**Rollback:** N/A (только чтение).
**Критерий успеха:** ни один активный файл не импортирует эти скрипты.

### Шаг 1.2 — Верифицировать содержимое legacy/prototypes/ совпадает с root-wrappers
**Команда:**
```bash
ls legacy/prototypes/
# Ожидаем: benchmark.py real_tracker.py tracker_final.py HYBRID_NIGHT_TRACKER.py train_script.py train_script.py README.md
```
**Критерий успеха:** все 5 файлов присутствуют в legacy/prototypes/.

### Шаг 1.3 — Верифицировать safety_snapshots не нужны для rollback
**Команда:**
```bash
cat safety_snapshots/20260309_191915/status_before.txt
git log --oneline -5
```
**Критерий успеха:** текущее состояние repo совпадает или новее снапшота.

---

## Phase 2 — Минимальная очистка root (после P1 verification + Human approve)

### Шаг 2.1 — Удалить root-level compatibility wrappers
**Предусловие:** Шаг 1.1 и 1.2 пройдены.

**Команда:**
```bash
# Dry-run: проверить что файлы — только wrappers
head -3 benchmark.py real_tracker.py tracker_final.py HYBRID_NIGHT_TRACKER.py train_script.py

# Выполнение (только после approve):
git rm benchmark.py real_tracker.py tracker_final.py HYBRID_NIGHT_TRACKER.py train_script.py
git commit -m "chore: remove root-level compatibility wrappers (archived in legacy/prototypes)"
```
**Rollback:**
```bash
git revert HEAD
```
**Критерий успеха:**
- `python3 -m compileall -q src app python_scripts tests` — OK
- `./tracker_env/bin/python main_tracker.py --help` — OK
- `git status` чист

### Шаг 2.2 — Удалить пустую директорию arduino_sketches/
**Предусловие:** Убедиться, что пустая.

**Команда:**
```bash
ls arduino_sketches/  # должно быть пусто
git rm -r arduino_sketches/
git commit -m "chore: remove empty arduino_sketches dir"
```
**Rollback:** `git revert HEAD`
**Критерий успеха:** `ls arduino_sketches/` → `No such file or directory`

### Шаг 2.3 — Архивировать safety_snapshots/ (опционально)
**Решение:** оставить как есть OR:
```bash
tar -czf safety_snapshots_20260309.tar.gz safety_snapshots/
git rm -r safety_snapshots/
git add safety_snapshots_20260309.tar.gz
git commit -m "chore: archive safety_snapshots into tarball"
```
**Rollback:** `git revert HEAD && tar -xzf safety_snapshots_20260309.tar.gz`

---

## Phase 3 — Управление artifacts (только после Phase 2 + явного Human-approve)

### Шаг 3.1 — Очистка старых RTX unpacked artifacts
**Предусловие:** новый RTX artifact уже ingested и промотирован.

**Команда:**
```bash
# Dry-run: список старых unpacked
ls imports/rtx/unpacked/

# Выполнение:
rm -rf imports/rtx/unpacked/<old_run_name>
```
**Запрещено:** удалять последний successful artifact до нового intake.
**Критерий успеха:** `imports/rtx/unpacked/` содержит только актуальный artifact.

### Шаг 3.2 — Ротация logs/
**Команда:**
```bash
# Архивировать логи старше 30 дней
find logs/ -name "*.log" -mtime +30 -exec gzip {} \;
```
**Rollback:** `gunzip logs/*.gz`

---

## Запрещено трогать (во всех фазах)
- `datasets/` — любые удаления только с явного Human-approve + backup verify
- `runs/` — хранить все; очистка только через run_stable_cycle workflow
- `tracker_env/` — Python environment, не трогать
- `src/uav_tracker/` — core бизнес-логика
- `app/` — UI layer
- `main_tracker.py` — runtime entrypoint
- `tracker_gui.py` — GUI entrypoint
- `models/checkpoints/rtx_latest_best.pt` — текущий baseline

---

## Чек-лист для каждой операции Phase 2+
- [ ] `python3 -m compileall -q src app python_scripts tests` — OK
- [ ] `./tracker_env/bin/python main_tracker.py --help` — OK (нет краша)
- [ ] `git status` — нет unexpected untracked
- [ ] `PYTHONPATH=src ./tracker_env/bin/python -m unittest -q tests.test_target_manager_lock_policy tests.test_package_import` — OK
