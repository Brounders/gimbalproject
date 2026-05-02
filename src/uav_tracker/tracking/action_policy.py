"""ActionPolicy — deterministic tracking action selector (ALG-001 v1).

Maps a TargetBelief + lock_score to one of TrackingAction values.
No ML, no randomness; pure thresholded rules.

Two layers:

1. Decision (`ActionPolicy.decide`) — deterministic, side-effect free, always
   produced as telemetry.
2. Behavior intent (`select_behavior_intent`) — guarded, off by default.
   The pipeline only acts on the intent when the explicit
   `Config.ACTION_POLICY_BEHAVIOR_ENABLED` flag is set.  When OFF the layer
   is pure telemetry and pipeline behavior is identical to the pre-existing
   TemplateLockTracker / TargetManager path.

The IR-first night gate semantics are encoded in TargetBelief.modality.
Behavior wiring is intentionally conservative: it can only ADD a drop
signal (release a clearly-stale lock one tick earlier), never extend hold.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from uav_tracker.tracking.evidence import TargetBelief


class TrackingAction(str, Enum):
    KEEP_LOCK = 'keep_lock'
    LOCAL_VALIDATE = 'local_validate'
    EXPAND_ROI = 'expand_roi'
    GLOBAL_RESCAN = 'global_rescan'
    REDETECT = 'redetect'
    DROP_LOCK = 'drop_lock'


# Behavior intent strings — kept as plain strings (not Enum) so they can be
# safely embedded in FrameOutput.decision_path for telemetry consumers.
BEHAVIOR_TELEMETRY_ONLY = 'telemetry_only'
BEHAVIOR_OBSERVE = 'behavior_guarded:observe'
BEHAVIOR_FORCE_DROP = 'behavior_guarded:force_drop'


def select_behavior_intent(action: 'TrackingAction', behavior_enabled: bool) -> str:
    """Pure mapping action -> behavior intent string.

    When `behavior_enabled` is False (default), always returns
    `BEHAVIOR_TELEMETRY_ONLY` and the pipeline must not act on the action.

    When True, only DROP_LOCK currently has a behavioral effect; every other
    action keeps the pre-existing TargetManager/LockTracker path intact
    (`BEHAVIOR_OBSERVE`).  This conservative mapping guarantees that enabling
    the flag never extends a lock; it can only drop a clearly-stale lock one
    tick earlier than the natural age-based drop.
    """
    if not behavior_enabled:
        return BEHAVIOR_TELEMETRY_ONLY
    if action == TrackingAction.DROP_LOCK:
        return BEHAVIOR_FORCE_DROP
    return BEHAVIOR_OBSERVE


@dataclass
class ActionPolicy:
    """Threshold-based, side-effect-free policy.

    Thresholds are deliberately decoupled from runtime Config so that
    tuning this layer cannot drift current preset thresholds.
    """
    keep_reliability_min: float = 0.60
    keep_lost_age_max: int = 2
    validate_reliability_min: float = 0.30
    validate_lost_age_max: int = 4
    validate_lock_score_max: float = 0.55
    expand_lost_age_max: int = 8
    drop_reliability_max: float = 0.10
    drop_lost_age_min: int = 12
    rescan_lost_age_min: int = 9

    def decide(
        self,
        belief: TargetBelief,
        lock_score: float,
        needs_recovery: bool = False,
    ) -> TrackingAction:
        if belief.active_id is None:
            return TrackingAction.GLOBAL_RESCAN

        if needs_recovery:
            return TrackingAction.REDETECT

        if (
            belief.reliability < self.drop_reliability_max
            and belief.lost_age >= self.drop_lost_age_min
        ):
            return TrackingAction.DROP_LOCK

        if belief.lost_age >= self.rescan_lost_age_min:
            return TrackingAction.GLOBAL_RESCAN

        if (
            belief.reliability >= self.keep_reliability_min
            and belief.lost_age <= self.keep_lost_age_max
            and lock_score >= self.validate_lock_score_max
        ):
            return TrackingAction.KEEP_LOCK

        if (
            belief.reliability >= self.validate_reliability_min
            and belief.lost_age <= self.validate_lost_age_max
        ):
            return TrackingAction.LOCAL_VALIDATE

        if belief.lost_age <= self.expand_lost_age_max:
            return TrackingAction.EXPAND_ROI

        return TrackingAction.GLOBAL_RESCAN
