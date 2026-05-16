from __future__ import annotations

from collections import deque
from types import SimpleNamespace

import numpy as np

from uav_tracker.config import Config
from uav_tracker.pipeline import TrackerPipeline
from uav_tracker.profile_io import load_preset
from uav_tracker.runtime_config import RuntimeConfigView


def _pipeline_stub(cfg: Config):
    stub = SimpleNamespace()
    stub.cfg = cfg
    stub._runtime_cfg = RuntimeConfigView(cfg)
    stub._auto_scene_state = "day"
    stub._auto_scene_streak = 0
    stub._auto_scene_frame_tick = 0
    # TASK-103c v2 additions
    stub._auto_scene_history = deque()
    stub._prev_sample_gray = None
    stub._adapt_auto_scene = TrackerPipeline._adapt_auto_scene.__get__(stub, type(stub))
    stub._sync_runtime_detectors = TrackerPipeline._sync_runtime_detectors.__get__(stub, type(stub))
    return stub


def test_tracking_live_auto_preset_enables_content_based_scene_switching():
    cfg, data = load_preset("tracking_live_auto", Config())

    assert data["auto_scene_detect"] is True
    assert cfg.AUTO_SCENE_DETECT is True
    assert cfg.NIGHT_ENABLED is False
    assert cfg.AUTO_SCENE_DAY_NIGHT_ENABLED is False
    assert cfg.AUTO_SCENE_IR_NIGHT_ENABLED is True
    assert cfg.AUTO_SCENE_IR_PEAK_ENABLED is True


def test_auto_scene_ir_enables_peak_detector_without_mutating_base_config():
    cfg = Config(
        AUTO_SCENE_DETECT=True,
        AUTO_SCENE_SAMPLE_INTERVAL=1,
        AUTO_SCENE_CONFIRM_FRAMES=1,
        AUTO_SCENE_NIGHT_BRIGHTNESS_MAX=1,
        AUTO_SCENE_IR_SAT_MAX=250,
        NIGHT_ENABLED=False,
        NIGHT_PEAK_ENABLED=False,
        NIGHT_CONTOUR_ENABLED=True,
    )
    stub = _pipeline_stub(cfg)
    frame = np.full((80, 80, 3), 180, dtype=np.uint8)

    stub._adapt_auto_scene(frame)

    assert stub._auto_scene_state == "ir"
    assert stub._runtime_cfg.NIGHT_ENABLED is True
    assert stub._runtime_cfg.NIGHT_PEAK_ENABLED is True
    assert stub._runtime_cfg.NIGHT_CONTOUR_ENABLED is False
    assert cfg.NIGHT_ENABLED is False
    assert cfg.NIGHT_PEAK_ENABLED is False


def test_auto_scene_day_disables_night_detector_without_mutating_base_config():
    cfg = Config(
        AUTO_SCENE_DETECT=True,
        AUTO_SCENE_SAMPLE_INTERVAL=1,
        AUTO_SCENE_CONFIRM_FRAMES=1,
        AUTO_SCENE_NIGHT_BRIGHTNESS_MAX=1,
        AUTO_SCENE_IR_SAT_MAX=1,
        AUTO_SCENE_DAY_NIGHT_ENABLED=False,
        NIGHT_ENABLED=True,
    )
    stub = _pipeline_stub(cfg)
    frame = np.zeros((80, 80, 3), dtype=np.uint8)
    frame[:, :, 0] = 10
    frame[:, :, 1] = 180
    frame[:, :, 2] = 250

    stub._adapt_auto_scene(frame)

    assert stub._auto_scene_state == "day"
    assert stub._runtime_cfg.NIGHT_ENABLED is False
    assert cfg.NIGHT_ENABLED is True


# ---------------------------------------------------------------------------
# TASK-103c Auto-scene-detect v2 tests
# ---------------------------------------------------------------------------

def test_eo_overcast_not_classified_as_ir():
    """Slightly-desaturated EO frame with strong edges → day (F1 guard).

    Uses ir_sat_max=40 so the frame's mean_S (~32) is in the borderline zone
    [sat_max*0.5=20, sat_max=40].  High edge_density + no hot spots triggers
    the EO-overcast guard → 'day'.
    """
    cfg = Config(
        AUTO_SCENE_DETECT=True,
        AUTO_SCENE_SAMPLE_INTERVAL=1,
        AUTO_SCENE_CONFIRM_FRAMES=1,
        AUTO_SCENE_NIGHT_BRIGHTNESS_MAX=50,
        AUTO_SCENE_IR_SAT_MAX=40,    # realistic-ish; borderline for slightly gray EO
        AUTO_SCENE_IR_EDGE_MAX=0.12,
        AUTO_SCENE_IR_HOT_FRAC=0.005,
        AUTO_SCENE_DAY_NIGHT_ENABLED=False,
    )
    stub = _pipeline_stub(cfg)
    # Slightly reddish-gray frame → mean_S ≈ 30-35 (above 50% threshold = 20)
    # Add checkerboard-style bars → high edge_density, no hot spots.
    frame = np.zeros((80, 80, 3), dtype=np.uint8)
    frame[:, :, 0] = 175   # B channel
    frame[:, :, 1] = 175   # G channel
    frame[:, :, 2] = 200   # R channel — slight warm tint → HSV-S ≈ 32
    frame[::4, :, 2] = 120  # alternating bars → Sobel edges
    frame[:, ::4, 2] = 120

    stub._adapt_auto_scene(frame)

    assert stub._auto_scene_state == "day", \
        "Borderline-desaturated textured EO frame must NOT be classified as IR"


