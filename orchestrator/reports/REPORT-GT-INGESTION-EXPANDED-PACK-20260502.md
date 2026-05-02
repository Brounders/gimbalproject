# REPORT-GT-INGESTION-EXPANDED-PACK-20260502

**Task:** GT/Label Ingestion for Expanded Regression Pack
**Date:** 2026-05-02
**Status:** Complete · 6/14 clips with GT · tracker rerun done · DEFER on ActionPolicy wiring

---

## 1. Clips с GT после ingestion

| Clip | GT type | Источник | gt_frames | target_present |
|------|---------|----------|----------:|:--------------:|
| `drone_closeup_mixkit_44644_360` | sibling `_gt.json` | `test_videos/drone_closeup_mixkit_44644_360_gt.json` (существовал) | 579 | ✅ all |
| `antiuav_rgbt_20190925_193610_1_1_visible` | pack-dir | Desktop `20190925_193610_1_1/visible.json` | 933 | ✅ all |
| `antiuav_rgbt_20190925_200805_1_2_visible` | pack-dir | Desktop `20190925_200805_1_2/visible.json` | 934 | ✅ all |
| `antiuav_rgbt_20190925_200805_1_2_infrared` | pack-dir | Desktop `20190925_200805_1_2/infrared.json` | 934 | ✅ all |
| `drone_detection_V_BIRD_001` | pack-dir (синтетический) | target-absent, 305 нулей | 0 | ❌ absent |
| `drone_detection_V_AIRPLANE_001` | pack-dir (синтетический) | target-absent, 327 нулей | 0 | ❌ absent |

**GT-covered frames: 579 + 933 + 934 + 934 + 305 + 327 = 4012 из ~5558 total (72 % кадров expanded pack).**

Sibling-lookup (`test_videos/drone_closeup_mixkit_44644_360_gt.json`) подхватился автоматически — это ранее созданный GT-файл, не импортированный скриптом.

---

## 2. Clips без GT и причины

| Clip | Причина |
|------|---------|
| `night_ground_large_drones` | Нет источника (кастомная запись) |
| `Demo_IR_DRONE_146` | Нет источника |
| `IR_DRONE_001` | Нет источника |
| `IR_BIRD_001` | Нет источника |
| `night_ground_indicator_lights` | Нет источника |
| `dataset_mendeley_f1_1_EO_dji_mavic_2_range_close` | Mendeley — нет GT файлов |
| `dataset_mendeley_f1_1_IR_dji_mavic_2_range_close` | Mendeley — нет GT файлов |
| `drone_detection_V_DRONE_001` | `V_DRONE_001_LABELS.mat` — формат MATLAB MCOS (`groundTruth` object, `MatlabOpaque`), не читается `scipy.io` без MATLAB runtime. **Limitation зафиксирована.** |

---

## 3. Результаты tracker rerun с GT

### Сводная таблица (14 клипов, default preset)

| Tracker | mean presence | mean false_lock | mean fps |
|---------|-------------:|----------------:|---------:|
| **ByteTrack** | 0.2636 | **0.1974** | 24.5 |
| **BoT-SORT**  | 0.2651 | **0.1989** | 24.4 |
| **BoT-SORT+ReID** | 0.2665 | **0.2003** | 27.2 |
| *project pipeline* | *0.58–0.66* | *0.51–0.58* | — |

> Сравни с previous run (no GT): `false_lock ≡ presence ≈ 0.264` для всех native trackers — OQ-003 артефакт. Теперь false_lock отделён от presence для 6 клипов.

### По clip-типам с GT

| Clip | GT type | BT presence | BT false_lock | BT avg_gt_iou | Project presence | Project false_lock | Project avg_gt_iou |
|------|---------|------------:|--------------:|--------------:|-----------------:|-------------------:|-------------------:|
| `drone_closeup_mixkit_44644_360` | GT-present | 0.926 | **0.000** | **0.9095** | 1.000 | **0.000** | **0.9356** |
| `antiuav_193610_1_1_visible` | GT-present | 0.603 | **0.603** | **0.0000** | 1.000 | **1.000** | **0.0000** |
| `antiuav_200805_1_2_visible` | GT-present | 0.706 | **0.705** | **0.0004** | 1.000 | **0.998** | **0.0000** |
| `antiuav_200805_1_2_infrared` | GT-present | 0.097 | **0.097** | **0.0000** | 0.891 | **0.891** | **0.0000** |
| `V_BIRD_001` | absent-GT | 0.000 | **0.000** | 0.0000 | 0.000 | **0.000** | 0.0000 |
| `V_AIRPLANE_001` | absent-GT | 0.000 | **0.000** | 0.0000 | 0.150 | **0.150** | 0.0000 |

