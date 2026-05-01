# REPORT OQ-003-diag: false_lock=1.000 на day clips

**Date:** 2026-05-01
**Status:** DIAGNOSED — root cause confirmed, no runtime fix needed
**OQ-003:** CLOSED (диагностика завершена)

---

## Вопрос

Почему `false_lock_rate=1.000` на day clips в quality gate? Это баг модели, preset-проблема
или структурный артефакт?

---

## Root Cause: нет GT-файла → структурный артефакт

**Клип:** `test_videos/drone_closeup_mixkit_44644_360.mp4`

В `src/uav_tracker/evaluation.py` логика:

```python
gt_visible = bool(meta.get('gt_bbox'))   # False когда нет GT-файла

if result.active_id is not None:          # трекер что-то отслеживает
    if (not gt_visible) or (gt_visible and result.gt_iou < 0.10):
        false_lock_frames += 1            # ← засчитывается при gt_visible=False
```

Если для клипа нет GT-файла (`gt_bbox` отсутствует):
- `gt_visible = False` на каждом кадре
- `gt_frames = 0`
- Каждый кадр, где `active_id is not None`, → `false_lock_frames += 1`
- Итог: `false_lock_rate = false_lock_frames / total_frames ≈ 1.000`

Это происходит для **любой модели** на этом клипе. Это не признак плохого качества модели.

---

## Влияние на gate: НУЛЕВОЕ (уже защищено)

`run_quality_gate.py` уже содержит защиту:

```python
if gt_frames > 0:                         # ← пропускает клипы без GT
    false_lock_limit = ...
    if float(row["false_lock_rate"]) > false_lock_limit:
        row_failures.append(...)
```

И в `_score_row`:
```python
has_gt = int(row.get("gt_frames", 0)) > 0
false_lock_penalty = 18.0 * float(row.get("false_lock_rate", 0.0)) if has_gt else 0.0
```

**Вывод:** `false_lock=1.000` появляется в JSON/CSV-выводе, но **не влияет на решение gate**
и **не включается в scoring**. Gate корректен.

---

## Риск: читаемость выходных данных

Число `false_lock_rate: 1.0000` в JSON/CSV вводит в заблуждение при ручном чтении.
Человек может принять это за провал модели.

Это уже задокументировано в `configs/regression_pack_day.csv`:
```
# NOTE: drone_closeup_mixkit_44644_360.mp4 has NO GT file.
# false_lock is structurally 1.000 for ANY model on this clip.
# This gate is VALID only for FPS and id_chg/min metrics.
```

Документация достаточная для оператора, читающего pack-файл.

---

## Возможные улучшения (не реализованы, не блокируют)

| Улучшение | Эффект | Приоритет |
|-----------|--------|-----------|
| Добавить GT-файл к клипу | false_lock станет реальным сигналом | Low — требует ручной разметки |
| Поле `false_lock_valid: false` в JSON когда gt_frames=0 | Устранит путаницу при чтении | Low — cosmetic |
| Заменить `false_lock_rate: 1.0` на `null` в no-GT строках | Явный сигнал "не валидно" | Low — breaking change в CSV |

Ни одно из улучшений не блокирует текущий workflow. Открывать как отдельные задачи только
по явному запросу Human.

---

## Заключение

| Вопрос | Ответ |
|--------|-------|
| Это баг модели? | Нет |
| Это preset-проблема? | Нет |
| Gate принимает неверные решения? | Нет — уже защищён через `gt_frames > 0` |
| Требует runtime-фикса? | Нет |
| OQ-003 можно закрыть? | **Да** |

OQ-003 закрыт: диагноз поставлен, поведение корректно, риск задокументирован.
