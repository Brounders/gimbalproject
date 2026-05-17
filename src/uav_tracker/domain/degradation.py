from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureCase(str, Enum):
    CAMERA_LOST = "camera_lost"
    MODEL_LOAD_FAIL = "model_load_fail"
    DTS_DISK_FULL = "dts_disk_full"
    TRAINING_CRASHED = "training_crashed"
    COMPARE_CRASHED = "compare_crashed"


class Severity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class FallbackState(str, Enum):
    SEARCH = "SEARCH"
    DEGRADED = "DEGRADED"
    DTS_PAUSED = "DTS_PAUSED"
    TRAINING_FAILED = "TRAINING_FAILED"
    COMPARE_FAILED = "COMPARE_FAILED"


@dataclass(frozen=True)
class DegradationStatus:
    case: FailureCase
    severity: Severity
    user_message: str
    fallback_state: FallbackState
    auto_recovery_allowed: bool
    operator_action: str
    telemetry_event: str


_CONTRACT: dict[FailureCase, DegradationStatus] = {
    FailureCase.CAMERA_LOST: DegradationStatus(
        case=FailureCase.CAMERA_LOST,
        severity=Severity.ERROR,
        user_message="Источник видео потерян",
        fallback_state=FallbackState.SEARCH,
        auto_recovery_allowed=True,
        operator_action="Проверьте камеру или выберите другой источник",
        telemetry_event="camera_lost",
    ),
    FailureCase.MODEL_LOAD_FAIL: DegradationStatus(
        case=FailureCase.MODEL_LOAD_FAIL,
        severity=Severity.CRITICAL,
        user_message="Модель не загрузилась",
        fallback_state=FallbackState.DEGRADED,
        auto_recovery_allowed=False,
        operator_action="Проверьте путь к модели и перезапустите детектор",
        telemetry_event="model_load_fail",
    ),
    FailureCase.DTS_DISK_FULL: DegradationStatus(
        case=FailureCase.DTS_DISK_FULL,
        severity=Severity.ERROR,
        user_message="DTS не может записать данные: нет места",
        fallback_state=FallbackState.DTS_PAUSED,
        auto_recovery_allowed=False,
        operator_action="Освободите место или смените папку записи",
        telemetry_event="dts_disk_full",
    ),
    FailureCase.TRAINING_CRASHED: DegradationStatus(
        case=FailureCase.TRAINING_CRASHED,
        severity=Severity.ERROR,
        user_message="Обучение candidate завершилось ошибкой",
        fallback_state=FallbackState.TRAINING_FAILED,
        auto_recovery_allowed=False,
        operator_action="Проверьте лог обучения и повторите запуск",
        telemetry_event="training_crashed",
    ),
    FailureCase.COMPARE_CRASHED: DegradationStatus(
        case=FailureCase.COMPARE_CRASHED,
        severity=Severity.ERROR,
        user_message="Сравнение candidate завершилось ошибкой",
        fallback_state=FallbackState.COMPARE_FAILED,
        auto_recovery_allowed=False,
        operator_action="Проверьте результат сравнения и повторите запуск",
        telemetry_event="compare_crashed",
    ),
}


def degradation_status(case: FailureCase | str) -> DegradationStatus:
    try:
        key = FailureCase(case)
    except ValueError:
        raise ValueError(f"Unknown failure case: {case!r}")
    return _CONTRACT[key]
