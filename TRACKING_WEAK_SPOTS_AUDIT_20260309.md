# Аудит слабых мест трекинга и детекции (2026-03-09)

## Цель
Выявить реальные узкие места в боевом контуре трекинга/детекции на текущем коде без изменения модели.

## Проверено
- Статический разбор ядра: `pipeline`, `target_manager`, `night_detector`, UI state.
- Короткий офлайн-бенч:
  - `test_videos/drone_closeup_mixkit_44644_360.mp4`
  - `test_videos/night_ground_large_drones.mp4`
  - `test_videos/IR_DRONE_001.mp4`
- Дополнительная форензика по источнику активной цели (`active.source`) на каждом клипе.

## Критичные проблемы (P0)

### P0.1 `TRACK` может означать не lock, а сопровождение шумовой night-цели
- Симптом:
  - На ночных/IR клипах режим часто `TRACK`, но `lock_event_counts` остаются нулевыми.
  - `active.source` в основном `night` (класс `-1`), а не `yolo/local/lock`.
- Подтверждение:
  - `night_ground_large_drones`: `active_source_counts {'night': 222}`, `focus_frames 0`, `mode_counts {'TRACK': 206}`.
  - `IR_DRONE_001`: `active_source_counts {'night': 182, 'roi': 54}`, `focus_frames 0`, `mode_counts {'TRACK': 215}`.
- Причина в коде:
  - `TRACK` считается по наличию `active` + grace, а не по подтвержденному drone-lock:
    - `src/uav_tracker/pipeline.py` (метод `_update_tracking_state`).
  - UI транслирует `TRACK` в состояние `LOCK`:
    - `app/main_gui.py` (блок `_update_stats`, ветка `tracker_mode == 'TRACK'`).

### P0.2 Ложная активная цель может удерживаться из night-контура
- Симптом:
  - Высокий `active_id_changes_per_min` на ночном клипе (`48.93/min`).
  - Часть треков формируется только из night-детекций без классовой валидации.
- Причина в коде:
  - `update_from_night` создает/ведет цели без проверки класса (`cls_id=-1`) и без жесткого барьера на выбор active:
    - `src/uav_tracker/tracking/target_manager.py`.
  - `select_active` допускает выбор непервичных источников, если нет лучшего primary.

### P0.3 Метрика `false_lock_rate` некорректна на клипах без GT
- Симптом:
  - На роликах без разметки GT `false_lock_rate` почти равна `active_presence_rate` (до 1.0).
- Причина в коде:
  - В `evaluation.py` любой active кадр без GT считается false_lock:
    - `src/uav_tracker/evaluation.py` (условие при `not gt_visible`).
- Риск:
  - Система качества может отвергать рабочие улучшения из-за неверной метрики на unlabelled видео.

## Средний приоритет (P1)

### P1.1 Разрыв между состояниями ядра и UI
- В ядре канон `SCAN/TRACK/LOST`, в UI используется `RUNNING/LOCK/LOST/...`.
- Сейчас `TRACK` в UI визуально равен lock-состоянию, что вводит оператора в заблуждение.

### P1.2 ROI/night контуры могут дублировать или перехватывать объект
- В `update_from_roi_yolo` привязка к существующим ROI-трекам ограничена `sources={'roi'}`.
- Это может плодить параллельные ID и ухудшать стабильность при слабом overlap с primary.

## Низкий приоритет (P2)

### P2.1 Сильная зависимость от preset-порогов для night-контуров
- При текущих `night_*` порогах (preset `night`) night-контур часто доминирует, когда primary слаб.
- Это повышает вероятность ложного `TRACK` при шумном фоне.

## Фактические метрики (короткий бенч)
- Файл: `runs/evaluations/benchmark/audit_20260309_benchmark_night.csv`
- Ключевые значения:
  - `drone_closeup`: lock_rate `0.9965`, idchg/min `0.00`, false_lock `1.0` (без GT)
  - `night_ground_large_drones`: lock_rate `0.7153`, idchg/min `48.93`, false_lock `0.7708`
  - `IR_DRONE_001`: lock_rate `0.7143`, idchg/min `5.98`, false_lock `0.7841`

## Рекомендуемый порядок исправлений
1. Разделить понятия:
   - `TRACK` (есть сопровождение) и `LOCK` (подтвержденный drone-lock).
2. Запретить UI показывать `LOCK`, если lock-контур не подтвержден (`focus_mode == False` и нет lock-событий).
3. Ужесточить выбор active:
   - приоритет `primary` над `night`;
   - ограничить автозахват night-целей без подтверждения primary.
4. Исправить оценку:
   - считать `false_lock_rate` только на клипах с GT;
   - для unlabelled клипов использовать отдельный индикатор (например `unverified_active_rate`).