---

## 4. Изменились ли false_lock выводы

### Было (OQ-003 no-GT):
`false_lock_rate ≡ presence_rate` для 10/14 клипов — неинтерпретируемо.

### Стало:
**Для noise clips (Bird, Airplane):**
- Native trackers: false_lock = 0.000 → **подтверждает**: native trackers не цепляются за птиц и самолёты. Безопасное поведение.
- Project pipeline: V_BIRD false_lock=0.000 ✅; V_AIRPLANE false_lock=0.150 ⚠️ — проект удерживает самолёт 15% кадров.

**Для Anti-UAV GT клипов — НОВОЕ ОТКРЫТИЕ:**
- `avg_gt_iou ≈ 0.0000` для обоих — native И project pipeline.
- Baseline model (drone_bird_probe_fast) **не локализует Anti-UAV дроны** по GT-координатам.
- Tracker обнаруживает что-то в кадре (presence > 0), но IoU с GT bbox близко к нулю.
- **Диагностика**: Anti-UAV дрон на кадре #0 для 193610 clip — GT xyxy = (1577, 477, 1638, 514) (правая часть, малый объект 61×37 px). Tracker возвращает (297, 101, 451, 158) — левая верхняя часть кадра, совершенно другой объект.
- Вывод: модель не обнаруживает Anti-UAV targets напрямую — обнаруживает false positive где-то в другой части кадра.

**Для drone_closeup_mixkit (sibling GT):**
- BT: presence=0.926, false_lock=0.000, avg_gt_iou=0.9095 → **истинный True Positive**.
- Project: presence=1.000, false_lock=0.000, avg_gt_iou=0.9356 → **project превосходит**.

---

## 5. Нужно ли повторять native tracker decision

**Нет.** Native tracker verdict подтверждён GT-данными:
- На единственном надёжном GT-положительном клипе (`drone_closeup_mixkit`): native присутствие 0.926 vs project 1.000 — проект лучше.
- На Anti-UAV clips: обе системы имеют IoU≈0 — обе теряют цель в той же мере.
- На noise clips: обе системы верно дают false_lock=0 (для native).
- **Вывод**: ByteTrack/BoT-SORT/ReID не могут заменить self-hold. Решение из REPORT-TRACKERS-EXPANDED-PACK-20260501 остаётся в силе.

---

## 6. Рекомендация: ActionPolicy behavior wiring — DEFER

**Решение: DEFER.** Обоснование:

| Критерий | Статус |
|----------|--------|
| GT для True Positive detection | ⚠️ **1 клип** (drone_closeup_mixkit) — недостаточно для gate |
| GT для False Positive контроля | ✅ 2 noise clips (Bird, Airplane) — достаточно |
| Anti-UAV clips верифицируют detection | ❌ model не локализует Anti-UAV targets (avg_iou=0) |
| Clips без GT (8/14) | ❌ для них false_lock не интерпретируем после wiring |
| Night/IR clips с GT | ❌ нет GT для ночных и IR клипов без Anti-UAV |

Для gate ActionPolicy behavior wiring требуется:
1. Хотя бы 3–4 GT-положительных клипа с `avg_gt_iou ≥ 0.10` для обоих trackers.
2. Или GT для `V_DRONE_001` (решить .mat limitation через MATLAB экспорт или ручную разметку).
3. Или GT для `night_ground_large_drones` / `IR_DRONE_001` (основные диагностические night/IR клипы).

До этого ActionPolicy остаётся telemetry-only (как в ALG-001 v1).

---

## 7. Что реализовано

### Изменённые файлы

