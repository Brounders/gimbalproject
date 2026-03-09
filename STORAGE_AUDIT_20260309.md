# Аудит хранения и реорганизация (2026-03-09)

## 1) Текущий размер проекта
- Общий размер: **~26 ГБ** (`du -sh .`)
- Основные потребители:
  - `datasets/` — **~23 ГБ**
  - `tracker_env/` — **~2.3 ГБ**
  - `runs/` — **~258 МБ**
  - `test_videos/` — **~23 МБ**
  - `imports/` — **~20 МБ**
  - `models/` — **~16 МБ**

## 2) Что действительно нужно для работы приложения (runtime)
Минимально для запуска GUI/CLI и трекинга:
- `app/`, `src/`, `configs/`, `python_scripts/`, `main_tracker.py`, `tracker_gui.py`
- рабочая модель (`models/yolo11n.pt` или `runs/detect/runs/.../best.pt`)
- `tracker_env/` (или любое другое корректное venv)

**Не требуется для runtime напрямую:**
- `datasets/` (нужны только для обучения)
- `imports/` (временный импорт артефактов)
- большая часть `runs/` (превью-видео/логи)
- `test_videos/` (нужны для benchmark/демо, но не обязательны)

## 3) Список файлов/папок, не влияющих на runtime (кандидаты на очистку)

### A. Технический мусор (безрисково удалять)
- все `**/.DS_Store` (найдено 27 шт., ~268 КБ)

### B. Дубли артефактов (безрисково удалять после проверки)
- `imports/rtx/rtx_drone_first_6h_v2_20260309_081522.zip`
- `imports/rtx/rtx_drone_first_6h_v2_20260309_081522/`

Проверено: `best.pt`, `last.pt`, `results.csv` в `imports/rtx/...` и `models/checkpoints/...` имеют одинаковые SHA256.

### C. Архивы VisDrone (опционально, если распакованные папки остаются)
- `datasets/VisDrone/VisDrone2019-DET-train.zip` (~1.3 ГБ)
- `datasets/VisDrone/VisDrone2019-DET-test-dev.zip` (~297 МБ)
- `datasets/VisDrone/VisDrone2019-DET-val.zip` (~78 МБ)

### D. Legacy-обертки в корне (не участвуют в основном runtime)
- `HYBRID_NIGHT_TRACKER.py`
- `real_tracker.py`
- `tracker_final.py`
- `train_script.py`
- `benchmark.py`

Это совместимые deprecated-обертки на `legacy/prototypes/*`; на основной контур (`main_tracker.py`, `tracker_gui.py`) не влияют.

### E. Артефакты разработки (не влияют на runtime)
- `exports/changesets/vnext_smoothing_ir_gate_ui_20260309.patch`
- `safety_snapshots/` (служебные снимки состояния)
- превью/тест mp4 и временные логи в `runs/` (кроме нужных отчётов)

## 4) Критичный вывод по 26–28 ГБ
**Нет, не все 26–28 ГБ нужны.**
Почти весь объем — это обучающие данные и артефакты:
- `datasets` + `tracker_env` = ~25.3 ГБ

Если оставить только runtime-контур + одну модель + venv, проект может быть в районе **2.5–3 ГБ**.
Если venv тоже пересоздавать на лету — можно опуститься значительно ниже.

## 5) Риски перед удалением
1. `datasets/drone_bird_mendeley_ir_mix_v1/train.txt` содержит ссылки на внешний путь Desktop (`/Users/bround/Desktop/.../UAV_ir_Dataset`).
   - Этот mix уже не self-contained.
2. Удаление `datasets/drone_bird_yolo` и `datasets/antiuav_rgbt_ir_yolo` ломает текущие training-скрипты 6h-сессии.
3. Удаление `runs/detect/runs/drone_bird_probe_fast/weights/best.pt` сломает дефолтные профили, где этот путь задан как `model_path`.

## 6) Идеальная структура хранения (рекомендация)
Разделить код и тяжелые данные:

- Репозиторий (быстрый, легкий):
  - `app/`, `src/`, `configs/`, `python_scripts/`, docs
- Внешнее хранилище данных (вне git-дерева):
  - `/Users/bround/GimbalData/datasets/`
  - `/Users/bround/GimbalData/runs/`
  - `/Users/bround/GimbalData/imports/`
  - `/Users/bround/GimbalData/test_videos/`

Подключать через:
- env-переменные (`GIMBAL_DATA_ROOT`, `GIMBAL_MODELS_ROOT`) или
- симлинки (`datasets -> /Users/.../GimbalData/datasets`)

## 7) Практический план реорганизации
1. Короткосрочно (сразу):
   - удалить `.DS_Store`
   - удалить `imports/rtx/*` (дубликаты)
   - удалить zip-архивы VisDrone (если распакованные копии оставляем)
2. Среднесрочно:
   - вынести `datasets/` и `runs/` во внешний data-root
   - в `configs/*.yaml` оставить относительные/переменные пути
3. Долгосрочно:
   - оставить в репозитории только код + конфиги + обязательные малые smoke-видео

## 8) Оценка потенциальной экономии
- `.DS_Store` + imports + VisDrone zips: **~1.7–1.8 ГБ**
- Дополнительно при выносе `datasets/`: **~23 ГБ**
- Дополнительно при пересоздании `tracker_env`: **~2.3 ГБ**

Итого максимально: **~27 ГБ** (почти весь текущий объем).
