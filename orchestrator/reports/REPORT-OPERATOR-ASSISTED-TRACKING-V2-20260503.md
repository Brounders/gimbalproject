# REPORT-OPERATOR-ASSISTED-TRACKING-V2-20260503

## Статус

Accepted / implemented by Codex Mac.

## Цель

Модернизировать ручной выбор цели из простого click-to-lock в
operator-assisted tracking mode и сразу заложить канал ручной разметки для
будущего обучения detector-модели.

## Реализовано

1. Drag-to-select bbox
   - `VideoStage` теперь различает короткий click и drag bbox.
   - `app/ui/video_mapping.py` конвертирует point/bbox из QLabel coordinates
     в координаты исходного frame с учётом `Qt.KeepAspectRatio`.

2. Автоподстройка seed bbox
   - `refine_operator_seed_bbox()` ищет контрастный blob внутри выбранной
     области.
   - Если blob не найден, исходный operator bbox сохраняется.

3. Operator hold policy
   - `OPERATOR_HOLD_GRACE_FRAMES`.
   - Operator target не удаляется сразу по обычному YOLO TTL.
   - `confirm_active_as_operator()` force-enters focus mode.

4. Multi-template удержание
   - `TemplateLockTracker` хранит bounded template bank.
   - `predict()` выбирает лучший score среди шаблонов.

5. Local/operator lock-first path
   - Для active source `operator` pipeline предпочитает `OPERATOR-LOCK`,
     а не немедленный global scan.
   - Это сохраняет локальное visual tracking поведение, даже если detector
     не видит объект.

6. Confirm / release controls
   - Worker получил `request_operator_confirm()` и
     `request_operator_release()`.
   - UI получил кнопки подтверждения и сброса operator target.

7. Канал данных для обучения
   - GUI-сессия создаёт `runs/operator_annotations/<timestamp>_*.jsonl`.
   - При успешном operator override пишется:
     - `frame_index`;
     - `source`;
     - `bbox_xyxy`;
     - `active_id`;
     - `active_source`;
     - `event=operator_bbox`.

## Почему это помогает обучению

Если operator bbox регулярно сохраняется на клипах, где detector не видит
дрон, эти события становятся hard-negative/hard-positive материалом:

- можно извлечь кадры по `frame_index`;
- конвертировать `bbox_xyxy` в YOLO txt labels;
- собрать датасет именно из случаев, где текущая модель провалилась;
- переобучать detector на реальных операторских коррекциях, а не на случайных
  красивых кадрах.

## Validation

- targeted tests for operator override / worker / mapping / seed refinement /
  lock tracker passed in-session.
- full validation pending in session close.

## Следующий шаг

Полевой GUI smoke на проблемных клипах:

- click vs drag bbox;
- проверить, что drag лучше фиксированного click box;
- проверить устойчивость `OPERATOR-LOCK`;
- убедиться, что `runs/operator_annotations/*.jsonl` содержит пригодные bbox.
