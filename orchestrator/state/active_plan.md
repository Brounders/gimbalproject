# Active Plan

## Plan ID
- AP-20260311-005

## Source Direction
- Human direction: `План: По какой то причине опять появился прицел в место рамки - вернуть рамку с ID цели. Режим авто не распознал ночную сцену, проверить алгоритмы распознования , предпринять меры исправления/устранения недостатков. Все еще сильное дрожание при трекинге цели, требую более точного/плавного распознования и ведения цели в ночное время , обдумать методы реализации и предложить. Подготовиться к большому изменению графической части интерфейса, предложить современные методы для достижения желаемого интерфейса, возможно я дам готовое приложение для изучения либо изображение желаемого.`
- Human confirmation for delivery: `Выгружай план клоду без редизайна`

## Status
- Active

## Brief In Focus
- BRIEF-20260311-008-tracking-hardening-no-redesign

## Active Claude Tasks (execution allowed now)
- TASK-20260311-019 | overlay-box-id-restore | Open
- TASK-20260311-020 | auto-scene-detection-hardening | Open
- TASK-20260311-021 | night-target-stability | Open

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.
- TASK-20260311-013 остается backlog-task и не относится к текущему hardening cycle.
- Большой редизайн UI в этот active plan сознательно не включен.

## Exit Criteria
- Default operator overlay is box + target ID.
- Auto mode handles obvious night scene selection more reliably.
- Night target following is visibly less jittery without broad decision-loop rewrite.
