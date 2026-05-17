# Project Safety Hardening Plan

Дата статуса: 2026-05-17

Этот документ фиксирует TASK-20260517-112: какие тесты и CI sanity нужны перед
возвратом к detector/training и физической реструктуризации. Это backlog, а не
runtime change.

## 1. NightSmallTargetDetector Unit Tests

Файл риска: `src/uav_tracker/detectors/night_detector.py`.

Почему риск высокий:

- detector stateful: `_candidates`, `_active_key`, `_active_missing`,
  `_prev_gray`, `_warmup`;
- поведение зависит от множества config knobs: MOG2, diff/motion thresholds,
  hotspot, peak, sticky, speed/area filters;
- слабые клипы Act5 уперлись в detector/data, поэтому detector changes без
  synthetic unit coverage будут плохо диагностироваться.

Минимальный test scope:

| Test area | Synthetic input | Expected assertion |
|-----------|-----------------|--------------------|
| Warmup contract | Несколько черных BGR frames | До `NIGHT_HIST_LEN` detector возвращает `[]`. |
| Moving small bright target | Черный фон, яркая точка/квадрат с малым сдвигом по кадрам | После confirm появляется detection с `source="night"` и bbox рядом с целью. |
| Border rejection | Такая же цель у края кадра | Detection rejected по `NIGHT_BORDER`. |
| Area filter | Слишком маленький и слишком большой blob | Rejected по `NIGHT_MIN_AREA` / `NIGHT_MAX_AREA`. |
| Candidate key collision | Две близкие точки в одной grid cell | Кандидаты не схлопываются в один счетчик; проверяется BUG-005 contract. |
| Sticky selection | Две detections с разным score, активная цель рядом с прошлым key | Sticky mode удерживает active target вместо случайного score jump. |
| Peak/hotspot path | `NIGHT_PEAK_ENABLED=True`, static bright spot with controlled top-hat response | `_peak_rows` дает bounded bbox и obeys `TOP_K` / NMS. |

Рекомендуемый файл: `tests/test_night_small_target_detector.py`.

Тесты должны строить кадры через `numpy`, без видеофайлов и без YOLO weights.

## 2. Offscreen UI Sanity

Текущее состояние:

- `tests/test_qml_app_state.py` уже выставляет `QT_QPA_PLATFORM=offscreen`;
- `python_scripts/smoke_qml_mvp.py` умеет прогонять QML bridge без открытия окна;
- `.github/workflows/ci.yml` сейчас ставит только `pytest pytest-cov`, поэтому
  PySide6-dependent tests могут быть нестабильны или невозможны в clean CI.

Минимальный CI proposal:

1. Оставить основной pytest job легким.
2. Добавить отдельный optional/manual или guarded job для UI sanity:
   - install minimal UI deps only there;
   - `QT_QPA_PLATFORM=offscreen`;
   - run `python python_scripts/smoke_qml_mvp.py --duration-ms 1500 --min-frames 1`
     only if `test_videos/cli_smoke_test.mp4` exists.
3. Если PySide6 не установлен, job должен явно report skip, а не молча
   маскировать отсутствие UI coverage.

## 3. Pipeline Smoke Proposal

Перед следующей detector/training итерацией нужен быстрый runtime smoke, который
проверяет не качество модели, а целостность wiring:

| Smoke | Command | Gate |
|-------|---------|------|
| Orchestrator state | `python3 orchestrator/scripts/check_orchestration_state.py` | exit 0 |
| Compile | `python3 -m compileall -q python_scripts src app orchestrator tests` | exit 0 |
| Target Lab tooling | `PYTHONPATH=src python python_scripts/run_tracking_gt_diagnostics.py --help` | exit 0 |
| Detector evidence tool | `PYTHONPATH=src python python_scripts/build_detector_evidence_pack.py --help` | exit 0 |
| QML bridge | `python python_scripts/smoke_qml_mvp.py --duration-ms 1500 --min-frames 1` | exit 0 or explicit skipped due missing PySide6/video |

## 4. No-Go Rules

- Не менять detector thresholds ради тестов.
- Не добавлять video fixtures в git без отдельного решения.
- Не делать UI smoke mandatory в CI, пока PySide6 dependency policy не
  подтверждена.
- Не возвращаться к TASK-20260517-108, пока NightSmallTargetDetector test scope
  не принят или явно не отложен Human decision.
