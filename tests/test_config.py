"""Unit tests for src/uav_tracker/config.py.

Covers:
  - Default construction (Config() builds without args)
  - Field types for key numeric/bool fields
  - Proportion invariants: alpha/thresh fields in (0, 1)
  - Ordering invariants: high > low, lock > reacquire, min < max
  - Override independence: overriding field X leaves field Y unchanged
  - Mutability: fields can be reassigned in-place (required by AutoSceneAdapter)
  - Section presence: one representative field per logical section (BRIEF-030 guard)
  - Production-safe defaults: AUTO_SCENE_DETECT=False, BUDGET_ENABLED=True, etc.

Runs without cv2, ultralytics, torch, or hardware.

Usage:
    PYTHONPATH=src python3 -m unittest -v tests.test_config
"""

import unittest

from uav_tracker.config import Config


def _cfg(**overrides) -> Config:
    return Config(**overrides)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConfigConstruction(unittest.TestCase):

    def test_default_construction_succeeds(self):
        cfg = Config()
        self.assertIsInstance(cfg, Config)

    def test_single_override(self):
        cfg = _cfg(CONF_THRESH=0.55)
        self.assertAlmostEqual(cfg.CONF_THRESH, 0.55)

    def test_multiple_overrides_independent(self):
        cfg = _cfg(CONF_THRESH=0.55, IMG_SIZE=1280, BUDGET_ENABLED=False)
        self.assertAlmostEqual(cfg.CONF_THRESH, 0.55)
        self.assertEqual(cfg.IMG_SIZE, 1280)
        self.assertFalse(cfg.BUDGET_ENABLED)

    def test_override_does_not_pollute_other_fields(self):
        """Changing one field must not affect unrelated field defaults."""
        default = Config()
        custom = _cfg(CONF_THRESH=0.99)
        self.assertEqual(custom.IOU_THRESH, default.IOU_THRESH)
        self.assertEqual(custom.GLOBAL_SCAN_INTERVAL, default.GLOBAL_SCAN_INTERVAL)
        self.assertEqual(custom.NIGHT_MOT_THRESH, default.NIGHT_MOT_THRESH)

    def test_classes_none_by_default(self):
        """CLASSES=None means 'all classes' — must stay None unless overridden."""
        cfg = Config()
        self.assertIsNone(cfg.CLASSES)


# ---------------------------------------------------------------------------
# Field types
# ---------------------------------------------------------------------------

class TestConfigFieldTypes(unittest.TestCase):
    """Key fields must have the expected Python types.

    Guards against accidental int/float swaps that would break downstream
    arithmetic (e.g., alpha EMA calculations depend on float division).
    """

    def setUp(self):
        self.cfg = Config()

    def test_conf_thresh_is_float(self):
        self.assertIsInstance(self.cfg.CONF_THRESH, float)

    def test_iou_thresh_is_float(self):
        self.assertIsInstance(self.cfg.IOU_THRESH, float)

    def test_img_size_is_int(self):
        self.assertIsInstance(self.cfg.IMG_SIZE, int)

    def test_global_scan_interval_is_int(self):
        self.assertIsInstance(self.cfg.GLOBAL_SCAN_INTERVAL, int)

    def test_lock_confirm_frames_is_int(self):
        self.assertIsInstance(self.cfg.LOCK_CONFIRM_FRAMES, int)

    def test_budget_target_fps_is_float(self):
        self.assertIsInstance(self.cfg.BUDGET_TARGET_FPS, float)

    def test_confidence_ema_alpha_is_float(self):
        self.assertIsInstance(self.cfg.CONFIDENCE_EMA_ALPHA, float)

    def test_smooth_bbox_alpha_is_float(self):
        self.assertIsInstance(self.cfg.SMOOTH_BBOX_ALPHA, float)

    def test_adaptive_scan_enabled_is_bool(self):
        self.assertIsInstance(self.cfg.ADAPTIVE_SCAN_ENABLED, bool)

    def test_budget_enabled_is_bool(self):
        self.assertIsInstance(self.cfg.BUDGET_ENABLED, bool)

    def test_night_enabled_is_bool(self):
        self.assertIsInstance(self.cfg.NIGHT_ENABLED, bool)

    def test_auto_scene_detect_is_bool(self):
        self.assertIsInstance(self.cfg.AUTO_SCENE_DETECT, bool)


# ---------------------------------------------------------------------------
# Proportion invariants — alpha/threshold fields must be in (0, 1)
# ---------------------------------------------------------------------------

