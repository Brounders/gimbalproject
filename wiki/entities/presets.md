# Presets

> YAML-driven runtime configurations for each operator context

## Canonical Operator Modes

| Operator Button | Preset | Night Override | Auto Scene |
|----------------|--------|----------------|------------|
| **Авто** | `default` | preset default | ✅ Day/Night/IR heuristic |
| **День** | `default` | `False` (off) | ❌ |
| **Ночь** | `night` | preset default | ❌ |
| **IR** | `antiuav_thermal` | preset default | ❌ |

Source: `app/main_gui.py → CANONICAL_OPERATOR_MODES`

## Preset Files

| Preset | File | conf_thresh | imgsz | night_enabled |
|--------|------|-------------|-------|---------------|
| `default` | `configs/default.yaml` | 0.30 | 640 | True |
| `night` | `configs/night.yaml` | 0.12 | 960 | True |
| `antiuav_thermal` | `configs/antiuav_thermal.yaml` | 0.12 | 960 | True |
| `small_target` | `configs/small_target.yaml` | 0.15 | 960 | True |

## Full Parameter Comparison (accepted runtime, AP-025)

| Parameter | day (default) | night | ir (antiuav_thermal) |
|-----------|--------------|-------|---------------------|
| `conf_thresh` | 0.30 | 0.12 | 0.12 |
| `imgsz` | 640 | 960 | 960 |
| `lock_confirm_frames` | 5 | **7** | **7** |
| `lock_lost_grace` | 2 | **1** | **1** |
| `lock_mode_release_frames` | 6 | **4** | **4** |
| `lock_reacquire_dist` | 120 | **90** | **90** |
| `drone_lock_score_min` | 0.62 | **0.64** | **0.60** |
| `drone_reacquire_score_min` | 0.48 | **0.52** | **0.48** |
| `active_id_switch_cooldown_frames` | 30 | **60** | 30 |
| `track_state_acquire_frames` | 3 | **4** | 3 |
| `lock_mode_acquire_frames` | 2 | **3** | 2 |
| `active_id_switch_allow_if_lost_frames` | 6 | **12** | 6 |
| `track_state_lost_frames` | 8 | **12** | 8 |
| `lock_tracker_min_score` | 0.42 | **0.52** | 0.42 |
| `class_ema_alpha` | 0.18 | **0.15** | 0.24 |
| `budget_target_fps` | 24.0 | 22.0 | 20.0 |
| `velocity_alpha` | 0.55 | 0.68 | 0.72 |
| `night_max_area` | 200 | **220** | 200 |
| `night_track_dist` | 42 | **65** | 42 |
| `night_lost_max` | 8 | 8 | 8 |
| `night_confirm` | 3 | **5** | 3 |

> ⚠️ CONTRADICTION: `OPERATOR_BASELINE.md` shows `night_confirm=4` for AP-025, but
> `project_state.md` and `decision_log.json` both record `night_confirm=5` as the accepted
> AP-025 runtime state. The PASS measurements (false_lock=0.510) are attributed to
> `night_confirm=5`. Trust `night_confirm=5` as correct.

## YAML Override Mechanism

Presets are loaded via `profile_io.py::apply_overrides()`. Only parameters present in the
`apply_overrides` mapping are overrideable from YAML. Parameters not in the mapping remain
at their code defaults regardless of YAML content.

New YAML keys added over time:
- AP-018: `lock_confirm_frames`
- AP-019: `lock_lost_grace`, `lock_reacquire_dist`
- AP-024: `night_max_area`, `night_track_dist`, `night_lost_max`, `night_confirm`, `night_max_ar`

## Related

- [lock_policy.md](../concepts/lock_policy.md) — what each parameter does
- [detection_pipeline.md](../concepts/detection_pipeline.md) — where parameters are applied
- [runtime_hardening.md](../concepts/runtime_hardening.md) — how values were determined
