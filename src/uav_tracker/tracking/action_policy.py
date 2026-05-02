"""ActionPolicy — deterministic tracking action selector (ALG-001 v1).

Maps a TargetBelief + lock_score to one of TrackingAction values.
No ML, no randomness; pure thresholded rules.

Telemetry-only by default: pipeline records the decision but does not (yet)
change behavior based on it.  Behavior wiring is reserved for a follow-up task
that must come with a quality-gate justification.
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
