"""Unit tests for ActionPolicy (ALG-001 v1) + guarded behavior wiring (v1.1)."""
from __future__ import annotations

import pytest

from uav_tracker.tracking.action_policy import (
    BEHAVIOR_FORCE_DROP,
    BEHAVIOR_OBSERVE,
    BEHAVIOR_TELEMETRY_ONLY,
    ActionPolicy,
    TrackingAction,
    select_behavior_intent,
)
from uav_tracker.tracking.evidence import TargetBelief


def _belief(**kwargs) -> TargetBelief:
    base = dict(
        active_id=1,
        bbox=(10, 10, 50, 50),
        last_good_bbox=(10, 10, 50, 50),
        velocity=(0.0, 0.0),
        scale=1.0,
        p_present=0.9,
        p_same_target=0.9,
        reliability=0.8,
        lost_age=0,
        source='yolo',
    )
    base.update(kwargs)
    return TargetBelief(**base)


class TestActionPolicy:
    def test_no_active_target_returns_global_rescan(self):
        policy = ActionPolicy()
        action = policy.decide(TargetBelief.empty(), lock_score=0.0)
        assert action == TrackingAction.GLOBAL_RESCAN

    def test_high_reliability_active_returns_keep_lock(self):
        policy = ActionPolicy()
        belief = _belief(reliability=0.85, lost_age=0)
        action = policy.decide(belief, lock_score=0.7)
        assert action == TrackingAction.KEEP_LOCK

    def test_weak_lock_but_plausible_returns_local_validate(self):
        policy = ActionPolicy()
        belief = _belief(reliability=0.45, lost_age=2)
        action = policy.decide(belief, lock_score=0.30)
        assert action == TrackingAction.LOCAL_VALIDATE

    def test_growing_lost_age_returns_expand_roi(self):
        policy = ActionPolicy()
        belief = _belief(reliability=0.40, lost_age=6)
        action = policy.decide(belief, lock_score=0.0)
        assert action == TrackingAction.EXPAND_ROI

    def test_long_lost_returns_global_rescan(self):
        policy = ActionPolicy()
        belief = _belief(reliability=0.20, lost_age=20)
        action = policy.decide(belief, lock_score=0.0)
        assert action == TrackingAction.GLOBAL_RESCAN

    def test_clearly_stale_low_reliability_returns_drop_lock(self):
        policy = ActionPolicy()
        belief = _belief(reliability=0.05, lost_age=30)
        action = policy.decide(belief, lock_score=0.0)
        assert action == TrackingAction.DROP_LOCK

    def test_redetect_when_recovery_requested(self):
        policy = ActionPolicy()
        belief = _belief(reliability=0.5, lost_age=2)
        action = policy.decide(belief, lock_score=0.2, needs_recovery=True)
        assert action == TrackingAction.REDETECT

    def test_action_is_deterministic(self):
        policy = ActionPolicy()
        belief = _belief(reliability=0.85, lost_age=0)
        results = {policy.decide(belief, lock_score=0.7) for _ in range(20)}
        assert results == {TrackingAction.KEEP_LOCK}

    def test_ir_strong_evidence_yields_keep_lock(self):
        """IR-source belief with high reliability still resolves to KEEP_LOCK.

        IR/thermal is the accepted night gate, so the baseline keep threshold
        remains valid for IR evidence.
        """
        policy = ActionPolicy()
        belief = _belief(reliability=0.85, lost_age=0, source='lock', modality='ir')
        action = policy.decide(belief, lock_score=0.7)
        assert action == TrackingAction.KEEP_LOCK

    def test_night_modality_requires_stronger_reliability_to_keep_lock(self):
        """RGB-night should not KEEP_LOCK on marginal reliability.

        The same reliability/lock_score still keeps day/IR targets, but
        visible-night is diagnostic-only and should fall back to validation.
        """
        policy = ActionPolicy()
        belief = _belief(reliability=0.65, lost_age=0, source='night', modality='night')
        action = policy.decide(belief, lock_score=0.7)
        assert action == TrackingAction.LOCAL_VALIDATE

    def test_ir_modality_keeps_lock_at_baseline_reliability(self):
        """IR is primary night evidence and must not inherit RGB-night strictness."""
        policy = ActionPolicy()
        belief = _belief(reliability=0.65, lost_age=0, source='lock', modality='ir')
        action = policy.decide(belief, lock_score=0.7)
        assert action == TrackingAction.KEEP_LOCK

    def test_night_modality_drops_stale_lock_earlier(self):
        """RGB-night stale evidence should release before generic RGB evidence."""
        policy = ActionPolicy()
        belief = _belief(reliability=0.14, lost_age=10, source='night', modality='night')
        action = policy.decide(belief, lock_score=0.0)
        assert action == TrackingAction.DROP_LOCK

    def test_weak_evidence_does_not_keep_lock(self):
        """Weak/lost evidence must NOT yield KEEP_LOCK regardless of modality."""
        policy = ActionPolicy()
        weak = _belief(reliability=0.05, lost_age=15, source='night', modality='night')
        action = policy.decide(weak, lock_score=0.0)
        assert action != TrackingAction.KEEP_LOCK

    def test_weak_night_runtime_evidence_drops_early(self):
        policy = ActionPolicy()
        belief = _belief(source='night', reliability=0.05, p_present=0.13, lost_age=1)
        action = policy.decide(belief, lock_score=0.0)
        assert action == TrackingAction.DROP_LOCK

    def test_weak_roi_runtime_evidence_drops_early(self):
        policy = ActionPolicy()
        belief = _belief(source='roi', reliability=0.15, p_present=0.35, lost_age=1)
        action = policy.decide(belief, lock_score=0.0)
        assert action == TrackingAction.DROP_LOCK

    def test_weak_yolo_evidence_is_not_suppressed_by_runtime_rule(self):
        policy = ActionPolicy()
        belief = _belief(source='yolo', reliability=0.05, p_present=0.13, lost_age=1)
        action = policy.decide(belief, lock_score=0.0)
        assert action != TrackingAction.DROP_LOCK

    def test_weak_lock_and_local_are_not_suppressed_by_runtime_rule(self):
        policy = ActionPolicy()
        for source in ('lock', 'local'):
            belief = _belief(source=source, reliability=0.15, p_present=0.35, lost_age=1)
            action = policy.decide(belief, lock_score=0.0)
            assert action != TrackingAction.DROP_LOCK


