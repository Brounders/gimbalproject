"""Unit tests for TargetEvidence/TargetBelief (ALG-001 v1)."""
from __future__ import annotations

import pytest

from uav_tracker.tracking.evidence import (
    SOURCE_RELIABILITY,
    TargetBelief,
    TargetEvidence,
    compute_total_score,
)


class TestComputeTotalScore:
    def test_clamps_to_unit_interval_high(self):
        s = compute_total_score(
            detector_score=10.0,
            motion_score=10.0,
            appearance_score=10.0,
            trajectory_score=10.0,
            scale_score=10.0,
            source_reliability=2.0,
        )
        assert 0.0 <= s <= 1.0
        assert s == 1.0

    def test_clamps_to_unit_interval_low(self):
        s = compute_total_score(
            detector_score=-10.0,
            motion_score=-10.0,
            appearance_score=-10.0,
            trajectory_score=-10.0,
            scale_score=-10.0,
            source_reliability=-1.0,
        )
        assert s == 0.0

    def test_zero_inputs_zero_score(self):
        s = compute_total_score(0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
        assert s == 0.0


class TestTargetEvidence:
    def test_total_score_in_range(self):
        ev = TargetEvidence(
            source='yolo',
            bbox=(10, 10, 50, 50),
            track_id=1,
            cls_id=0,
            conf=0.9,
            detector_score=0.9,
            motion_score=0.5,
            appearance_score=0.7,
            trajectory_score=0.6,
            scale_score=0.5,
            source_reliability=SOURCE_RELIABILITY['yolo'],
        )
        assert 0.0 <= ev.total_score <= 1.0

    def test_reliable_yolo_beats_weak_motion(self):
        yolo_ev = TargetEvidence(
            source='yolo',
            bbox=(10, 10, 50, 50),
            track_id=1,
            cls_id=0,
            conf=0.9,
            detector_score=0.9,
            motion_score=0.3,
            appearance_score=0.7,
            trajectory_score=0.6,
            scale_score=0.5,
            source_reliability=SOURCE_RELIABILITY['yolo'],
        )
        night_ev = TargetEvidence(
            source='night',
            bbox=(10, 10, 50, 50),
            track_id=None,
            cls_id=-1,
            conf=0.0,
            detector_score=0.0,
            motion_score=0.4,
            appearance_score=0.0,
            trajectory_score=0.1,
            scale_score=0.2,
            source_reliability=SOURCE_RELIABILITY['night'],
        )
        assert yolo_ev.total_score > night_ev.total_score

    def test_unknown_source_default_reliability(self):
        ev = TargetEvidence(
            source='unknown_xyz',
            bbox=None,
            track_id=None,
            cls_id=-1,
            conf=0.0,
            detector_score=0.0,
            motion_score=0.0,
            appearance_score=0.0,
            trajectory_score=0.0,
            scale_score=0.0,
            source_reliability=0.0,
        )
        assert ev.total_score == 0.0


class TestTargetBelief:
    def test_default_no_target_belief_low_reliability(self):
        belief = TargetBelief.empty()
        assert belief.active_id is None
        assert belief.bbox is None
        assert belief.p_present == 0.0
        assert belief.reliability == 0.0
        assert belief.lost_age == 0

    def test_belief_high_reliability_for_fresh_yolo(self):
        belief = TargetBelief(
            active_id=1,
            bbox=(10, 10, 50, 50),
            last_good_bbox=(10, 10, 50, 50),
            velocity=(0.0, 0.0),
            scale=1.0,
            p_present=0.9,
            p_same_target=0.9,
            reliability=0.85,
            lost_age=0,
            source='yolo',
        )
        assert belief.reliability >= 0.6
        assert belief.lost_age == 0
