"""TASK-125 — Static high-contrast target rejection gate."""
from __future__ import annotations

from uav_tracker.config import Config
from uav_tracker.tracking.proposal_trust import build_proposals
from uav_tracker.tracking.target_manager import TargetManager
from uav_tracker.tracking.tracked_target import TrackedTarget


def _target(
    tid: int,
    source: str,
    *,
    conf: float = 0.8,
    drone_score: float = 0.6,
    hit_streak: int = 6,
    static_streak: int = 0,
    motion_score: float = 0.5,
) -> TrackedTarget:
    return TrackedTarget(
        track_id=tid,
        bbox=(0, 0, 20, 20),
        raw_bbox=(0, 0, 20, 20),
        cx=10,
        cy=10,
        conf=conf,
        drone_score=drone_score,
        hit_streak=hit_streak,
        lost_frames=0,
        source=source,
        static_streak=static_streak,
        motion_score=motion_score,
    )


def test_static_gate_off_preserves_existing_scoring():
    cfg = Config(STATIC_TARGET_REJECTION_ENABLED=False)
    targets = {
        1: _target(1, "night", static_streak=20, motion_score=0.0),
        2: _target(2, "roi", conf=0.5, drone_score=0.3, hit_streak=2, motion_score=0.9),
    }

    props = build_proposals(targets, "ir", lambda s: str(s), cfg=cfg)

    assert props[0].target_id == 1
    assert props[0].static_penalty == 1.0


def test_static_gate_penalizes_weak_static_candidate():
    cfg = Config(
        STATIC_TARGET_REJECTION_ENABLED=True,
        STATIC_TARGET_SOURCES=("night", "roi", "lock"),
        STATIC_TARGET_STREAK_MIN=3,
        STATIC_TARGET_PENALTY=0.10,
    )
    targets = {
        1: _target(1, "night", conf=0.95, drone_score=0.75, hit_streak=10, static_streak=8, motion_score=0.0),
        2: _target(2, "roi", conf=0.55, drone_score=0.30, hit_streak=2, static_streak=0, motion_score=0.8),
    }

    props = build_proposals(targets, "ir", lambda s: str(s), cfg=cfg)

    assert props[0].target_id == 2
    assert props[1].target_id == 1
    assert props[1].static_penalty == 0.10


def test_static_gate_does_not_penalize_primary_yolo():
    cfg = Config(STATIC_TARGET_REJECTION_ENABLED=True, STATIC_TARGET_STREAK_MIN=3)
    targets = {1: _target(1, "yolo", static_streak=20, motion_score=0.0)}

    props = build_proposals(targets, "day", lambda s: str(s), cfg=cfg)

    assert props[0].static_penalty == 1.0


def test_pick_active_switches_from_static_text_to_moving_candidate():
    cfg = Config(
        STATIC_TARGET_REJECTION_ENABLED=True,
        STATIC_TARGET_SOURCES=("night", "roi", "lock"),
        STATIC_TARGET_STREAK_MIN=3,
        STATIC_TARGET_PENALTY=0.10,
        ACTIVE_STRICT_LOCK_SWITCH=False,
        TRUST_SWITCH_MARGIN=0.10,
        SELECT_ACTIVE_MIN_SPEED=0.0,
        DRONE_REACQUIRE_SCORE_MIN=0.2,
    )
    mgr = TargetManager(cfg)
    static_text = _target(1, "night", conf=0.95, drone_score=0.75, hit_streak=10, static_streak=9, motion_score=0.0)
    moving_candidate = _target(2, "roi", conf=0.55, drone_score=0.35, hit_streak=3, static_streak=0, motion_score=0.8)
    mgr.targets = {1: static_text, 2: moving_candidate}
    mgr.active_id = 1

    mgr.pick_active_by_trust(scene="ir")

    assert mgr.active_id == 2
