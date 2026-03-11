Use `$gimbal-codex-automation-conveyor` and `$gimbal-quality-gate`.

If you duplicate this prompt into a Codex App Automation, keep it literal and do not leave unresolved placeholder tokens.

Goal: fetch exactly one published artifact on Mac, benchmark it, run quality gate, and record the decision.

Steps:
1. `git pull --ff-only origin main`
2. `./tracker_env/bin/python python_scripts/fetch_training_artifact.py --manifest automation/state/artifact_manifest.json --output-dir imports`
3. Run benchmark and quality gate against the fetched artifact using explicit `--model` override.
4. Decide `promote`, `hold_and_tune`, or `reject`.
5. Record the decision with `./tracker_env/bin/python python_scripts/training_conveyor.py record-decision ...`
6. Commit and push only updated manifests/decision logs and review notes.

Constraints:
- Evaluate one artifact per run.
- Never change canonical operator presets just to evaluate a candidate.
- Keep the artifact itself out of `main`.
