# REPORT-TRACKERS-EXPANDED-PACK-20260501

**Task:** TASK-20260501-ALG001-INTEGRATE-EVIDENCE-V1 (продолжение — measurement run)
**Date:** 2026-05-01
**Status:** Measurement run complete · all native trackers rejected as self-hold replacement

---

## 1. Использованные клипы

### `configs/regression_pack.csv` (14 клипов)

| Категория | N | Клипы |
|-----------|---|-------|
| day   | 3 | `drone_closeup_mixkit_44644_360`, `dataset_mendeley_f1_1_EO_dji_mavic_2_range_close`, `drone_detection_V_DRONE_001` |
| night | 3 | `night_ground_large_drones`, `antiuav_rgbt_20190925_193610_1_1_visible`, `antiuav_rgbt_20190925_200805_1_2_visible` |
| ir    | 4 | `Demo_IR_DRONE_146`, `IR_DRONE_001`, `dataset_mendeley_f1_1_IR_dji_mavic_2_range_close`, `antiuav_rgbt_20190925_200805_1_2_infrared` |
| noise | 4 | `IR_BIRD_001`, `night_ground_indicator_lights`, `drone_detection_V_BIRD_001`, `drone_detection_V_AIRPLANE_001` |

Все 14 файлов открываются OpenCV: `frame_count` от 288 до 1134, FPS 20–30.

### `configs/regression_pack_night.csv` (6 клипов)

| Категория | N | Клипы |
|-----------|---|-------|
| night | 3 | `night_ground_large_drones`, `antiuav_rgbt_20190925_193610_1_1_visible`, `antiuav_rgbt_20190925_200805_1_2_visible` |
| noise | 3 | `night_ground_indicator_lights`, `drone_detection_V_BIRD_001`, `drone_detection_V_AIRPLANE_001` |

---

## 2. Сводные метрики (mean по pack’у)

### Default preset · `regression_pack.csv` (14 клипов)

| Tracker | native_presence | native_id/min | native_false_lock | avg_fps | Δpresence vs project | Δid/min vs project | Δfalse_lock vs project |
|---------|----------------:|--------------:|------------------:|--------:|---------------------:|-------------------:|-----------------------:|
| ByteTrack         | 0.264 | 2.59 | 0.264 | 61.4 | 0.391 (хуже) | 6.59 | 0.391 |
| BoT-SORT          | 0.265 | 1.93 | 0.265 | 50.3 | 0.391 (хуже) | 7.40 | 0.391 |
| BoT-SORT + ReID   | 0.267 | 2.94 | 0.267 | 45.4 | 0.389 (хуже) | 8.30 | 0.389 |
| **project pipeline** | **0.655** | **5.54** | **0.655** | ~ | — | — | — |

Project mean `presence ≈ 0.655` против native `0.26–0.27`: native трекеры теряют цель на ~40% кадров pack’а больше, чем self-hold pipeline.

> Note: `false_lock_rate` ≈ `presence_rate` — структурный артефакт (большинство клипов без GT, OQ-003 уже зафиксирован). На клипах без GT любой active_frame считается false_lock, поэтому здесь это фактически "сколько кадров tracker удержал хоть какую-то цель", а не качество против правды.

### Night preset · `regression_pack_night.csv` (6 клипов)

| Tracker | native_presence | native_id/min | avg_fps | project_presence | project_id/min |
|---------|----------------:|--------------:|--------:|-----------------:|---------------:|
| ByteTrack | **0.005** | 0.00 | 35.4 | 0.265 | 5.95 |
| BoT-SORT  | **0.000** | 0.00 | 22.0 | 0.251 | 5.74 |

Native trackers под night-preset (более жёсткие пороги inference) **полностью отказывают**: `antiuav_rgbt_*` и `night_ground_large_drones`, которые на default-пресете для BT давали presence 0.6–0.7, на night-пресете дают 0.000.

---

## 3. Таблица по категориям (default preset)

| Категория | n | BT presence | BS presence | ReID presence | Project presence | BT id/min | BS id/min | ReID id/min |
|-----------|---|------------:|------------:|--------------:|-----------------:|----------:|----------:|------------:|
| day   | 3 | 0.761 | 0.769 | 0.771 | **0.995** | 2.65 | 0.00 | 0.00 |
| night | 3 | 0.436 | 0.436 | 0.440 | **0.937** | 9.42 | 9.00 | 13.71 |
| ir    | 4 | 0.024 | 0.024 | 0.024 | **0.535** | 0.00 | 0.00 | 0.00 |
| noise | 4 | 0.000 | 0.000 | 0.000 | 0.306 | 0.00 | 0.00 | 0.00 |

