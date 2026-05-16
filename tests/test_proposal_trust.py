"""TASK-103d — Unit tests for Unified Proposal Layer."""
from __future__ import annotations

import pytest
from types import SimpleNamespace
from uav_tracker.tracking.proposal_trust import (
    SCENE_TRUST, DEFAULT_TRUST, Proposal, source_trust, build_proposals,
)


# ---------------------------------------------------------------------------
# source_trust table tests
# ---------------------------------------------------------------------------

def test_night_ir_highest_trust():
    """night/ir must have highest trust (F5: IR truth carrier)."""
    t = source_trust("night", "ir")
    assert t >= 0.90, f"night/ir trust should be ≥0.90, got {t}"


def test_yolo_ir_heavily_demoted():
    """yolo/ir trust must be <0.4 (YOLO fires 0-2% on IR clips, F5)."""
    t = source_trust("yolo", "ir")
    assert t < 0.40, f"yolo/ir trust should be <0.40, got {t}"


def test_lock_ir_lower_than_night_ir():
    """lock/ir less trusted than night/ir (lock unreliable on RGBT, F5)."""
    assert source_trust("lock", "ir") < source_trust("night", "ir")


def test_yolo_day_highest_for_day_scene():
    """yolo/day must have highest non-operator trust for day scene."""
    sources = ["yolo", "lock", "local", "roi", "night"]
    best = max(sources, key=lambda s: source_trust(s, "day"))
    assert best == "yolo", f"Expected yolo to dominate day scene, got {best}"


def test_operator_always_1():
    """Operator trust must be 1.0 for all scenes."""
    for scene in ("ir", "day", "night"):
        t = source_trust("operator", scene)
        assert t == 1.0, f"operator/{scene} trust should be 1.0, got {t}"


def test_unknown_pair_returns_default():
    """Unknown (source, scene) falls back to DEFAULT_TRUST."""
    t = source_trust("unknown_src", "unknown_scene")
    assert t == DEFAULT_TRUST


def test_night_day_lower_than_yolo_day():
    """Night detector has low trust on day scene."""
    assert source_trust("night", "day") < source_trust("yolo", "day")


# ---------------------------------------------------------------------------
# build_proposals tests
# ---------------------------------------------------------------------------

def _fake_target(tid, source, conf=0.8, drone_score=0.7, hit_streak=5, lost_frames=0):
    t = SimpleNamespace()
    t.track_id = tid
    t.source = source
    t.raw_bbox = (0, 0, 10, 10)
    t.conf = conf
    t.drone_score = drone_score
    t.hit_streak = hit_streak
    t.lost_frames = lost_frames
    return t


def test_build_proposals_returns_sorted_descending():
    """build_proposals returns list sorted by total_score desc."""
    targets = {
        1: _fake_target(1, "yolo"),
        2: _fake_target(2, "night"),
        3: _fake_target(3, "lock"),
    }
    props = build_proposals(targets, "ir", lambda s: str(s))
    scores = [p.total_score for p in props]
    assert scores == sorted(scores, reverse=True)


def test_build_proposals_ir_scene_prefers_night():
    """On IR scene, night-source proposal should outrank yolo."""
    targets = {
        1: _fake_target(1, "yolo", conf=0.9, drone_score=0.8),
        2: _fake_target(2, "night", conf=0.7, drone_score=0.6),
    }
    props = build_proposals(targets, "ir", lambda s: str(s))
    top = props[0]
    assert top.target_id == 2, f"Expected night-source on top for IR, got source={top.source}"


def test_build_proposals_day_scene_prefers_yolo():
    """On day scene, yolo-source proposal should outrank night."""
    targets = {
        1: _fake_target(1, "yolo", conf=0.8, drone_score=0.7),
        2: _fake_target(2, "night", conf=0.8, drone_score=0.7),
    }
    props = build_proposals(targets, "day", lambda s: str(s))
    top = props[0]
    assert top.source == "yolo", f"Expected yolo on top for day scene, got {top.source}"


