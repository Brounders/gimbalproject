"""TASK-119 — Guarded primary-source semantics for night detector targets."""
from __future__ import annotations

from uav_tracker.config import Config
from uav_tracker.detection_source import DetectionSource
from uav_tracker.tracking.target_manager import TargetManager


def _night_det(cx: int = 40, cy: int = 30) -> dict:
    return {
        "bbox": (cx - 5, cy - 5, cx + 5, cy + 5),
        "cx": cx,
        "cy": cy,
        "conf": 0.6,
        "_key": (cx // 8, cy // 8, 0),
    }


def test_night_source_is_not_primary_by_default():
    cfg = Config(
        LOCK_CONFIRM_FRAMES=2,
        DRONE_REACQUIRE_SCORE_MIN=0.48,
        DRONE_LOCK_SCORE_MIN=0.62,
        NIGHT_PRIMARY_SOURCE_ENABLED=False,
    )
    mgr = TargetManager(cfg)

    seen = mgr.update_from_night([_night_det()], primary_ids=set())
    mgr.update_from_night([_night_det(42, 31)], primary_ids=set())
    mgr.pick_active_by_trust(scene="ir")

    assert seen
    assert mgr.has_confirmed_drone_lock() is False


def test_night_source_can_be_guarded_primary_when_enabled():
    cfg = Config(
        LOCK_CONFIRM_FRAMES=2,
        DRONE_REACQUIRE_SCORE_MIN=0.48,
        DRONE_LOCK_SCORE_MIN=0.62,
        NIGHT_PRIMARY_SOURCE_ENABLED=True,
        NIGHT_PRIMARY_DRONE_SCORE=0.70,
    )
    mgr = TargetManager(cfg)

    mgr.update_from_night([_night_det()], primary_ids=set())
    mgr.update_from_night([_night_det(42, 31)], primary_ids=set())
    mgr.pick_active_by_trust(scene="ir")

    active = mgr.get_active_target()
    assert active is not None
    assert active.source == DetectionSource.NIGHT
    assert active.drone_score >= cfg.DRONE_LOCK_SCORE_MIN
    assert mgr.has_confirmed_drone_lock() is True
