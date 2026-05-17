"""TASK-103e — Tests for Lock Health Release Gate in pick_active_by_trust.

Mechanism: when the active source is persistently untrusted for the current scene
(trust < LOCK_HEALTH_MIN_TRUST) for LOCK_HEALTH_RELEASE_STREAK consecutive frames,
the active target is released (→ SCAN).  LOCK_HEALTH_RELEASE_STREAK defaults to 80
(well above the 30-frame switch cooldown) so it only fires as a last resort when
the standard 103d trust-switch has also failed to fire.

The standard 103d trust-switch path is NOT modified: _can_switch_active() is
called without force, preserving the 30-frame cooldown-based switch behaviour.
"""
from __future__ import annotations

import pytest
from uav_tracker.config import Config
from uav_tracker.tracking.target_manager import TargetManager
from uav_tracker.tracking.tracked_target import TrackedTarget


def _cfg(**kwargs):
    defaults = dict(
        SELECT_ACTIVE_MIN_SPEED=0.0,
        DRONE_REACQUIRE_SCORE_MIN=0.3,
        ACTIVE_STRICT_LOCK_SWITCH=False,
        TRUST_SWITCH_MARGIN=10.0,        # very high → no switch, only health fires
        LOCK_HEALTH_MIN_TRUST=0.50,
        LOCK_HEALTH_RELEASE_STREAK=80,
        ACTIVE_ID_SWITCH_COOLDOWN_FRAMES=30,
        ACTIVE_ID_SWITCH_ALLOW_IF_LOST_FRAMES=6,
    )
    defaults.update(kwargs)
    return Config(**defaults)


def _target(tid, source, drone_score=0.5, hit_streak=10, lost_frames=0, conf=0.75):
    return TrackedTarget(
        track_id=tid, bbox=(0, 0, 20, 20), raw_bbox=(0, 0, 20, 20),
        cx=10, cy=10, conf=conf, drone_score=drone_score,
        source=source, hit_streak=hit_streak, lost_frames=lost_frames,
    )


# ---------------------------------------------------------------------------
# Last-resort release tests
# ---------------------------------------------------------------------------

def test_last_resort_releases_after_streak():
    """No trusted alternative → lock/ir released after LOCK_HEALTH_RELEASE_STREAK frames."""
    cfg = _cfg(LOCK_HEALTH_RELEASE_STREAK=5, TRUST_SWITCH_MARGIN=10.0)
    mgr = TargetManager(cfg)
    mgr.targets = {1: _target(1, "lock")}
    mgr.active_id = 1

    for i in range(4):
        mgr.pick_active_by_trust(scene="ir")
        assert mgr.active_id == 1, f"Should not release at frame {i+1}"

    mgr.pick_active_by_trust(scene="ir")
    assert mgr.active_id is None, "Should release after 5 consecutive untrusted frames"


def test_last_resort_no_release_when_trusted():
    """yolo/day active (trust=0.85) → streak never accumulates → no release."""
    cfg = _cfg(LOCK_HEALTH_RELEASE_STREAK=3, TRUST_SWITCH_MARGIN=10.0)
    mgr = TargetManager(cfg)
    mgr.targets = {1: _target(1, "yolo")}
    mgr.active_id = 1

    for _ in range(10):
        mgr.pick_active_by_trust(scene="day")
    assert mgr.active_id == 1


def test_last_resort_no_release_for_operator():
    """Operator source trust=1.0 → never released by health gate."""
    cfg = _cfg(LOCK_HEALTH_RELEASE_STREAK=2, TRUST_SWITCH_MARGIN=10.0)
    mgr = TargetManager(cfg)
    mgr.targets = {1: _target(1, "operator", drone_score=1.0)}
    mgr.active_id = 1

    for _ in range(10):
        mgr.pick_active_by_trust(scene="ir")
    assert mgr.active_id == 1


def test_last_resort_local_ir_released():
    """local/ir trust=0.35 < 0.50 → released after streak."""
    cfg = _cfg(LOCK_HEALTH_RELEASE_STREAK=4, TRUST_SWITCH_MARGIN=10.0)
    mgr = TargetManager(cfg)
    mgr.targets = {1: _target(1, "local")}
    mgr.active_id = 1

    for i in range(3):
        mgr.pick_active_by_trust(scene="ir")
        assert mgr.active_id == 1

    mgr.pick_active_by_trust(scene="ir")
    assert mgr.active_id is None


# ---------------------------------------------------------------------------
# Streak counter behaviour
# ---------------------------------------------------------------------------

def test_streak_resets_on_set_active_id_none():
    """_set_active_id(None) resets _low_trust_streak."""
    cfg = _cfg(LOCK_HEALTH_RELEASE_STREAK=80)
    mgr = TargetManager(cfg)
    mgr.targets = {1: _target(1, "lock")}
    mgr.active_id = 1

    for _ in range(3):
        mgr.pick_active_by_trust(scene="ir")
    assert mgr._low_trust_streak == 3

    mgr._set_active_id(None)
    assert mgr._low_trust_streak == 0