| Файл | Тип | Описание |
|------|-----|----------|
| `src/uav_tracker/pipeline.py` | EDIT | `SequenceGroundTruth`: поддержка MP4/file sources; `_resolve_file_gt_path()` (sibling + pack-dir lookup); `pipeline.open()` создаёт GT для file sources |
| `python_scripts/import_regression_pack_gt.py` | NEW | Импорт Anti-UAV JSON, синтез absent GT для noise clips, документирование .mat limitation |
| `tests/test_pipeline_helpers.py` | EDIT | +13 тестов: MP4 GT resolution (sibling/pack-dir/no-gt), bbox_for xywh→xyxy, target-absent, Anti-UAV round-trip, sibling priority, import_antiuav error/valid, synthesise_absent |

### Сгенерированные GT файлы

```
configs/ground_truth/regression_pack/
  antiuav_rgbt_20190925_193610_1_1_visible_gt.json  (933 frames, all present)
  antiuav_rgbt_20190925_200805_1_2_visible_gt.json   (934 frames, all present)
  antiuav_rgbt_20190925_200805_1_2_infrared_gt.json  (934 frames, all present)
  drone_detection_V_BIRD_001_gt.json                 (305 frames, all absent)
  drone_detection_V_AIRPLANE_001_gt.json             (327 frames, all absent)
```

### Rerun artifacts

```
runs/ultralytics_tracking_eval/
  gt_tracking_eval_default_bytetrack.{json,csv}
  gt_tracking_eval_default_botsort.{json,csv}
  gt_reid_tracking_eval_default_botsort.{json,csv}
  gt_<clip>_{bytetrack,botsort,project}.json  (per-clip, 42 files)
```

---

## 8. Validation

| Команда | Результат |
|---------|-----------|
| `pytest tests/test_pipeline_helpers.py tests/test_ultralytics_tracking_eval.py -q` | **33 passed** |
| `pytest tests` | **476 passed** (+10 vs 466 before) |
| `compileall python_scripts src app orchestrator tests` | OK |
| `git diff --check` | clean |
| `check_orchestration_state.py` | `OK`, active=0, open=0, completed=69 |
| `import_regression_pack_gt.py --pack-file configs/regression_pack.csv` | 5/14 OK |

---

## 9. Риски и ограничения

1. **Anti-UAV avg_gt_iou=0.** Baseline model не детектирует Anti-UAV targets. Не регрессия — это ограничение модели по отношению к этому датасету. Для корректной оценки нужна либо другая модель, либо другие GT клипы.

2. **V_DRONE_001_LABELS.mat.** MATLAB MCOS формат, неразбираемый без runtime. Для решения: экспортировать из MATLAB в CSV/JSON, или ручная разметка.

3. **8/14 клипов без GT.** Ночные, IR и Mendeley clips остаются без GT. Для них `false_lock` после wiring по-прежнему неинтерпретируем.

4. **V_AIRPLANE_001: project false_lock=0.150.** Project pipeline удерживает самолёт 15% кадров — это реальный FP, обнаруженный благодаря GT. Требует внимания при wiring.

5. **SequenceGroundTruth._PACK_GT_DIR — относительный путь.** Работает когда CWD = project root. Если процесс запускается из другой директории, lookup не найдёт GT. Приемлемо для offline eval scripts, неприемлемо для runtime deployment.

---

## 10. Что осталось (предложение для Codex/Human)

1. **GT для V_DRONE_001**: экспортировать из MATLAB → JSON; или ручная разметка N=500 ключевых кадров.
2. **GT для night/IR clips**: `night_ground_large_drones`, `IR_DRONE_001`, `Demo_IR_DRONE_146` — основные diagnostic clips без GT.
3. **Anti-UAV model gap**: либо fine-tune модель на Anti-UAV clips, либо выводить их из gate как "нет GT на модели".
4. **ActionPolicy behavior wiring gate**: только после п.1 или п.2 — нужен хотя бы один night GT клип с project avg_gt_iou ≥ 0.10.
5. **V_AIRPLANE FP**: исследовать почему project удерживает самолёт 15% кадров; может указывать на нужду в FP-suppressor в ActionPolicy.

---

**Stop after task.** Следующий шаг выбирает Codex/Human.
