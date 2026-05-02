"""Unit tests for ActionPolicy (ALG-001 v1)."""
from __future__ import annotations

import pytest

from uav_tracker.tracking.action_policy import ActionPolicy, TrackingAction
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
