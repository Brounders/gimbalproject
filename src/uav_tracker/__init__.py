from uav_tracker.config import Config

__all__ = ['Config', 'TrackerPipeline', 'apply_runtime_preset', 'run_tracker']


def __getattr__(name: str):
    # Lazy import: pipeline pulls in cv2/ultralytics — only load when actually needed.
    if name in ('TrackerPipeline', 'apply_runtime_preset', 'run_tracker'):
        from uav_tracker.pipeline import TrackerPipeline, apply_runtime_preset, run_tracker
        globals()['TrackerPipeline'] = TrackerPipeline
        globals()['apply_runtime_preset'] = apply_runtime_preset
        globals()['run_tracker'] = run_tracker
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
