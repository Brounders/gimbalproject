"""TASK-103d — Unified Proposal Layer: scene-conditional trust table.

Provides a trust weight for each (source, scene) pair, calibrated from
the F5 diagnostic findings:

  - IR drones:   night/peak is the truth carrier  (22–93% proposal rate)
  - RGBT clips:  lock is alive but unreliable      (off-target 80%)
  - Day/EO:      yolo dominates; night near-zero
  - Negatives:   all sources 0% → trust table irrelevant

Trust is applied as a multiplier in pick_active_by_trust() to bias target
selection toward sources that are actually reliable for the current scene.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

__all__ = [
    "Proposal",
    "SCENE_TRUST",
    "DEFAULT_TRUST",
    "source_trust",
]


# ---------------------------------------------------------------------------
# Proposal dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Proposal:
    """Snapshot of a tracked-target candidate with trust-weighted scoring."""

    target_id: int
    bbox: tuple[int, int, int, int]
    source: str
    conf: float
    drone_score: float
    hit_streak: int
    lost_frames: int
    trust: float        # scene-conditional trust weight
    geo_score: float    # geometry component (conf + drone_score + streak − lost)
    total_score: float  # trust × geo_score


# ---------------------------------------------------------------------------
# Trust table  (source, scene) → float [0, 1]
# ---------------------------------------------------------------------------

# Calibrated from TASK-103a F5 findings on 14-clip GT minipack.
# Keys: (source_name, scene_label) where scene_label ∈ {'ir', 'day', 'night'}.
# '*' scene matches any scene not found in the table.
SCENE_TRUST: dict[tuple[str, str], float] = {
    # ── IR scene ────────────────────────────────────────────────────────────
    # night/peak is the truth carrier on IR drones (22–93% proposal rate).
    ("night", "ir"):    0.92,
    # yolo fires 0–2% on IR clips — heavily demote.
    ("yolo",  "ir"):    0.30,
    # lock is alive (80% on RGBT) but often locks on wrong region → demote.
    ("lock",  "ir"):    0.38,
    ("local", "ir"):    0.35,
    ("roi",   "ir"):    0.35,

    # ── Day / EO scene ───────────────────────────────────────────────────────
    # yolo dominates on day; night detector near-zero on EO.
    ("yolo",  "day"):   0.85,
    ("lock",  "day"):   0.70,
    ("local", "day"):   0.65,
    ("roi",   "day"):   0.60,
    ("night", "day"):   0.15,

    # ── Night scene ─────────────────────────────────────────────────────────
    ("night", "night"): 0.90,
    ("yolo",  "night"): 0.70,
    ("lock",  "night"): 0.62,
    ("local", "night"): 0.55,
    ("roi",   "night"): 0.50,

    # ── Operator — always fully trusted ──────────────────────────────────────
    ("operator", "ir"):    1.00,
    ("operator", "day"):   1.00,
    ("operator", "night"): 1.00,
}

DEFAULT_TRUST: float = 0.50  # fallback for unknown (source, scene) pairs


def source_trust(source: str, scene: str) -> float:
    """Return trust weight for *source* in *scene*.

    Falls back to DEFAULT_TRUST if the pair is not in SCENE_TRUST.
    """
    return SCENE_TRUST.get((source, scene), DEFAULT_TRUST)


# ---------------------------------------------------------------------------
# Helpers for pick_active_by_trust (called from TargetManager)
# ---------------------------------------------------------------------------

def _geo_score(
    conf: float,
    drone_score: float,
    hit_streak: int,
    lost_frames: int,
    *,
    streak_cap: int = 10,
    lost_penalty: float = 0.15,
) -> float:
    """Geometry-based score independent of trust (same scale as conf)."""
    return (
        conf
        + drone_score * 0.50
        + min(streak_cap, hit_streak) * 0.08
        - lost_frames * lost_penalty
    )


def build_proposals(
    targets: dict,          # dict[int, TrackedTarget]
    scene: str,
    normalize_fn,           # normalize_source callable
) -> list[Proposal]:
    """Convert all TrackedTarget objects to Proposal list with trust scores."""
    proposals = []
    for target in targets.values():
        src = normalize_fn(target.source)
        trust = source_trust(src, scene)
        geo = _geo_score(
            float(target.conf),
            float(target.drone_score),
            int(target.hit_streak),
            int(target.lost_frames),
        )
        proposals.append(
            Proposal(
                target_id=int(target.track_id),
                bbox=tuple(target.raw_bbox),
                source=src,
                conf=float(target.conf),
                drone_score=float(target.drone_score),
                hit_streak=int(target.hit_streak),
                lost_frames=int(target.lost_frames),
                trust=trust,
                geo_score=geo,
                total_score=trust * max(0.0, geo),
            )
        )
    return sorted(proposals, key=lambda p: p.total_score, reverse=True)
