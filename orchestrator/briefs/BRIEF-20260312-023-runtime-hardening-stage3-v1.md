# BRIEF: BRIEF-20260312-023-runtime-hardening-stage3-v1

Brief ID: BRIEF-20260312-023
Date: 2026-03-12
Owner: Codex Mac
Status: Active

## Summary

The first two runtime-hardening cycles improved IR behavior and made the tuning/evidence loop more disciplined, but they did not close the operator-facing false-lock problem on noisy night scenes. The clearest remaining weak points are `night_ground_indicator_lights` and `night_ground_large_drones`, with the latter regressing sharply during stage-2.

This cycle focuses on one narrow objective: improve night/noise runtime behavior without opening a new training cycle or another architecture refactor.

## Why Now

- The local desktop product is structurally stronger after the previous audit-driven cycles.
- The main remaining blocker is not code organization, but runtime behavior on noisy night scenes.
- A new training cycle before stabilizing these scenes would produce new candidates against the same runtime barrier.

## Scope

In scope:
- narrow runtime hardening for noise-like night scenes
- focused stabilization for `night_ground_large_drones`
- a short threshold-based problem-pack mini-gate

Out of scope:
- new training cycle
- new UI redesign
- `pipeline.py` / `main_gui.py` deeper refactor
- Hailo / RPi migration
- automation expansion

## Tasks In This Brief

- `TASK-20260312-067` — night-noise scene classification gating
- `TASK-20260312-068` — large-drones night stability fix
- `TASK-20260312-069` — problem-pack threshold contract

## Acceptance

- noise-like night scenes are treated more explicitly instead of being folded into one coarse `night` behavior
- `night_ground_large_drones` no longer shows runaway `id_changes/min` behavior in the canonical short loop
- a short problem-pack mini-gate exists with explicit thresholds and reproducible outputs

## Risks

- Over-tightening noise gating can suppress weak true targets.
- Fixing `indicator_lights` and `large_drones` with one coarse preset change can create new regressions.
- The cycle must stay narrowly runtime-focused; no hidden redesign or training work should leak in.