class TestConfigProportionInvariants(unittest.TestCase):
    """All EMA alpha and normalised threshold fields must be in (0, 1)."""

    def setUp(self):
        self.cfg = Config()

    def _assert_unit(self, name: str) -> None:
        v = getattr(self.cfg, name)
        self.assertGreater(v, 0.0, msg=f'{name} must be > 0')
        self.assertLess(v, 1.0, msg=f'{name} must be < 1')

    def test_conf_thresh(self):        self._assert_unit('CONF_THRESH')
    def test_iou_thresh(self):         self._assert_unit('IOU_THRESH')
    def test_confidence_ema_alpha(self): self._assert_unit('CONFIDENCE_EMA_ALPHA')
    def test_smooth_bbox_alpha(self):  self._assert_unit('SMOOTH_BBOX_ALPHA')
    def test_smooth_bbox_size_alpha(self): self._assert_unit('SMOOTH_BBOX_SIZE_ALPHA')
    def test_reticle_center_alpha(self): self._assert_unit('RETICLE_CENTER_ALPHA')
    def test_velocity_alpha(self):     self._assert_unit('VELOCITY_ALPHA')
    def test_class_ema_alpha(self):    self._assert_unit('CLASS_EMA_ALPHA')
    def test_drone_lock_score_min(self): self._assert_unit('DRONE_LOCK_SCORE_MIN')
    def test_drone_reacquire_score_min(self): self._assert_unit('DRONE_REACQUIRE_SCORE_MIN')
    def test_lock_tracker_min_score(self): self._assert_unit('LOCK_TRACKER_MIN_SCORE')
    def test_lock_tracker_update_alpha(self): self._assert_unit('LOCK_TRACKER_UPDATE_ALPHA')
    def test_local_track_conf(self):   self._assert_unit('LOCAL_TRACK_CONF')
    def test_roi_conf_thresh(self):    self._assert_unit('ROI_CONF_THRESH')
    def test_small_target_conf(self):  self._assert_unit('SMALL_TARGET_CONF')


# ---------------------------------------------------------------------------
# Ordering invariants
# ---------------------------------------------------------------------------

class TestConfigOrderingInvariants(unittest.TestCase):
    """Relational invariants between pairs of config fields."""

    def setUp(self):
        self.cfg = Config()

    def test_budget_high_load_above_low_load(self):
        """CPU load thresholds must be ordered: scale-up trigger > scale-down trigger."""
        self.assertGreater(self.cfg.BUDGET_HIGH_LOAD, self.cfg.BUDGET_LOW_LOAD)

    def test_drone_lock_score_above_reacquire_score(self):
        """Lock confirmation score must be stricter than reacquire score."""
        self.assertGreater(self.cfg.DRONE_LOCK_SCORE_MIN, self.cfg.DRONE_REACQUIRE_SCORE_MIN)

    def test_night_min_area_below_max_area(self):
        self.assertLess(self.cfg.NIGHT_MIN_AREA, self.cfg.NIGHT_MAX_AREA)

    def test_roi_min_area_below_max_area(self):
        self.assertLess(self.cfg.ROI_MIN_AREA, self.cfg.ROI_MAX_AREA)

    def test_local_track_min_size_below_max_size(self):
        self.assertLess(self.cfg.LOCAL_TRACK_MIN_SIZE, self.cfg.LOCAL_TRACK_MAX_SIZE)

    def test_global_scan_interval_positive(self):
        self.assertGreater(self.cfg.GLOBAL_SCAN_INTERVAL, 0)

    def test_lock_confirm_frames_positive(self):
        self.assertGreater(self.cfg.LOCK_CONFIRM_FRAMES, 0)

    def test_budget_level_max_positive(self):
        self.assertGreater(self.cfg.BUDGET_LEVEL_MAX, 0)

    def test_budget_roi_min_candidates_positive(self):
        self.assertGreater(self.cfg.BUDGET_ROI_MIN_CANDIDATES, 0)

    def test_budget_roi_min_below_max_candidates(self):
        self.assertLess(self.cfg.BUDGET_ROI_MIN_CANDIDATES, self.cfg.ROI_MAX_CANDIDATES)

    def test_night_blur_kernel_is_odd(self):
        """Gaussian kernel size must be odd or cv2.GaussianBlur raises."""
        self.assertEqual(self.cfg.NIGHT_BLUR_KERNEL % 2, 1)

    def test_track_lost_frames_above_acquire_frames(self):
        """Losing a track should require more frames than acquiring one."""
        self.assertGreater(self.cfg.TRACK_STATE_LOST_FRAMES, self.cfg.TRACK_STATE_ACQUIRE_FRAMES)

    def test_track_reset_frames_above_lost_frames(self):
        """Full reset requires more patience than entering LOST."""
        self.assertGreater(self.cfg.TRACK_STATE_RESET_FRAMES, self.cfg.TRACK_STATE_LOST_FRAMES)


