"""uav_tracker.exceptions — Typed pipeline exceptions (BUG-008).

Raised by pipeline, session, and backend code so TrackerWorker can emit
specific error messages instead of a generic str(exc).
"""
from __future__ import annotations


class TrackerError(RuntimeError):
    """Base class for all UAV tracker errors."""


class ModelNotFoundError(TrackerError):
    """Model file missing or unreadable at startup."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Модель не найдена: '{path}'. "
            "Проверьте путь в настройках или переустановите baseline."
        )
        self.path = path


class SourceOpenError(TrackerError):
    """Video source (file or device) could not be opened."""

    def __init__(self, source: str | int) -> None:
        super().__init__(
            f"Не удалось открыть источник видео: '{source}'. "
            "Проверьте путь к файлу или индекс камеры."
        )
        self.source = source


class InferenceDeviceError(TrackerError):
    """GPU / MPS / CUDA device error during inference."""

    def __init__(self, device: str, cause: Exception) -> None:
        super().__init__(
            f"Ошибка устройства вывода '{device}': {cause}. "
            "Попробуйте сменить DEVICE на 'cpu' в настройках."
        )
        self.device = device
        self.cause = cause