# ---------------------------------------------------------------------------
# Guarded behavior wiring (ALG-001 v1.1) — pure function tests.
# ---------------------------------------------------------------------------


class TestSelectBehaviorIntent:
    def test_off_always_returns_telemetry_only(self):
        for action in TrackingAction:
            assert select_behavior_intent(action, behavior_enabled=False) == BEHAVIOR_TELEMETRY_ONLY

    def test_on_keep_lock_is_observe(self):
        assert select_behavior_intent(TrackingAction.KEEP_LOCK, behavior_enabled=True) == BEHAVIOR_OBSERVE

    def test_on_local_validate_is_observe(self):
        assert select_behavior_intent(TrackingAction.LOCAL_VALIDATE, behavior_enabled=True) == BEHAVIOR_OBSERVE

    def test_on_expand_roi_is_observe(self):
        assert select_behavior_intent(TrackingAction.EXPAND_ROI, behavior_enabled=True) == BEHAVIOR_OBSERVE

    def test_on_global_rescan_is_observe(self):
        assert select_behavior_intent(TrackingAction.GLOBAL_RESCAN, behavior_enabled=True) == BEHAVIOR_OBSERVE

    def test_on_redetect_is_observe(self):
        assert select_behavior_intent(TrackingAction.REDETECT, behavior_enabled=True) == BEHAVIOR_OBSERVE

    def test_on_drop_lock_is_force_drop(self):
        assert select_behavior_intent(TrackingAction.DROP_LOCK, behavior_enabled=True) == BEHAVIOR_FORCE_DROP

    def test_off_drop_lock_still_telemetry(self):
        """Critical safety: even DROP_LOCK is telemetry-only when flag is off."""
        assert select_behavior_intent(TrackingAction.DROP_LOCK, behavior_enabled=False) == BEHAVIOR_TELEMETRY_ONLY
