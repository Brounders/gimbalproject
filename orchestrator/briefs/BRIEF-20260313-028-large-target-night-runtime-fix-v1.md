# Brief ID
- BRIEF-20260313-028

# Title
- Large-Target Night Runtime Fix v1

# Why Now
- The project has cleared the major structural and governance items from audit `032`.
- The dominant remaining operator-facing defect is still the `night_ground_large_drones` scenario.
- Current stage-4b / detector-contract work improved bounded behavior and reduced some churn, but the large-target night case still remains above acceptable runtime quality levels.
- Opening a new training cycle before resolving this runtime barrier would likely produce another candidate that fails the same night/noise gate.

# Scope
- Runtime-only, narrow cycle focused on the large-target night problem.
- No training, no UI redesign, no GUI refactor, no `pipeline.py` refactor, no embedded/Hailo work.

# Objectives
1. Strengthen continuity gating for already-held large night targets.
2. Harden reacquire/release behavior specifically for large-target night scenes.
3. Produce a reproducible before/after evidence artifact and hard-gate verdict for the large-target night case, with explicit no-regression check on `night_ground_indicator_lights`.

# Constraints
- Keep diffs minimal and reversible.
- Do not broaden this cycle into a global `night` retune.
- Do not change training or automation flows.
- Do not regress the bounded `indicator_lights` behavior achieved in prior cycles.

# Acceptance Focus
- `night_ground_large_drones` improves relative to the current accepted point.
- `night_ground_indicator_lights` does not regress.
- The cycle yields one clear engineering verdict based on reproducible local evidence.