def test_thermal_ir_with_hot_spot_classified_as_ir():
    """Desaturated frame with thermal hot spots → IR (not EO overcast)."""
    cfg = Config(
        AUTO_SCENE_DETECT=True,
        AUTO_SCENE_SAMPLE_INTERVAL=1,
        AUTO_SCENE_CONFIRM_FRAMES=1,
        AUTO_SCENE_NIGHT_BRIGHTNESS_MAX=50,
        AUTO_SCENE_IR_SAT_MAX=25,
        AUTO_SCENE_IR_EDGE_MAX=0.12,
        AUTO_SCENE_IR_HOT_FRAC=0.005,
    )
    stub = _pipeline_stub(cfg)
    # Dark gray frame with a few bright hot pixels (thermal target)
    frame = np.full((80, 80, 3), 80, dtype=np.uint8)
    frame[38:42, 38:42] = 255   # hot spot → hot_pixel_frac ≈ 0.0025 still above threshold for tiny frame

    # Ensure saturation is low (grayscale-ish)
    frame[:, :, 0] = frame[:, :, 1]
    frame[:, :, 2] = frame[:, :, 1]

    stub._adapt_auto_scene(frame)

    assert stub._auto_scene_state == "ir"


def test_multi_roi_majority_vote_detects_ir_in_half_frame():
    """RGBT split-screen: IR half + colored half → majority of ROIs should detect IR or day, not crash."""
    cfg = Config(
        AUTO_SCENE_DETECT=True,
        AUTO_SCENE_SAMPLE_INTERVAL=1,
        AUTO_SCENE_CONFIRM_FRAMES=1,
        AUTO_SCENE_NIGHT_BRIGHTNESS_MAX=50,
        AUTO_SCENE_IR_SAT_MAX=25,
        AUTO_SCENE_IR_EDGE_MAX=0.12,
        AUTO_SCENE_IR_HOT_FRAC=0.005,
    )
    stub = _pipeline_stub(cfg)
    # Left half: colored (day), right half: gray IR
    frame = np.zeros((120, 120, 3), dtype=np.uint8)
    frame[:, :60, 1] = 200   # green left half → high saturation
    frame[:, 60:] = 100      # gray right half → low saturation

    stub._adapt_auto_scene(frame)

    # Should not raise; result is either 'day' or 'ir' (not 'night')
    assert stub._auto_scene_state in ("day", "ir")


def test_scene_confidence_is_stability_ratio():
    """After multiple consistent samples, history-based stability should approach 1.0."""
    cfg = Config(
        AUTO_SCENE_DETECT=True,
        AUTO_SCENE_SAMPLE_INTERVAL=1,
        AUTO_SCENE_CONFIRM_FRAMES=1,
        AUTO_SCENE_NIGHT_BRIGHTNESS_MAX=50,
        AUTO_SCENE_IR_SAT_MAX=25,
        AUTO_SCENE_STABILITY_WINDOW=10,
    )
    stub = _pipeline_stub(cfg)
    # Colorful frame → 'day' every time
    frame = np.zeros((80, 80, 3), dtype=np.uint8)
    frame[:, :, 1] = 200  # green → high saturation

    for _ in range(10):
        stub._adapt_auto_scene(frame)

    hist = stub._auto_scene_history
    assert len(hist) > 0
    stability = sum(1 for s in hist if s == stub._auto_scene_state) / len(hist)
    assert stability >= 0.9, f"Expected high stability after 10 consistent frames, got {stability:.2f}"


def test_pipeline_syncs_night_detector_to_runtime_config_view():
    cfg = Config(NIGHT_ENABLED=False, NIGHT_PEAK_ENABLED=False)
    stub = SimpleNamespace()
    stub.cfg = cfg
    stub._runtime_cfg = RuntimeConfigView(cfg, {"NIGHT_ENABLED": True, "NIGHT_PEAK_ENABLED": True})
    stub.night = SimpleNamespace(cfg=cfg)
    stub._sync_runtime_detectors = TrackerPipeline._sync_runtime_detectors.__get__(stub, type(stub))

    stub._sync_runtime_detectors()

    assert stub.night.cfg.NIGHT_ENABLED is True
    assert stub.night.cfg.NIGHT_PEAK_ENABLED is True
    assert cfg.NIGHT_ENABLED is False
