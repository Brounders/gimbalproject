"""Tests for the degradation contract domain types."""
from __future__ import annotations

import pytest

from uav_tracker.domain.degradation import (
    DegradationStatus,
    FailureCase,
    FallbackState,
    Severity,
    degradation_status,
)


def test_all_known_cases_return_degradation_status():
    for case in FailureCase:
        status = degradation_status(case)
        assert isinstance(status, DegradationStatus)


def test_string_input_works():
    status = degradation_status("camera_lost")
    assert status.case == FailureCase.CAMERA_LOST


def test_enum_input_works():
    status = degradation_status(FailureCase.MODEL_LOAD_FAIL)
    assert status.case == FailureCase.MODEL_LOAD_FAIL


def test_unknown_string_raises_value_error():
    with pytest.raises(ValueError, match="Unknown failure case"):
        degradation_status("totally_unknown_case")


def test_camera_lost_auto_recovery_allowed():
    status = degradation_status(FailureCase.CAMERA_LOST)
    assert status.auto_recovery_allowed is True


def test_model_load_fail_severity_critical():
    status = degradation_status(FailureCase.MODEL_LOAD_FAIL)
    assert status.severity == Severity.CRITICAL


def test_dts_disk_full_fallback_dts_paused():
    status = degradation_status(FailureCase.DTS_DISK_FULL)
    assert status.fallback_state == FallbackState.DTS_PAUSED


def test_training_crashed_fallback_training_failed():
    status = degradation_status(FailureCase.TRAINING_CRASHED)
    assert status.fallback_state == FallbackState.TRAINING_FAILED


def test_compare_crashed_fallback_compare_failed():
    status = degradation_status(FailureCase.COMPARE_CRASHED)
    assert status.fallback_state == FallbackState.COMPARE_FAILED


def test_dataclass_is_frozen():
    status = degradation_status(FailureCase.CAMERA_LOST)
    with pytest.raises((AttributeError, TypeError)):
        status.severity = Severity.INFO  # type: ignore[misc]


def test_all_cases_have_non_empty_user_message():
    for case in FailureCase:
        status = degradation_status(case)
        assert status.user_message, f"user_message empty for {case}"


def test_all_cases_have_non_empty_operator_action():
    for case in FailureCase:
        status = degradation_status(case)
        assert status.operator_action, f"operator_action empty for {case}"


def test_all_cases_have_telemetry_event_matching_case_value():
    for case in FailureCase:
        status = degradation_status(case)
        assert status.telemetry_event == case.value