- На **day** native-трекеры работают терпимо, но всё равно проигрывают project pipeline на 0.23 presence.
- На **night** провал в 2× по presence; ReID *увеличивает* `id_changes/min` (13.7 vs 9.4 BT) — то есть ухудшает identity stability вопреки заявленной цели.
- На **ir** native-трекеры почти не видят цель (presence ≈ 0.02). Project — 0.54.
- На **noise** native не цепляется ни на бирды, ни на самолёты, ни на indicator-lights — это, как ни странно, *безопаснее* чем project (project на noise клипах даёт 0.31 presence = по сути «удерживает не то»). Это аргумент для следующих задач: выявлять, какие клипы были «правильно потеряны», а не «потеряны вообще». Без GT отличить нельзя.

---

## 4. Worst clips

### Native теряет цель полностью (presence ≈ 0)

| Clip | Scene | BT | BS | ReID | Project |
|------|-------|---:|---:|-----:|--------:|
| `night_ground_large_drones` | night | 0.000 | 0.000 | 0.000 | **0.892** |
| `Demo_IR_DRONE_146` | ir | 0.000 | 0.000 | 0.000 | **0.668** |
| `IR_DRONE_001` | ir | 0.000 | 0.000 | 0.000 | **0.439** |
| `dataset_mendeley_f1_1_IR_dji_mavic_2_range_close` | ir | 0.000 | 0.000 | 0.000 | 0.052 |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | ir | 0.097 | 0.096 | 0.096 | **0.983** |

### Native даёт ложные удержания (presence > 0 без подтверждения GT)

Из-за no-GT артефакта весь **noise** идёт в false_lock, но native не цепляется ни на одном noise-клипе → native в этом смысле «безопасный». Project на noise клипах удерживает в среднем 0.306 → project FP ≥ native FP. Однако без GT это не интерпретируемо как качество, см. Section 9.

### Где ReID помогает / где ухудшает

| Clip | BT presence | ReID presence | BT id/min | ReID id/min | Вывод |
|------|------------:|--------------:|----------:|------------:|-------|
| `dataset_mendeley_EO_dji_mavic_2_range_close` | 0.615 | **0.640** | 7.94 | 0.00 | помог: id_chg ↓, presence ↑ |
| `drone_detection_V_DRONE_001` | 0.744 | 0.748 | 0.00 | 0.00 | нейтрально |
| `antiuav_rgbt_20190925_200805_1_2_visible` | 0.706 | 0.717 | 21.84 | **34.69** | **ухудшил** id_chg |
| `antiuav_rgbt_20190925_193610_1_1_visible` | 0.603 | 0.603 | 6.43 | 6.43 | нейтрально |

Обобщение: ReID на presence даёт прирост ≤ 0.025; на самом нагруженном клипе (200805 visible) увеличивает `id_changes/min` в 1.6× — то есть генерирует больше false re-IDs, чем удерживает. Подтверждается прежний вывод REPORT-20260429: ReID *не* решает self-hold.

---

## 5. Можно ли заменить наше удержание цели штатным tracker?

| Tracker | Замена self-hold? | Обоснование |
|---------|:-----------------:|-------------|
| **ByteTrack** | ❌ нет | Mean presence 0.264 vs project 0.655. На night/IR pack’е под night preset presence=0.005. Подтверждает REPORT-20260429-tracker-ab. |
| **BoT-SORT**  | ❌ нет | Mean presence 0.265, на night preset 0.000. Хуже ByteTrack по FPS (50 vs 61). |
| **BoT-SORT + ReID** | ❌ нет | Mean presence 0.267 (микроскопический прирост к BoT-SORT), но `id_changes/min` хуже на ключевых клипах. Стоимость FPS 45 vs 61 (BT). REID не выигрывает там, где self-hold нужен. |

**Подтверждается прежний вывод:** native Ultralytics trackers не удерживают цель в условиях, где project pipeline (YOLO + TemplateLockTracker + TargetManager + NightDetector) даёт ≥ 0.5 presence.

---

## 6. Архитектурные выводы

