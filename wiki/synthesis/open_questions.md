# Open Questions

> Unresolved issues and missing knowledge, ordered by priority

## High Priority

### OQ-001 — Dataset Composition of drone-bird-yolo

**Question:** What fraction of the `drone-bird-yolo` dataset is IR/thermal vs visible-light night?

**Why it matters:** The curriculum rejection was attributed to IR-dominant training causing
visible-light night regression. But the composition has not been audited. If the hypothesis
is wrong, the training reset strategy may be misdirected.

**How to answer:** Inspect `automation/state/dataset_registry.json` and the actual dataset
contents on RTX. Count clips/frames by scene type.

**Blocking:** Any new training strategy decision.

---

### OQ-002 — IR Gate Thresholds

**Question:** What are the formal false_lock and id_chg/min thresholds for the IR context?

**Why it matters:** IR gate is currently measured as reference only. `baseline.pt` was
installed with IR gate as an "open issue." Without formal thresholds, IR quality cannot be
tracked or used as a promotion criterion.

**How to answer:** Analyze IR clip measurements (Demo_IR_DRONE_146, IR_BIRD_001, IR_BIRD_002)
and define achievable thresholds that represent acceptable operator performance.

**Blocking:** Formal IR quality governance.

---

### OQ-003 — Day Clip False Lock

**Question:** Why does `drone_closeup_mixkit_44644_360.mp4` always show false_lock=1.000,
regardless of model or runtime config?

**Why it matters:** The day gate is effectively non-functional. If a model degraded on day
scenarios, we would not detect it through the current regression pack.

**Hypothesis:** Drone exits frame very quickly; all remaining frames have no target present,
inflating false_lock rate.

**How to answer:** Inspect the clip manually or measure frame-by-frame detection presence.
If confirmed, replace or augment with a better day regression clip.

**Blocking:** Reliable day quality gate.

---

## Medium Priority

### OQ-004 — night_confirm Value in OPERATOR_BASELINE.md

**Question:** Is `night_confirm=4` or `night_confirm=5` the accepted AP-025 value?

**Status:** CONTRADICTION exists.
- `OPERATOR_BASELINE.md` shows `night_confirm=4` labeled as AP-025.
- `project_state.md` and `decision_log.json` both record `night_confirm=5` for the accepted PASS.
- The night PASS measurements (false_lock=0.510) are definitively attributed to `night_confirm=5`.

**Likely resolution:** `OPERATOR_BASELINE.md` was not updated after AP-025 final tuning sweep.
Trust `night_confirm=5` (the value that produced the PASS measurements).

**How to answer:** Check the actual `configs/night.yaml` value in the current codebase.

---

### OQ-005 — Baseline.pt Installation Verification

**Question:** Is `models/baseline.pt` and `models/baseline_manifest.json` actually present
and consistent with the AP-025 runtime state?

**Context:** Installation was performed in AP-026 autonomous session. The decision_log.json
records the decision, but the physical files should be verified.

**How to answer:** `python_scripts/install_baseline.py --verify` or manual file check.

---

### OQ-006 — Architecture Refactor Scope

**Question:** What is the plan for completing the `pipeline.py` / `main_gui.py` refactor?

**Context:** AP-016 and AP-017 did stage-0/stage-1 splits (1308→1067 lines for pipeline,
1660→1598 for GUI). Both files remain large and tightly coupled. A full architecture
matching `PROJECT_ARCHITECTURE.md` is still aspirational.

**Not blocking:** Current runtime is stable. This is a code quality / maintainability issue.

---

## Low Priority

### OQ-007 — Hailo/RPi5 Migration Path

**Question:** What is the concrete migration plan for Raspberry Pi 5 + Hailo deployment?

**Context:** `hailo_backend.py` is referenced in architecture but not yet implemented.
This is the long-term deployment target.

**Not blocking:** macOS runtime is the current product focus.

---

## Answered Questions (for reference)

| Question | Answer | Source |
|----------|--------|--------|
| Can night gate be passed with current model? | Yes — AP-025 first PASS | AP-025 |
| Is drone-bird-yolo curriculum promotable? | No — reject_and_reset | AP-026 |
| What is the root cause of false-lock on large-target night? | night detector level, not lock policy | AP-025 adversarial review |
| Does `models/baseline.pt` need to be present? | No — fallback to `drone_bird_probe_fast` via `resolve_model_path()` | AP-026 |

## Related

- [current_state.md](current_state.md) — overall project status
- [model_decisions.md](../decisions/model_decisions.md) — training decisions
- [quality_gates.md](../concepts/quality_gates.md) — gate status