def test_streak_resets_when_trusted_source_promoted():
    """After standard switch to night/ir (trust=0.92), streak resets."""
    # Use TRUST_SWITCH_MARGIN=0.10 and cooldown=0 so standard switch fires.
    cfg = _cfg(TRUST_SWITCH_MARGIN=0.10, LOCK_HEALTH_RELEASE_STREAK=80,
               ACTIVE_ID_SWITCH_COOLDOWN_FRAMES=0)
    mgr = TargetManager(cfg)
    lock_t = _target(1, "lock", hit_streak=10)
    night_t = _target(2, "night", hit_streak=10, conf=0.80)
    mgr.targets = {1: lock_t, 2: night_t}
    mgr.active_id = 1  # lock is active

    # Simulate a few frames where lock is active and streak builds
    # (here cooldown=0, so standard switch fires immediately)
    mgr.pick_active_by_trust(scene="ir")
    # Standard switch: night total=0.92*geo > lock total=0.38*geo*(1.10) → switch
    assert mgr.active_id == 2, "Standard switch should promote night/ir"
    assert mgr._low_trust_streak == 0, "Streak resets after switching to trusted night/ir"


# ---------------------------------------------------------------------------
# TASK-103f: Re-acquisition suppression after health release
# ---------------------------------------------------------------------------

def test_suppression_prevents_immediate_relock():
    """After health release, same tid is suppressed for one streak window."""
    cfg = _cfg(LOCK_HEALTH_RELEASE_STREAK=3, TRUST_SWITCH_MARGIN=10.0)
    mgr = TargetManager(cfg)
    mgr.targets = {1: _target(1, "lock")}
    mgr.active_id = 1

    # Health gate fires at frame 3
    for _ in range(3):
        mgr.pick_active_by_trust(scene="ir")
    assert mgr.active_id is None, "Health gate should release"
    assert mgr._health_released_tid == 1
    assert mgr._health_suppress_frames == 3

    # tid=1 (lock) still the only target — must stay suppressed
    for _ in range(2):
        mgr.pick_active_by_trust(scene="ir")
        assert mgr.active_id is None, "Suppressed tid must not be re-locked"

    # After suppression window expires, re-lock is allowed
    mgr.pick_active_by_trust(scene="ir")
    assert mgr.active_id == 1, "After suppression expires, re-lock is allowed"


def test_suppression_cleared_by_trusted_switch():
    """If a trusted primary-source target appears during suppression it is selected and clears suppression."""
    # Use day scene: yolo/day trust=0.85 > 0.50, yolo IS primary source → can be promoted when active=None.
    # Lock/day trust=0.50 → exactly at threshold, but use lock/ir so trust=0.38 < 0.50 to build streak.
    # Switch to day scene after health fires so yolo target can be promoted.
    cfg = _cfg(LOCK_HEALTH_RELEASE_STREAK=3, TRUST_SWITCH_MARGIN=10.0,
               ACTIVE_ID_SWITCH_COOLDOWN_FRAMES=0)
    mgr = TargetManager(cfg)
    mgr.targets = {1: _target(1, "lock")}
    mgr.active_id = 1

    # Health gate fires in IR scene (lock/ir trust=0.38 < 0.50)
    for _ in range(3):
        mgr.pick_active_by_trust(scene="ir")
    assert mgr.active_id is None
    assert mgr._health_released_tid == 1

    # Yolo target appears (different tid, primary source) — day scene, trust=0.85
    mgr.targets[2] = _target(2, "yolo", drone_score=0.6, hit_streak=10)
    mgr.pick_active_by_trust(scene="day")
    assert mgr.active_id == 2, "Trusted yolo target should be promoted"
    assert mgr._health_released_tid is None, "Suppression cleared by trusted switch"
    assert mgr._health_suppress_frames == 0


def test_suppression_cleared_by_operator_release():
    """release_active() clears the suppression window."""
    cfg = _cfg(LOCK_HEALTH_RELEASE_STREAK=10, TRUST_SWITCH_MARGIN=10.0)
    mgr = TargetManager(cfg)
    mgr.targets = {1: _target(1, "lock")}
    mgr.active_id = 1

    for _ in range(10):
        mgr.pick_active_by_trust(scene="ir")
    assert mgr._health_released_tid == 1

    mgr.release_active()  # operator releases
    assert mgr._health_released_tid is None
    assert mgr._health_suppress_frames == 0


def test_streak_preserved_when_switch_blocked_by_cooldown():
    """When cooldown blocks switch, streak accumulates each frame."""
    cfg = _cfg(TRUST_SWITCH_MARGIN=0.10, LOCK_HEALTH_RELEASE_STREAK=80,
               ACTIVE_ID_SWITCH_COOLDOWN_FRAMES=30)
    mgr = TargetManager(cfg)
    lock_t = _target(1, "lock", hit_streak=10)
    night_t = _target(2, "night", hit_streak=10, conf=0.80)
    mgr.targets = {1: lock_t, 2: night_t}
    mgr.active_id = 1
    mgr._active_switch_cooldown = 30  # simulate cooldown blocking switch

    for i in range(1, 4):
        mgr.pick_active_by_trust(scene="ir")
        assert mgr._low_trust_streak == i, f"Streak should be {i} at frame {i}"
    # Active still lock (switch blocked by cooldown)
    assert mgr.active_id == 1
