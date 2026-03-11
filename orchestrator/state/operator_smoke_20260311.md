# Operator Smoke Snapshot — 2026-03-11

## Command
- `PYTHONPATH=src ./tracker_env/bin/python python_scripts/run_quick_kpi_smoke.py --sources test_videos/drone_closeup_mixkit_44644_360.mp4,test_videos/night_ground_large_drones.mp4,test_videos/Demo_IR_DRONE_146.mp4,test_videos/IR_BIRD_001.mp4 --max-frames 180 --preset default`

## Aggregate
- `avg_fps=85.2`
- `active_id_changes_per_min=14.68`
- `lock_switches_per_min=0.00`
- `false_lock_rate=0.724`

## Per-clip Highlights
- `drone_closeup_mixkit_44644_360.mp4`
  - `fps=164.8`
  - `id_chg/min=0.00`
  - `false_lock_rate=1.000`
- `night_ground_large_drones.mp4`
  - `fps=59.5`
  - `id_chg/min=58.72`
  - `false_lock_rate=0.861`
- `Demo_IR_DRONE_146.mp4`
  - `fps=55.0`
  - `id_chg/min=0.00`
  - `false_lock_rate=0.556`
- `IR_BIRD_001.mp4`
  - `fps=61.5`
  - `id_chg/min=0.00`
  - `false_lock_rate=0.478`

## Interpretation
- Current `default` operator baseline remains acceptable on bright day footage.
- Weak scenes are still night/IR/noise heavy.
- Immediate pressure point is not FPS, but false-lock and ID instability on night clips.
