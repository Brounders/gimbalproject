# Current State

> Where the project stands as of 2026-04-24 (last ingested: AP-026, 2026-03-13)

## Project Mission

Stable UAV detection and tracking system (day/night/IR) for local desktop operation,
with future deployment on Raspberry Pi 5 + Hailo.

## Phase

**stabilization-first** — runtime quality hardening and model governance complete for current cycle.
Next phase requires explicit human approval.

## Runtime Status — STABLE

| Context | Gate | Status |
|---------|------|--------|
| Night | false_lock < 0.55, id_chg/min < 18.0 | **PASS** (AP-025) |
| IR | — | Open issue (no formal threshold) |
| Day | structural | false_lock=1.000 on day clip — clip issue, not runtime issue |

Current runtime contract: AP-025 (`night_confirm=5`, `night_track_dist=65`, `lock_lost_grace=1`).

## Model Status

| Model | Status |
|-------|--------|
| `drone_bird_probe_fast` → `models/baseline.pt` | **Installed** (AP-026) |
| `drone-bird-yolo` curriculum | **Rejected** (reject_and_reset_training_strategy) |

`models/baseline.pt` is present (installed in AP-026 autonomous session).
SHA256: `bedc77fe7b899de1ac68ae654f49fcee6301a9d3f8a61e9eff5c1e8d66641d44`

## Architecture Status

| Component | State |
|-----------|-------|
| `src/uav_tracker/pipeline.py` | 1067 lines (was 1308, AP-016 extracted `FrameOutput` + `overlay`) |
| `app/main_gui.py` | 1598 lines (was 1660, AP-017 extracted `theme.py` + `cards.py`) |
| `app/ui/theme.py` | Extracted; canonical `APP_STYLESHEET` source |
| `app/ui/cards.py` | Extracted; display-card factories |
| `src/uav_tracker/frame_result.py` | Extracted; `FrameOutput` dataclass |
| `src/uav_tracker/overlay.py` | Extracted; draw helpers |

> `app/main_gui.py` and `src/uav_tracker/pipeline.py` remain large and tightly coupled.
> Full architecture refactor planned but not yet scoped.

## Active Plan

AP-026 is **completed**. No active tasks. Backlog is empty.

The next cycle must be opened explicitly by the human (Bround) from the approved next steps.

## Recommended Next Steps (AP-026, not yet approved)

1. **Audit drone-bird-yolo dataset composition** — count IR vs visible-light night clips.
   This is the prerequisite for any training strategy reset.

2. **Verify baseline installation** — confirm `models/baseline.pt` and `baseline_manifest.json`
   are correct and consistent with the AP-025 runtime state.

3. **Decide training strategy** — after dataset audit, choose one of:
   - Re-train from scratch with balanced dataset (night visible-light + IR)
   - Fine-tune `drone_bird_probe_fast` on problem cases
   - Other approach per dataset audit findings

4. **IR gate formalization** — define thresholds and add IR clips to formal gate contract.

## Agent Topology

| Role | Agent |
|------|-------|
| Orchestrator (strategic decisions) | Human (Bround) |
| Architect/planner/reviewer | Codex Mac |
| Implementation lead | Claude Mac |
| Training/evaluation worker | Codex RTX |

## Related

- [open_questions.md](open_questions.md) — unresolved issues
- [model_decisions.md](../decisions/model_decisions.md) — formal decision record
- [training_strategy.md](../concepts/training_strategy.md) — training context