| Вопрос | Ответ |
|--------|-------|
| Оставлять штатный tracker как evidence source? | **Да.** Native track_id / bbox / conf — корректная новая `TargetEvidence` со средней `source_reliability` (≈ 0.6, ниже project YOLO=1.0, выше night=0.4). Использовать как ещё один proposal channel — НЕ как replacement self-hold. |
| Подключать `TrackingAction` к behavior сейчас? | **Нет.** `ActionPolicy` (ALG-001 v1) остаётся telemetry-only. Перед wiring нужен отдельный gate run на этом расширенном pack’е, иначе нет baseline для сравнения. |
| Нужна ли задача на GT/label ingestion для Anti-UAV / Drone-detection? | **Да, высокий приоритет.** Текущая интерпретация ограничена: 10 из 14 клипов без GT, поэтому `false_lock_rate ≡ presence_rate` (OQ-003 артефакт). Без GT нельзя различить «правильно удерживает» и «удерживает не то». Anti-UAV и Drone-detection датасеты содержат label.json — следующий task должен импортировать их в `SequenceGroundTruth` для каждого видео-клипа. |

---

## 7. Output артефакты

JSON summary + CSV per tracker (`runs/ultralytics_tracking_eval/`):

| Файл | Run |
|------|-----|
| `expanded_pack_bytetrack_tracking_eval_default_bytetrack.{json,csv}` | default · ByteTrack · 14 клипов |
| `expanded_pack_botsort_tracking_eval_default_botsort.{json,csv}` | default · BoT-SORT · 14 клипов |
| `expanded_pack_botsort_reid_tracking_eval_default_botsort.{json,csv}` | default · BoT-SORT + ReID · 14 клипов |
| `expanded_night_bytetrack_tracking_eval_night_bytetrack.{json,csv}` | night · ByteTrack · 6 клипов |
| `expanded_night_botsort_tracking_eval_night_botsort.{json,csv}` | night · BoT-SORT · 6 клипов |

Per-clip JSONs (один на клип на трекер) тоже сохранены в той же директории. Smoke-прогон (--max-frames 60) сохранён под префиксом `smoke_`.

`runs/ultralytics_tracking_eval/log_*.txt` — stdout/stderr каждого запуска.

---

## 8. Validation

| Команда | Результат |
|---------|-----------|
| `pytest tests/test_ultralytics_tracking_eval.py -q` | **5 passed** |
| `compileall python_scripts src app orchestrator tests` | OK |
| `git diff --check` | clean |
| `git status --short --branch` | main впереди origin/main; новый отчёт + measurement артефакты в `runs/` |

---

## 9. Риски и ограничения

1. **No-GT артефакт.** 10 из 14 клипов (`drone_closeup_mixkit`, mendeley EO/IR, `drone_detection_V_*`, antiuav_rgbt visible/infrared) не имеют GT, поэтому каждый удержанный кадр считается false_lock. `false_lock_rate ≡ presence_rate`. Сравнение presence — корректно, false_lock — *не* интерпретируемо как качество. OQ-003 уже зафиксирован.
2. **Native night отказ — может быть preset-induced.** Под night preset `CONF_THRESH=0.12`, `IMG_SIZE` повышен. Возможно, BT/BS требуется свой подбор conf под night. Этот task не калибрует — фиксирует факт.
3. **ReID конфигурация — дефолтная.** `configs/trackers/botsort_reid.yaml` использует встроенную модель Ultralytics; кастомный ReID-encoder не обучался. Возможен потенциал улучшения, но требует обучения и не входит в scope.
4. **MPS детерминизм.** Прогоны под MPS могут давать ±0.01 разброс presence между запусками. Различия 0.264 vs 0.655 заведомо за пределами шума.
5. **Behavior pipeline не менялся.** Никаких изменений в pipeline, thresholds, presets. Quality gate не перезапускался — он не нужен, поведение не меняли.

---

## 10. Что осталось на следующий task (предложение для Codex/Human)

1. **GT/label ingestion** — импорт Anti-UAV / Drone-detection labels (`label.json`/`IR_label.json`) для всех клипов из `regression_pack.csv`. Без этого `false_lock_rate` бессмыслен.
2. **TargetEvidence: Ultralytics native track как evidence channel.** В `pipeline.py` добавить evidence из `model.track(persist=True)` параллельно с YOLO-detections; не подключать к `select_active`, но писать в telemetry.
3. **ActionPolicy behavior wiring** — после п.1 (есть GT) можно делать gated A/B.
4. **Калибровка native trackers под night preset** — отдельная диагностическая задача; вернуть BT/BS на достижимые числа или зафиксировать ограничение.

---

**Stop after task.** Следующий шаг выбирает Codex/Human.
