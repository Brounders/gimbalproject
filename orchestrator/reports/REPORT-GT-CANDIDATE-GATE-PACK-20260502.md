# REPORT-GT-CANDIDATE-GATE-PACK-20260502

**Task:** подобрать night/IR клипы для будущего `ActionPolicy` gate
**Date:** 2026-05-02
**Status:** PARTIAL · IR GT-positive найден · night остается weak/diagnostic

---

## 1. Что искали

Цель была не просто добавить новые видео, а найти клипы, где:

- есть GT bbox;
- видео читается OpenCV;
- baseline/project pipeline реально попадает в цель;
- есть минимум day/night/IR TP и noise FP-control для будущего behavior gate.

Порог для accepted GT-positive:

- `avg_gt_iou >= 0.10` для project pipeline;
- либо достаточное число `hits_iou_01`, если клип используется только как diagnostic candidate.

---

## 2. Источники и скрининг

### Anti-UAV-RGBT visible/night

Просканированы dark/dusk visible-кандидаты из:

- `/Users/bround/Desktop/Датасеты/Anti-UAV-RGBT/test`
- `/Users/bround/Desktop/Датасеты/Anti-UAV-RGBT/train`

Сначала был быстрый detector scan по sampled frames. Лучшие visible-кандидаты:

| Clip | sampled mean_iou | hit01 | mean_gray | Вывод |
|------|-----------------:|------:|----------:|-------|
| `train/20190925_210802_1_2/visible` | 0.175 | 3/8 | 3.7 | detector иногда видит цель |
| `train/20190925_210802_1_7/visible` | 0.156 | 2/8 | 3.7 | detector иногда видит цель |
| `train/20190925_210802_1_4/visible` | 0.109 | 2/8 | 3.8 | detector иногда видит цель |

Но stateful `TrackerPipeline` на тех же клипах удерживал ложные объекты:

| Clip | preset | frames | project avg_gt_iou | hits_iou_01 | Вывод |
|------|--------|-------:|-------------------:|------------:|-------|
| `20190925_210802_1_2/visible` | `night` | 300 | 0.0006 | 0/300 | reject |
| `20190925_210802_1_4/visible` | `night` | 300 | 0.0014 | 2/300 | reject |
| `20190925_205804_1_2/visible` | `night` | 300 | 0.0107 | 8/300 | weak, not accepted |
| `20190925_210802_1_4/visible` | `default` | 300 | 0.0086 | 7/300 | weak, not accepted |

Вывод: Anti-UAV visible night сейчас не годится как GT-positive gate для baseline/project pipeline.

### Existing night clip

Для `test_videos/night_ground_large_drones.mp4` создан derived GT по bright compact target в верхней части кадра:

- `configs/ground_truth/regression_pack/night_ground_large_drones_gt.json`
- 288 frames total;
- 259 GT-present frames;
- visual overlay checked manually.

Full night-preset eval:

| Clip | frames | gt_frames | project_presence | project_false_lock | avg_gt_iou | hits_iou_01 |
|------|-------:|----------:|-----------------:|-------------------:|-----------:|------------:|
| `night_ground_large_drones` | 288 | 259 | 0.5208 | 0.4479 | 0.0125 | 21 |

Вывод: клип полезен как night diagnostic, но **не проходит accepted GT-positive threshold**.

### Anti-UAV-RGBT infrared

Найдены и подтверждены два сильных IR GT-positive клипа:

| Clip | frames | gt_frames | project_presence | project_false_lock | avg_gt_iou | hits_iou_01 | hits_iou_05 |
|------|-------:|----------:|-----------------:|-------------------:|-----------:|------------:|------------:|
| `antiuav_rgbt_train_20190925_210802_1_7_infrared` | 934 | 934 | 1.0000 | 0.0118 | 0.7620 | 923 | 915 |
| `antiuav_rgbt_train_20190925_205804_1_2_infrared` | 894 | 894 | 1.0000 | 0.1107 | 0.6924 | 795 | 787 |

Вывод: IR часть gate теперь закрыта.

---

## 3. Созданные/обновленные pack files

| File | Назначение | Статус |
|------|------------|--------|
| `configs/gt_candidate_gate_pack.csv` | day + weak night + accepted IR + noise controls | candidate only |
| `configs/gt_candidate_gate_pack_night.csv` | night diagnostic + noise controls | weak diagnostic |
| `configs/gt_positive_gate_pack_ir.csv` | accepted IR GT-positive + noise controls | accepted for IR |

`configs/gt_candidate_gate_pack.csv` сейчас не должен использоваться как final behavior gate, потому что night-клип weak.

---

## 4. Сгенерированные GT файлы

| File | Frames | Источник |
|------|-------:|----------|
| `configs/ground_truth/regression_pack/night_ground_large_drones_gt.json` | 288 | derived bright-blob GT, manual visual check |
| `configs/ground_truth/regression_pack/antiuav_rgbt_train_20190925_210802_1_7_infrared_gt.json` | 934 | Anti-UAV train `infrared.json` |
| `configs/ground_truth/regression_pack/antiuav_rgbt_train_20190925_205804_1_2_infrared_gt.json` | 894 | Anti-UAV train `infrared.json` |

Также уже существовали/используются:

- `test_videos/drone_closeup_mixkit_44644_360_gt.json`
- `configs/ground_truth/regression_pack/drone_detection_V_BIRD_001_gt.json`
- `configs/ground_truth/regression_pack/drone_detection_V_AIRPLANE_001_gt.json`

---

## 5. Eval artifacts

| Artifact | Что проверяет |
|----------|---------------|
| `runs/ultralytics_tracking_eval/gtpos_ir_tracking_eval_antiuav_thermal_bytetrack.json` | full IR pack, `antiuav_thermal` preset |
| `runs/ultralytics_tracking_eval/gtpos_ir_tracking_eval_antiuav_thermal_bytetrack.csv` | full IR pack CSV |
| `runs/ultralytics_tracking_eval/gtpos_night_v2_tracking_eval_night_bytetrack.json` | night diagnostic pack, `night` preset |
| `runs/ultralytics_tracking_eval/gtpos_night_v2_tracking_eval_night_bytetrack.csv` | night diagnostic CSV |

---

## 6. Решение

**IR:** PASS for gate-candidate readiness.
Два IR клипа имеют сильный project IoU и годятся для будущего A/B.

**Night:** DEFER.
Ни Anti-UAV visible night, ни derived `night_ground_large_drones` не дают `project avg_gt_iou >= 0.10`. Ночной клип можно использовать как diagnostic, но не как accepted GT-positive gate.

**ActionPolicy behavior wiring:** DEFER.
Теперь есть day + IR + noise, но все еще нет сильного night GT-positive клипа. Для behavior wiring нужен хотя бы один night clip с project `avg_gt_iou >= 0.10`, иначе night regression risk не закрыт.

---

## 7. Следующий шаг

1. Сделать ручную GT-разметку для `night_ground_large_drones` не только по bright-blob, а по фактическому target extent и проверить center/IoU.
2. Или подобрать новый visible-night клип вне Anti-UAV-RGBT, где текущий project pipeline реально попадает в цель.
3. После этого собрать final `gt_positive_gate_pack.csv` и только потом запускать `ActionPolicy` behavior A/B.