# ---------------------------------------------------------------------------
# Mutability (required by AutoSceneAdapter inline logic in pipeline.py)
# ---------------------------------------------------------------------------

class TestConfigMutability(unittest.TestCase):
    """Config fields must be reassignable in-place.

    AutoSceneAdapter directly writes cfg.CONF_THRESH = X etc.
    This test guards that the dataclass does not become frozen/immutable.
    """

    def test_conf_thresh_can_be_overwritten(self):
        cfg = Config()
        original = cfg.CONF_THRESH
        cfg.CONF_THRESH = 0.05
        self.assertAlmostEqual(cfg.CONF_THRESH, 0.05)
        # Restore to confirm assignment is in-place
        cfg.CONF_THRESH = original
        self.assertAlmostEqual(cfg.CONF_THRESH, original)

    def test_multiple_fields_can_be_overwritten_independently(self):
        cfg = Config()
        cfg.CONF_THRESH = 0.12
        cfg.NIGHT_MOT_THRESH = 12
        cfg.LOCK_CONFIRM_FRAMES = 8
        self.assertAlmostEqual(cfg.CONF_THRESH, 0.12)
        self.assertEqual(cfg.NIGHT_MOT_THRESH, 12)
        self.assertEqual(cfg.LOCK_CONFIRM_FRAMES, 8)


# ---------------------------------------------------------------------------
# Production-safe defaults
# ---------------------------------------------------------------------------

class TestConfigProductionDefaults(unittest.TestCase):
    """Critical default-off / default-on flags that affect production behaviour."""

    def setUp(self):
        self.cfg = Config()

    def test_auto_scene_detect_off_by_default(self):
        """AUTO_SCENE must be off in default mode — operator enables explicitly."""
        self.assertFalse(self.cfg.AUTO_SCENE_DETECT)

    def test_budget_enabled_by_default(self):
        self.assertTrue(self.cfg.BUDGET_ENABLED)

    def test_night_enabled_by_default(self):
        self.assertTrue(self.cfg.NIGHT_ENABLED)

    def test_lock_tracker_enabled_by_default(self):
        self.assertTrue(self.cfg.LOCK_TRACKER_ENABLED)

    def test_adaptive_scan_enabled_by_default(self):
        self.assertTrue(self.cfg.ADAPTIVE_SCAN_ENABLED)

    def test_roi_assist_enabled_by_default(self):
        self.assertTrue(self.cfg.ROI_ASSIST_ENABLED)

    def test_budget_target_fps_reasonable(self):
        """Default target FPS should be in a plausible video range."""
        self.assertGreaterEqual(self.cfg.BUDGET_TARGET_FPS, 10.0)
        self.assertLessEqual(self.cfg.BUDGET_TARGET_FPS, 120.0)

    def test_img_size_is_standard(self):
        """Default inference size must be a multiple of 32 (YOLO stride)."""
        self.assertEqual(self.cfg.IMG_SIZE % 32, 0)

    def test_small_target_img_size_is_standard(self):
        self.assertEqual(self.cfg.SMALL_TARGET_IMG_SIZE % 32, 0)


# ---------------------------------------------------------------------------
# Section presence — BRIEF-030 regression guard
# ---------------------------------------------------------------------------