def test_proposal_dataclass_fields():
    """Proposal must carry trust, geo_score, total_score."""
    targets = {1: _fake_target(1, "yolo")}
    props = build_proposals(targets, "day", lambda s: str(s))
    p = props[0]
    assert p.trust > 0
    assert p.geo_score != 0
    assert p.total_score == pytest.approx(p.trust * max(0, p.geo_score))


def test_high_lost_frames_reduces_total_score():
    """Stale target with many lost frames ranks lower than fresh target."""
    targets = {
        1: _fake_target(1, "yolo", lost_frames=0),
        2: _fake_target(2, "yolo", lost_frames=15),
    }
    props = build_proposals(targets, "day", lambda s: str(s))
    assert props[0].target_id == 1, "Fresh target should rank above stale one"


# ---------------------------------------------------------------------------
# pick_active_by_trust integration test
# ---------------------------------------------------------------------------

def test_pick_active_promotes_night_over_yolo_on_ir_scene():
    """TargetManager.pick_active_by_trust promotes night source when scene=ir."""
    from uav_tracker.config import Config
    from uav_tracker.tracking.target_manager import TargetManager
    from uav_tracker.tracking.tracked_target import TrackedTarget

    cfg = Config(
        SELECT_ACTIVE_MIN_SPEED=0.0,
        DRONE_REACQUIRE_SCORE_MIN=0.3,
        ACTIVE_STRICT_LOCK_SWITCH=False,
        TRUST_SWITCH_MARGIN=0.10,  # low margin → easier to switch
    )
    mgr = TargetManager(cfg)

    # Manually insert two targets: YOLO (drone_score=0.8) and Night (drone_score=0.5)
    yolo_t = TrackedTarget(track_id=1, bbox=(0,0,10,10), raw_bbox=(0,0,10,10),
                           cx=5, cy=5, conf=0.85, drone_score=0.80, source="yolo",
                           hit_streak=8, lost_frames=0)
    night_t = TrackedTarget(track_id=2, bbox=(20,20,30,30), raw_bbox=(20,20,30,30),
                            cx=25, cy=25, conf=0.60, drone_score=0.50, source="night",
                            hit_streak=5, lost_frames=0)
    mgr.targets = {1: yolo_t, 2: night_t}
    mgr.active_id = 1  # YOLO is currently active

    # With IR scene and night trust 0.92 vs yolo trust 0.30,
    # night total_score should be > yolo total_score × 1.10 → switch
    mgr.pick_active_by_trust(scene="ir")

    assert mgr.active_id == 2, (
        f"Expected night target (id=2) to be promoted on IR scene, "
        f"but active_id={mgr.active_id}"
    )


def test_pick_active_no_switch_when_margin_not_met():
    """No switch occurs when score difference is below TRUST_SWITCH_MARGIN.

    Both targets have the same source (yolo/day) so trust is equal.
    Challenger has slightly better geo (higher conf) but not enough to
    beat the margin=1.0 (100% better required).
    """
    from uav_tracker.config import Config
    from uav_tracker.tracking.target_manager import TargetManager
    from uav_tracker.tracking.tracked_target import TrackedTarget

    cfg = Config(
        SELECT_ACTIVE_MIN_SPEED=0.0,
        DRONE_REACQUIRE_SCORE_MIN=0.3,
        ACTIVE_STRICT_LOCK_SWITCH=False,
        TRUST_SWITCH_MARGIN=1.0,   # challenger must score 2× current to switch
    )
    mgr = TargetManager(cfg)
    # Active target (id=1): yolo, good scores
    active_t = TrackedTarget(track_id=1, bbox=(0,0,10,10), raw_bbox=(0,0,10,10),
                             cx=5, cy=5, conf=0.80, drone_score=0.75, source="yolo",
                             hit_streak=8, lost_frames=0)
    # Challenger (id=2): same source, marginally better — not 2× better
    challenger_t = TrackedTarget(track_id=2, bbox=(20,20,30,30), raw_bbox=(20,20,30,30),
                                 cx=25, cy=25, conf=0.85, drone_score=0.78, source="yolo",
                                 hit_streak=6, lost_frames=0)
    mgr.targets = {1: active_t, 2: challenger_t}
    mgr.active_id = 1

    mgr.pick_active_by_trust(scene="day")

    assert mgr.active_id == 1, "Should not switch when margin threshold not met"
