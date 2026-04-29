"""Detection source identifiers.

Replaces ad-hoc string literals ('yolo', 'lock', 'roi', 'night', 'local')
with a typed enum so invalid values are caught at definition time.
"""
from __future__ import annotations

from enum import Enum


class DetectionSource(str, Enum):
    """Origin of a detection or tracking update."""

    YOLO = "yolo"          # Primary YOLO/ByteTrack global scan
    LOCAL = "local"        # Local validation crop around active target
    LOCK = "lock"          # Template lock tracker update
    ROI = "roi"            # ROI assist / motion crop proposal
    NIGHT = "night"        # Night MOG2 / small-target detector

    # Convenience sets (used for membership checks)
    @classmethod
    def primary_sources(cls) -> frozenset["DetectionSource"]:
        """Sources that carry a valid class_id and are treated as primary signal."""
        return frozenset({cls.YOLO, cls.ROI, cls.LOCAL, cls.LOCK})
