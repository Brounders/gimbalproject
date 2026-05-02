# Active Plan

## Plan ID
- AP-FP-ID-SUPPRESSOR-V1

## Status
- Completed

## Active Claude Tasks (execution allowed now)
- none

## Active RTX Tasks (execution allowed now)
- none

## Source Direction
Human approved the FP/ID suppressor cycle after ActionPolicy telemetry showed that the blocking `noise-airplane` false lock and visible-night diagnostic false locks were weak runtime evidence rather than high-confidence YOLO false positives.

## AP-FP-ID-SUPPRESSOR-V1 — False Positive / ID Suppressor

### Цель

Проверить, можно ли безопасно уменьшить ложные удержания и ID-дёрганье на weak/noise evidence без ухудшения accepted day/IR gate.

### Результат

| ID | Задача | Статус | Результат |
|----|--------|--------|-----------|
| FPID-001 | Baseline promotion + diagnostic gates | ✅ DONE | Blocking retry PASS; diagnostic-night PASS |
| FPID-002 | Evaluation telemetry for false locks | ✅ DONE | `EvaluationReport` получил action/source/modality/reliability counters |
| FPID-003 | Telemetry rerun + decision checkpoint | ✅ DONE | `POLICY_SUPPRESSOR_CANDIDATE`: false locks идут из weak runtime evidence |
| FPID-004 | Weak-evidence suppressor implementation | ✅ DONE | `night/roi` weak evidence → guarded `DROP_LOCK`; blocking gate PASS |
| FPID-005 | Final report and state close | ✅ DONE | `REPORT-FP-ID-SUPPRESSOR-IMPLEMENTATION-20260503.md` |

### Итоговое решение

**PASS for blocking gate.**

Ключевые факты:

- `noise-airplane` false lock улучшен: `0.190 → 0.171`.
- Day clip не изменился по presence/false_lock/idchg.
- IR clips не ухудшены materially.
- Visible-night diagnostic false_lock/idchg снижаются, но presence падает и drop rate высокий, поэтому visible-night остаётся diagnostic-only.
- `ACTION_POLICY_BEHAVIOR_ENABLED` остаётся default OFF.

### Отчёты

- `orchestrator/reports/REPORT-FP-ID-SUPPRESSOR-V1-20260502.md`
- `orchestrator/reports/REPORT-FP-ID-SUPPRESSOR-IMPLEMENTATION-20260503.md`

### Следующий шаг

Выбрать новый цикл после Human approval. Не начинать следующий implementation без отдельного подтверждения.
