"""Domain contracts for frame-level tracking facts.

These dataclasses are intentionally independent from UI/QML and detector
backend classes.  They are the stable language shared by pipeline telemetry,
DTS, replay/evaluation, and future state-machine work.
"""
from __future__ import annotations

from .adapters import frame_result_from_output, operator_hint_from_override
from .degradation import (
    DegradationStatus,
    FailureCase,
    FallbackState,
    Severity,
    degradation_status,
)
from .telemetry import JsonlTelemetryReader, JsonlTelemetryWriter
from .types import (
    Candidate,
    Detection,
    FrameResult,
    HealthStatus,
    OperatorHint,
    Track,
    TransitionEvent,
)
from .workflow import derive_operator_workflow_state

__all__ = [
    "Candidate",
    "Detection",
    "FrameResult",
    "HealthStatus",
    "DegradationStatus",
    "FailureCase",
    "FallbackState",
    "JsonlTelemetryReader",
    "JsonlTelemetryWriter",
    "OperatorHint",
    "Track",
    "TransitionEvent",
    "frame_result_from_output",
    "operator_hint_from_override",
    "Severity",
    "degradation_status",
    "derive_operator_workflow_state",
]
