# TASK-20260517-125 — Static-text rejection / motion-aware target validity intake

## Status

Accepted as the next active no-training direction.

## Human correction

The OSD-wide ignore-zone fix is useful for historical diagnostic clips that
contain embedded telemetry text, but it is not the right live-tracking strategy.
Live video should not depend on hand-drawn text exclusion zones.

The real question is: why can the tracker prefer a static high-contrast text
region over a moving, active, contrast target?

## Current code finding

The active target selector is still primarily a source/trust + geometry scorer:

- `TargetManager.pick_active_by_trust()` ranks proposals from
  `build_proposals()`.
- `build_proposals()` scores `conf + drone_score + hit_streak - lost_penalty`,
  then multiplies by scene/source trust.
- `TargetEvidence` already defines `motion_score`, `appearance_score`,
  `trajectory_score`, and `scale_score`, but this evidence model is not the
  active selector path.
- `NightSmallTargetDetector` has temporal motion masking for night proposals,
  but the final active-target decision does not require the selected target to
  demonstrate temporal motion, trajectory plausibility, or non-static behavior.

This means a static text/overlay patch can become a strong candidate if it is
bright, stable, and repeatedly detected.

## Decision

Do not propagate the wide OSD ignore zone into `tracking_live_auto` as the main
operator strategy.

Keep `antiuav_thermal_peak` OSD-wide behavior as a diagnostic/test-clip safety
patch only.  Open the next active task on target-validity logic:

1. measure motion evidence for each active/candidate bbox;
2. penalize candidates that are static for multiple frames unless backed by a
   strong primary detector;
3. require moving/active evidence for weak sources such as `night`, `roi`, and
   `lock` during acquisition/reacquisition;
4. validate by A/B against weak4 and regression IR/day/noise packs.

## Non-goals

- No RTX training.
- No model replacement.
- No physical folder restructure.
- No runtime code change in this intake step.

## Proposed bounded implementation after approval

Add a default-off `STATIC_TARGET_REJECTION_ENABLED` candidate gate with
telemetry first:

- bbox-local frame-difference motion ratio;
- static-frame streak per tracked target;
- selector penalty for weak-source candidates with low motion and no primary
  detector support;
- diagnostic counters in `FrameOutput`/reports before promotion.

Promotion requires:

- weak4 off-target reduction on OSD/text clips;
- no regression on `9_dji2_range_medium`;
- no day/EO regression;
- no protected noise regression;
- acceptable FPS impact.
