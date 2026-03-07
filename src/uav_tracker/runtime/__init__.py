from uav_tracker.runtime.base import Detection, DetectorBackend
from uav_tracker.runtime.hailo_backend import HailoBackend
from uav_tracker.runtime.ultralytics_backend import UltralyticsBackend


def create_detector_backend(model_path: str, device: str):
    if str(device).lower() == 'hailo' or model_path.lower().endswith('.hef'):
        return HailoBackend(model_path)
    return UltralyticsBackend(model_path)
