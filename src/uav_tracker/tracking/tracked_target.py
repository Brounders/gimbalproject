from collections import deque
from dataclasses import dataclass, field


@dataclass
class TrackedTarget:
    track_id: int
    bbox: tuple
    raw_bbox: tuple
    cx: float = 0.0
    cy: float = 0.0
    speed: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    conf: float = 0.0
    cls_id: int = -1
    drone_score: float = 0.5
    lost_frames: int = 0
    hit_streak: int = 0
    source: str = 'yolo'
    trail: deque = field(default_factory=lambda: deque(maxlen=30))
