from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

BBox = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class Detection:
    bbox: BBox
    confidence: float
    class_id: int
    source: str
    track_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["bbox"] = list(self.bbox)
        return data


@dataclass(frozen=True, slots=True)
class Candidate:
    candidate_id: int
    bbox: BBox
    score: float
    confidence: float
    source: str
    active: bool = False
    lost_frames: int = 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["bbox"] = list(self.bbox)
        return data


@dataclass(frozen=True, slots=True)
class OperatorHint:
    kind: str
    point: tuple[int, int] | None = None
    bbox: BBox | None = None
    frame_index: int | None = None
    reason: str = "operator_click"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.point is not None:
            data["point"] = list(self.point)
        if self.bbox is not None:
            data["bbox"] = list(self.bbox)
        return data


@dataclass(frozen=True, slots=True)
class Track:
    track_id: int | None
    bbox: BBox | None
    source: str
    confidence: float
    lock_score: float
    reliability: float
    present_probability: float
    lost_frames: int | None = None
    operator_verified: bool = False
    lock_age: int = 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.bbox is not None:
            data["bbox"] = list(self.bbox)
        return data


@dataclass(frozen=True, slots=True)
class TransitionEvent:
    event: str
    frame_index: int
    state_before: str
    state_after: str
    reason: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class HealthStatus:
    ok: bool = True
    source_ok: bool = True
    detector_ok: bool = True
    tracker_ok: bool = True
    fps_ok: bool = True
    latency_ok: bool = True
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FrameResult:
    schema_version: int
    frame_id: int
    timestamp_monotonic: float
    source: str
    source_mode: str
    frame_width: int
    frame_height: int
    state_before: str
    state_after: str
    detections: tuple[Detection, ...] = ()
    candidates: tuple[Candidate, ...] = ()
    primary_track: Track | None = None
    operator_hint: OperatorHint | None = None
    transition_events: tuple[TransitionEvent, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)
    health: HealthStatus = field(default_factory=HealthStatus)
    dts_events: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "frame_id": self.frame_id,
            "timestamp_monotonic": self.timestamp_monotonic,
            "source": self.source,
            "source_mode": self.source_mode,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "detections": [item.to_dict() for item in self.detections],
            "candidates": [item.to_dict() for item in self.candidates],
            "primary_track": self.primary_track.to_dict() if self.primary_track else None,
            "operator_hint": self.operator_hint.to_dict() if self.operator_hint else None,
            "transition_events": [item.to_dict() for item in self.transition_events],
            "metrics": dict(self.metrics),
            "health": self.health.to_dict(),
            "dts_events": [dict(item) for item in self.dts_events],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrameResult":
        def _bbox(v: Any) -> BBox:
            if v is None:
                return (0, 0, 0, 0)
            return (int(v[0]), int(v[1]), int(v[2]), int(v[3]))

        def _point(v: Any) -> "tuple[int, int] | None":
            if v is None:
                return None
            return (int(v[0]), int(v[1]))

        detections = tuple(
            Detection(
                bbox=_bbox(d.get("bbox")),
                confidence=float(d.get("confidence", 0.0)),
                class_id=int(d.get("class_id", 0)),
                source=str(d.get("source", "")),
                track_id=d.get("track_id"),
            )
            for d in (data.get("detections") or [])
        )
        candidates = tuple(
            Candidate(
                candidate_id=int(c.get("candidate_id", 0)),
                bbox=_bbox(c.get("bbox")),
                score=float(c.get("score", 0.0)),
                confidence=float(c.get("confidence", 0.0)),
                source=str(c.get("source", "")),
                active=bool(c.get("active", False)),
                lost_frames=int(c.get("lost_frames", 0)),
            )
            for c in (data.get("candidates") or [])
        )
        pt_raw = data.get("primary_track")
        primary_track: Track | None = None
        if pt_raw is not None:
            primary_track = Track(
                track_id=pt_raw.get("track_id"),
                bbox=_bbox(pt_raw["bbox"]) if pt_raw.get("bbox") is not None else None,
                source=str(pt_raw.get("source", "")),
                confidence=float(pt_raw.get("confidence", 0.0)),
                lock_score=float(pt_raw.get("lock_score", 0.0)),
                reliability=float(pt_raw.get("reliability", 0.0)),
                present_probability=float(pt_raw.get("present_probability", 0.0)),
                lost_frames=pt_raw.get("lost_frames"),
                operator_verified=bool(pt_raw.get("operator_verified", False)),
                lock_age=int(pt_raw.get("lock_age", 0)),
            )
        oh_raw = data.get("operator_hint")
        operator_hint: OperatorHint | None = None
        if oh_raw is not None:
            operator_hint = OperatorHint(
                kind=str(oh_raw.get("kind", "")),
                point=_point(oh_raw.get("point")),
                bbox=_bbox(oh_raw["bbox"]) if oh_raw.get("bbox") is not None else None,
                frame_index=oh_raw.get("frame_index"),
                reason=str(oh_raw.get("reason", "operator_click")),
            )
        transition_events = tuple(
            TransitionEvent(
                event=str(te.get("event", "")),
                frame_index=int(te.get("frame_index", 0)),
                state_before=str(te.get("state_before", "")),
                state_after=str(te.get("state_after", "")),
                reason=str(te.get("reason", "")),
                payload=dict(te.get("payload") or {}),
            )
            for te in (data.get("transition_events") or [])
        )
        h_raw = data.get("health") or {}
        health = HealthStatus(
            ok=bool(h_raw.get("ok", True)),
            source_ok=bool(h_raw.get("source_ok", True)),
            detector_ok=bool(h_raw.get("detector_ok", True)),
            tracker_ok=bool(h_raw.get("tracker_ok", True)),
            fps_ok=bool(h_raw.get("fps_ok", True)),
            latency_ok=bool(h_raw.get("latency_ok", True)),
            message=str(h_raw.get("message", "")),
        )
        dts_events = tuple(dict(e) for e in (data.get("dts_events") or []))
        return cls(
            schema_version=int(data.get("schema_version", 1)),
            frame_id=int(data.get("frame_id", 0)),
            timestamp_monotonic=float(data.get("timestamp_monotonic", 0.0)),
            source=str(data.get("source", "")),
            source_mode=str(data.get("source_mode", "")),
            frame_width=int(data.get("frame_width", 0)),
            frame_height=int(data.get("frame_height", 0)),
            state_before=str(data.get("state_before", "")),
            state_after=str(data.get("state_after", "")),
            detections=detections,
            candidates=candidates,
            primary_track=primary_track,
            operator_hint=operator_hint,
            transition_events=transition_events,
            metrics=dict(data.get("metrics") or {}),
            health=health,
            dts_events=dts_events,
        )
