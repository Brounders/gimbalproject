"""TargetEvidence / TargetBelief — detection-first tracking primitives (ALG-001 v1).

Telemetry-only data classes used by ActionPolicy to decide tracking action.
This module is read-only relative to existing pipeline state: it does not
mutate TargetManager or LockTracker; it merely summarizes their state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# Per-source baseline reliability prior (0..1).
# Primary YOLO detections are highest; template lock is conservative;
# motion-only night detections are lowest.
SOURCE_RELIABILITY: dict[str, float] = {
    'yolo': 1.00,
    'local': 0.85,
    'roi': 0.70,
    'lock': 0.50,
    'night': 0.40,
}


def normalize_source(source: object) -> str:
    """Return stable source labels used by policy and telemetry.

    DetectionSource is a string-valued Enum, but some historical call sites
    stored `str(enum_member)` which becomes `DetectionSource.NIGHT`.  Policy
    rules should not depend on that representation.
    """
    value = getattr(source, 'value', source)
    text = str(value).strip()
    if text.startswith('DetectionSource.'):
        text = text.rsplit('.', 1)[-1].lower()
    return text


# Component weights for total_score (sum to 1.0).
_W_DETECTOR = 0.40
_W_APPEARANCE = 0.20
_W_TRAJECTORY = 0.15
_W_MOTION = 0.15
_W_SCALE = 0.10


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def compute_total_score(
    detector_score: float,
    motion_score: float,
    appearance_score: float,
    trajectory_score: float,
    scale_score: float,
    source_reliability: float,
) -> float:
    """Weighted, reliability-scaled, clamped total score in [0, 1]."""
    raw = (
        _W_DETECTOR * _clamp01(detector_score)
        + _W_MOTION * _clamp01(motion_score)
        + _W_APPEARANCE * _clamp01(appearance_score)
        + _W_TRAJECTORY * _clamp01(trajectory_score)
        + _W_SCALE * _clamp01(scale_score)
    )
    return _clamp01(raw * _clamp01(source_reliability))


@dataclass
class TargetEvidence:
    """A single proposal/observation for a candidate target.

    Score components are in [0, 1]; total_score is computed from them
    weighted by source_reliability and clamped to [0, 1].
    """
    source: str
    bbox: Optional[tuple[int, int, int, int]]
    track_id: Optional[int]
    cls_id: int
    conf: float
    detector_score: float = 0.0
    motion_score: float = 0.0
    appearance_score: float = 0.0
    trajectory_score: float = 0.0
    scale_score: float = 0.0
    source_reliability: float = 0.0
    total_score: float = field(init=False)

    def __post_init__(self) -> None:
        self.total_score = compute_total_score(
            detector_score=self.detector_score,
            motion_score=self.motion_score,
            appearance_score=self.appearance_score,
            trajectory_score=self.trajectory_score,
            scale_score=self.scale_score,
            source_reliability=self.source_reliability,
        )


@dataclass
class TargetBelief:
    """Aggregate belief about the active target across frames.

    Pure summary — does not modify pipeline state.

    `modality` is a sensor/scene tag in {'rgb', 'ir', 'night', 'unknown'}
    used by downstream consumers (e.g. ActionPolicy) to apply IR-first
    night gate semantics: RGB is primary in daylight, IR/thermal is the
    primary night evidence, RGB-night observations are diagnostic.

    The default 'rgb' keeps existing call sites backward compatible; the
    pipeline overrides it from the auto-scene state.
    """
    active_id: Optional[int]
    bbox: Optional[tuple[int, int, int, int]]
    last_good_bbox: Optional[tuple[int, int, int, int]]
    velocity: tuple[float, float]
    scale: float
    p_present: float
    p_same_target: float
    reliability: float
    lost_age: int
    source: str
    modality: str = 'rgb'

    def __post_init__(self) -> None:
        self.source = normalize_source(self.source)

    @classmethod
    def empty(cls) -> 'TargetBelief':
        return cls(
            active_id=None,
            bbox=None,
            last_good_bbox=None,
            velocity=(0.0, 0.0),
            scale=1.0,
            p_present=0.0,
            p_same_target=0.0,
            reliability=0.0,
            lost_age=0,
            source='-',
            modality='rgb',
        )
