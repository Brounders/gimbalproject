# CODEX HANDOFF LOG

> Лог автономной работы Claude Mac начиная с 2026-03-13.
> Codex: прочти этот файл перед открытием нового AP-цикла.
> Записи добавляются снизу в хронологическом порядке.

---

<!-- ЗАПИСИ НАЧИНАЮТСЯ ЗДЕСЬ -->

---

## 2026-03-13 — Сессия 1: Baseline + Day Gate + IR Hardening v1

### Что сделано

**1. Day Gate — Governance Fix**
- `configs/regression_pack_day.csv`: добавлен комментарий — day clip `drone_closeup_mixkit_44644_360.mp4` без GT, `false_lock=1.000` структурно для любой модели
- `RUNBOOK.md`: добавлена секция "Day Gate — известное ограничение (FPS-only)"
- **Вывод:** day gate теперь используется только для FPS и id_chg/min сравнений
- Commit: `governance: day gate is FPS-only`

**2. Baseline Formalization**
- Прогнан IR gate на `drone_bird_probe_fast` (первый раз): Demo_IR_DRONE_146 false_lock=0.840/id_chg=63.26 FAIL; IR_DRONE_001 false_lock=0.784 FAIL; IR_BIRD_001 false_lock=0.090 PASS
- `install_baseline.py` выполнен → `models/baseline.pt` установлен
- SHA256: `bedc77fe7b899de1ac68ae654f49fcee6301a9d3f8a61e9eff5c1e8d66641d44`
- `models/baseline_manifest.json` создан с gate-привязками (night + IR)
- `automation/state/decision_log.json`: добавлена запись `install_as_baseline`
- Отчёт: `orchestrator/reports/REPORT-baseline-formalization.md`
- Commit: `baseline: formalize drone_bird_probe_fast as models/baseline.pt`

**3. IR Hardening v1 — Null Result (диагностически важно)**
- Добавлены 4 lock policy knobs в `configs/antiuav_thermal.yaml`:
  `active_id_switch_cooldown_frames=60`, `track_state_acquire_frames=4`,
  `lock_mode_acquire_frames=3`, `active_id_switch_allow_if_lost_frames=12`
- Gate: Demo_IR_DRONE_146 id_chg **63.26 (без изменений)** → lock policy layer НЕ является драйвером
- Root cause: YOLO детекции нестабильны → трек уходит в LOST → SCAN → новый ID (track reset, не ID switch)
- Cooldown не применяется к track resets из SCAN mode
- Отчёт: `orchestrator/reports/REPORT-ir-hardening-v1.md`
- Commit: `IR hardening v1: null result`

### Ключевые числа после сессии

| Контекст | Clip | false_lock | id_chg/min | Статус |
|----------|------|-----------|------------|--------|
| Night | large_drones | **0.510** | **12.23** | PASS (AP-025) |
| Night | indicator_lights | **0.096** | 0.00 | PASS (AP-025) |
| IR | Demo_IR_DRONE_146 | 0.840 | 63.26 | FAIL — open |
| IR | IR_DRONE_001 | 0.784 | 5.98 | FAIL — open |
| IR | IR_BIRD_001 | **0.090** | 0.00 | PASS |
| Day | drone_closeup | 1.000* | 0.00 | *no GT — FPS-only |

### Что открыто для следующего цикла Codex

1. **IR id_chg (Demo_IR_DRONE_146)**: попробовать `track_state_lost_frames: 16-20` в `antiuav_thermal.yaml` — держать трек при кратковременных YOLO пропусках. Риск: может продлить false_lock events. Нужен отдельный AP-цикл.
2. **IR false_lock (IR_DRONE_001: 0.784)**: требует модельного решения — лучшая IR-trained модель. Runtime tuning даст лишь partial improvement.
3. **Day GT**: `drone_closeup_mixkit_44644_360.mp4` нужен `label.json` для полноценного day gate.
4. **Training strategy reset**: dataset audit drone-bird-yolo + новый training plan (одобрение Codex).
