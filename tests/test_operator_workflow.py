from __future__ import annotations

from collections import deque

from uav_tracker.config import Config
from uav_tracker.detection_source import DetectionSource
from uav_tracker.tracking.operator_workflow import OperatorWorkflowMachine, OperatorWorkflowState
from uav_tracker.tracking.tracked_target import TrackedTarget


def _target(*, hit_streak: int = 1, lost_frames: int = 0) -> TrackedTarget:
    bbox = (10, 20, 30, 40)
    return TrackedTarget(
        track_id=7,
        bbox=bbox,
        raw_bbox=bbox,
        cx=20,
        cy=30,
        conf=0.9,
        cls_id=0,
        drone_score=1.0,
        hit_streak=hit_streak,
        lost_frames=lost_frames,
        source=DetectionSource.OPERATOR,
        trail=deque(maxlen=30),
    )


def test_operator_hint_enters_verifying() -> None:
    sm = OperatorWorkflowMachine(Config(LOCK_CONFIRM_FRAMES=3))

    result = sm.update(
        frame_index=10,
        active=_target(hit_streak=1),
        visible_count=1,
        operator_override_status="verifying",
        lock_score=0.0,
        display_confidence=0.0,
        low_level_mode="SCAN",
    )

    assert result.state == OperatorWorkflowState.VERIFYING
    assert result.events == ["OPERATOR_HINT"]
    assert result.verify_age_frames == 0


def test_verifying_persists_until_track_is_confirmed() -> None:
    sm = OperatorWorkflowMachine(Config(LOCK_CONFIRM_FRAMES=3))
    sm.update(
        frame_index=10,
        active=_target(hit_streak=1),
        visible_count=1,
        operator_override_status="verifying",
        lock_score=0.0,
        display_confidence=0.0,
        low_level_mode="SCAN",
    )

    result = sm.update(
        frame_index=11,
        active=_target(hit_streak=2),
        visible_count=1,
        operator_override_status="none",
        lock_score=0.2,
        display_confidence=0.2,
        low_level_mode="TRACK",
    )

    assert result.state == OperatorWorkflowState.VERIFYING
    assert result.events == []
    assert result.verify_age_frames == 1


def test_verifying_transitions_to_tracking_with_click_to_lock_metric() -> None:
    sm = OperatorWorkflowMachine(Config(LOCK_CONFIRM_FRAMES=3))
    sm.update(
        frame_index=10,
        active=_target(hit_streak=1),
        visible_count=1,
        operator_override_status="verifying",
        lock_score=0.0,
        display_confidence=0.0,
        low_level_mode="SCAN",
    )

    result = sm.update(
        frame_index=13,
        active=_target(hit_streak=3),
        visible_count=1,
        operator_override_status="none",
        lock_score=0.5,
        display_confidence=0.5,
        low_level_mode="TRACK",
    )

    assert result.state == OperatorWorkflowState.TRACKING
    assert result.events == ["LOCK_CONFIRMED"]
    assert result.click_to_lock_frames == 3


def test_tracking_degrades_to_weak_when_unstable() -> None:
    sm = OperatorWorkflowMachine(Config(LOCK_CONFIRM_FRAMES=2))
    sm.update(
        frame_index=1,
        active=_target(hit_streak=2),
        visible_count=1,
        operator_override_status="none",
        lock_score=0.6,
        display_confidence=0.6,
        low_level_mode="TRACK",
    )

    result = sm.update(
        frame_index=2,
        active=_target(hit_streak=2),
        visible_count=1,
        operator_override_status="none",
        lock_score=0.0,
        display_confidence=0.0,
        low_level_mode="TRACK",
    )

    assert result.state == OperatorWorkflowState.WEAK_TRACK
    assert result.events == ["TRACKING_TO_WEAK_TRACK"]


def test_track_loss_emits_target_lost() -> None:
    sm = OperatorWorkflowMachine(Config(LOCK_CONFIRM_FRAMES=2, TRACK_STATE_LOST_FRAMES=4))
    sm.update(
        frame_index=1,
        active=_target(hit_streak=2),
        visible_count=1,
        operator_override_status="none",
        lock_score=0.6,
        display_confidence=0.6,
        low_level_mode="TRACK",
    )

    result = sm.update(
        frame_index=2,
        active=_target(hit_streak=2, lost_frames=5),
        visible_count=1,
        operator_override_status="none",
        lock_score=0.0,
        display_confidence=0.0,
        low_level_mode="LOST",
    )

    assert result.state == OperatorWorkflowState.LOST
    assert result.events == ["TARGET_LOST"]