class TestConfigSectionPresence(unittest.TestCase):
    """One representative field per logical section must be accessible.

    If BRIEF-030 (Config restructuring) renames or moves fields,
    these tests will catch the regression before callers do.
    """

    def setUp(self):
        self.cfg = Config()

    def test_section_source_runtime(self):
        _ = self.cfg.VIDEO_SOURCE
        _ = self.cfg.RUNTIME_MODE

    def test_section_model(self):
        _ = self.cfg.MODEL_PATH
        _ = self.cfg.CONF_THRESH
        _ = self.cfg.IMG_SIZE
        _ = self.cfg.DEVICE

    def test_section_adaptive_scan(self):
        _ = self.cfg.ADAPTIVE_SCAN_ENABLED
        _ = self.cfg.GLOBAL_SCAN_INTERVAL
        _ = self.cfg.LOCAL_VALIDATE_INTERVAL

    def test_section_lock_tracker(self):
        _ = self.cfg.LOCK_TRACKER_ENABLED
        _ = self.cfg.LOCK_TRACKER_MIN_SCORE
        _ = self.cfg.LOCK_TRACKER_SEARCH_SCALE

    def test_section_roi_assist(self):
        _ = self.cfg.ROI_ASSIST_ENABLED
        _ = self.cfg.ROI_MAX_CANDIDATES
        _ = self.cfg.ROI_CONF_THRESH

    def test_section_budget_controller(self):
        _ = self.cfg.BUDGET_ENABLED
        _ = self.cfg.BUDGET_TARGET_FPS
        _ = self.cfg.BUDGET_LEVEL_MAX
        _ = self.cfg.BUDGET_SCAN_INTERVAL_BOOST_PER_LEVEL

    def test_section_tracking_and_lock(self):
        _ = self.cfg.LOCK_CONFIRM_FRAMES
        _ = self.cfg.DRONE_LOCK_SCORE_MIN
        _ = self.cfg.TRACK_STATE_ACQUIRE_FRAMES
        _ = self.cfg.YOLO_LOST_MAX
        _ = self.cfg.ACTIVE_ID_SWITCH_COOLDOWN_FRAMES

    def test_section_night_detector(self):
        _ = self.cfg.NIGHT_ENABLED
        _ = self.cfg.NIGHT_MOT_THRESH
        _ = self.cfg.NIGHT_DIFF_THRESH
        _ = self.cfg.NIGHT_MOG2_HISTORY

    def test_section_display_overlay(self):
        _ = self.cfg.RETICLE_OVERLAY_ENABLED
        _ = self.cfg.CONFIDENCE_EMA_ALPHA
        _ = self.cfg.TRAIL_LEN
        _ = self.cfg.DISPLAY_MAX_LOST_FRAMES

    def test_section_auto_scene(self):
        _ = self.cfg.AUTO_SCENE_DETECT
        _ = self.cfg.AUTO_SCENE_NIGHT_BRIGHTNESS_MAX
        _ = self.cfg.AUTO_SCENE_IR_SAT_MAX
        _ = self.cfg.AUTO_SCENE_NIGHT_DRONE_LOCK_SCORE

    def test_section_bbox_smoothing(self):
        _ = self.cfg.SMOOTH_BBOX_ALPHA
        _ = self.cfg.SMOOTH_BBOX_SIZE_ALPHA
        _ = self.cfg.SMOOTH_BBOX_HOLD_FRAMES
        _ = self.cfg.DISPLAY_STATE_HOLD_FRAMES


# ---------------------------------------------------------------------------
# __post_init__ validation
# ---------------------------------------------------------------------------

class TestConfigValidation(unittest.TestCase):
    """Config.__post_init__ must raise ValueError for hard invariant violations."""

    def test_conf_thresh_zero_raises(self):
        with self.assertRaises(ValueError):
            Config(CONF_THRESH=0.0)

    def test_conf_thresh_one_raises(self):
        with self.assertRaises(ValueError):
            Config(CONF_THRESH=1.0)

    def test_iou_thresh_above_one_raises(self):
        with self.assertRaises(ValueError):
            Config(IOU_THRESH=1.5)

    def test_img_size_zero_raises(self):
        with self.assertRaises(ValueError):
            Config(IMG_SIZE=0)

    def test_budget_load_inverted_raises(self):
        """BUDGET_HIGH_LOAD <= BUDGET_LOW_LOAD must be rejected."""
        with self.assertRaises(ValueError):
            Config(BUDGET_HIGH_LOAD=0.7, BUDGET_LOW_LOAD=0.9)

    def test_track_acquire_frames_zero_raises(self):
        with self.assertRaises(ValueError):
            Config(TRACK_STATE_ACQUIRE_FRAMES=0)

    def test_img_size_non_multiple_of_32_warns(self):
        import warnings as _warnings
        with _warnings.catch_warnings(record=True) as caught:
            _warnings.simplefilter("always")
            Config(IMG_SIZE=600)
        msgs = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
        self.assertTrue(any("multiple of 32" in m for m in msgs))


if __name__ == '__main__':
    unittest.main()
