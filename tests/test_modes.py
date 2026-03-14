import unittest

from uav_tracker.config import Config
from uav_tracker.modes import RUNTIME_MODES, apply_runtime_mode


def _cfg(**overrides) -> Config:
    return Config(**overrides)


# ---------------------------------------------------------------------------
# RUNTIME_MODES constant
# ---------------------------------------------------------------------------

class TestRuntimeModesConstant(unittest.TestCase):

    def test_is_tuple(self):
        self.assertIsInstance(RUNTIME_MODES, tuple)

    def test_contains_three_modes(self):
        self.assertEqual(len(RUNTIME_MODES), 3)

    def test_contains_research(self):
        self.assertIn('research', RUNTIME_MODES)

    def test_contains_operator(self):
        self.assertIn('operator', RUNTIME_MODES)

    def test_contains_embedded(self):
        self.assertIn('embedded', RUNTIME_MODES)


# ---------------------------------------------------------------------------
# apply_runtime_mode — return value
# ---------------------------------------------------------------------------

class TestApplyRuntimeModeReturnValue(unittest.TestCase):

    def test_returns_same_object(self):
        cfg = _cfg()
        result = apply_runtime_mode(cfg, 'research')
        self.assertIs(result, cfg)

    def test_operator_returns_same_object(self):
        cfg = _cfg()
        result = apply_runtime_mode(cfg, 'operator')
        self.assertIs(result, cfg)

    def test_embedded_returns_same_object(self):
        cfg = _cfg()
        result = apply_runtime_mode(cfg, 'embedded')
        self.assertIs(result, cfg)


# ---------------------------------------------------------------------------
# apply_runtime_mode — research
# ---------------------------------------------------------------------------

class TestResearchMode(unittest.TestCase):

    def setUp(self):
        self.cfg = apply_runtime_mode(_cfg(), 'research')

    def test_runtime_mode_set(self):
        self.assertEqual(self.cfg.RUNTIME_MODE, 'research')

    def test_show_gt_overlay_enabled(self):
        self.assertTrue(self.cfg.SHOW_GT_OVERLAY)

    def test_show_debug_timings_enabled(self):
        self.assertTrue(self.cfg.SHOW_DEBUG_TIMINGS)

    def test_show_trails_enabled(self):
        self.assertTrue(self.cfg.SHOW_TRAILS)

    def test_operator_minimal_overlay_disabled(self):
        self.assertFalse(self.cfg.OPERATOR_MINIMAL_OVERLAY)

    def test_reticle_overlay_enabled(self):
        self.assertTrue(self.cfg.RETICLE_OVERLAY_ENABLED)

    def test_night_enabled(self):
        self.assertTrue(self.cfg.NIGHT_ENABLED)

    def test_lock_tracker_enabled(self):
        self.assertTrue(self.cfg.LOCK_TRACKER_ENABLED)

    def test_show_focus_window_enabled(self):
        self.assertTrue(self.cfg.SHOW_FOCUS_WINDOW)

    def test_adaptive_scan_enabled(self):
        self.assertTrue(self.cfg.ADAPTIVE_SCAN_ENABLED)

    def test_roi_assist_enabled(self):
        self.assertTrue(self.cfg.ROI_ASSIST_ENABLED)

    def test_show_only_active_on_lock(self):
        self.assertTrue(self.cfg.SHOW_ONLY_ACTIVE_ON_LOCK)


# ---------------------------------------------------------------------------
# apply_runtime_mode — operator
# ---------------------------------------------------------------------------

class TestOperatorMode(unittest.TestCase):

    def setUp(self):
        self.cfg = apply_runtime_mode(_cfg(), 'operator')

    def test_runtime_mode_set(self):
        self.assertEqual(self.cfg.RUNTIME_MODE, 'operator')

    def test_show_gt_overlay_disabled(self):
        self.assertFalse(self.cfg.SHOW_GT_OVERLAY)

    def test_show_debug_timings_disabled(self):
        self.assertFalse(self.cfg.SHOW_DEBUG_TIMINGS)

    def test_show_trails_disabled(self):
        self.assertFalse(self.cfg.SHOW_TRAILS)

    def test_operator_minimal_overlay_enabled(self):
        self.assertTrue(self.cfg.OPERATOR_MINIMAL_OVERLAY)

    def test_reticle_overlay_disabled(self):
        self.assertFalse(self.cfg.RETICLE_OVERLAY_ENABLED)

    def test_night_enabled(self):
        self.assertTrue(self.cfg.NIGHT_ENABLED)

    def test_lock_tracker_enabled(self):
        self.assertTrue(self.cfg.LOCK_TRACKER_ENABLED)

    def test_adaptive_scan_enabled(self):
        self.assertTrue(self.cfg.ADAPTIVE_SCAN_ENABLED)

    def test_roi_assist_enabled(self):
        self.assertTrue(self.cfg.ROI_ASSIST_ENABLED)

    def test_show_focus_window_disabled(self):
        self.assertFalse(self.cfg.SHOW_FOCUS_WINDOW)


# ---------------------------------------------------------------------------
# apply_runtime_mode — embedded
# ---------------------------------------------------------------------------

class TestEmbeddedMode(unittest.TestCase):

    def setUp(self):
        self.cfg = apply_runtime_mode(_cfg(), 'embedded')

    def test_runtime_mode_set(self):
        self.assertEqual(self.cfg.RUNTIME_MODE, 'embedded')

    def test_show_gt_overlay_disabled(self):
        self.assertFalse(self.cfg.SHOW_GT_OVERLAY)

    def test_show_trails_disabled(self):
        self.assertFalse(self.cfg.SHOW_TRAILS)

    def test_operator_minimal_overlay_enabled(self):
        self.assertTrue(self.cfg.OPERATOR_MINIMAL_OVERLAY)

    def test_reticle_overlay_disabled(self):
        self.assertFalse(self.cfg.RETICLE_OVERLAY_ENABLED)

    def test_roi_assist_disabled(self):
        self.assertFalse(self.cfg.ROI_ASSIST_ENABLED)

    def test_night_disabled(self):
        self.assertFalse(self.cfg.NIGHT_ENABLED)

    def test_lock_tracker_enabled(self):
        self.assertTrue(self.cfg.LOCK_TRACKER_ENABLED)

    def test_global_scan_interval_at_least_8(self):
        self.assertGreaterEqual(self.cfg.GLOBAL_SCAN_INTERVAL, 8)

    def test_local_validate_interval_at_least_4(self):
        self.assertGreaterEqual(self.cfg.LOCAL_VALIDATE_INTERVAL, 4)

    def test_global_scan_interval_raised_from_default(self):
        default_interval = _cfg().GLOBAL_SCAN_INTERVAL
        # Default is 6, embedded clamps to max(6, 8) = 8
        self.assertGreater(self.cfg.GLOBAL_SCAN_INTERVAL, default_interval)

    def test_local_validate_interval_raised_from_default(self):
        default_interval = _cfg().LOCAL_VALIDATE_INTERVAL
        # Default is 3, embedded clamps to max(3, 4) = 4
        self.assertGreater(self.cfg.LOCAL_VALIDATE_INTERVAL, default_interval)


# ---------------------------------------------------------------------------
# apply_runtime_mode — embedded with already-large intervals
# ---------------------------------------------------------------------------

class TestEmbeddedModeIntervalClamping(unittest.TestCase):

    def test_large_global_scan_interval_preserved(self):
        cfg = apply_runtime_mode(_cfg(GLOBAL_SCAN_INTERVAL=15), 'embedded')
        self.assertEqual(cfg.GLOBAL_SCAN_INTERVAL, 15)

    def test_large_local_validate_interval_preserved(self):
        cfg = apply_runtime_mode(_cfg(LOCAL_VALIDATE_INTERVAL=10), 'embedded')
        self.assertEqual(cfg.LOCAL_VALIDATE_INTERVAL, 10)

    def test_small_global_scan_interval_clamped_to_8(self):
        cfg = apply_runtime_mode(_cfg(GLOBAL_SCAN_INTERVAL=2), 'embedded')
        self.assertEqual(cfg.GLOBAL_SCAN_INTERVAL, 8)

    def test_small_local_validate_interval_clamped_to_4(self):
        cfg = apply_runtime_mode(_cfg(LOCAL_VALIDATE_INTERVAL=1), 'embedded')
        self.assertEqual(cfg.LOCAL_VALIDATE_INTERVAL, 4)


# ---------------------------------------------------------------------------
# apply_runtime_mode — input normalisation
# ---------------------------------------------------------------------------

class TestApplyRuntimeModeNormalisation(unittest.TestCase):

    def test_mode_stripped_of_whitespace(self):
        cfg = apply_runtime_mode(_cfg(), '  research  ')
        self.assertEqual(cfg.RUNTIME_MODE, 'research')

    def test_mode_lowercased(self):
        cfg = apply_runtime_mode(_cfg(), 'OPERATOR')
        self.assertEqual(cfg.RUNTIME_MODE, 'operator')

    def test_none_defaults_to_research(self):
        cfg = apply_runtime_mode(_cfg(), None)
        self.assertEqual(cfg.RUNTIME_MODE, 'research')

    def test_empty_string_defaults_to_research(self):
        cfg = apply_runtime_mode(_cfg(), '')
        self.assertEqual(cfg.RUNTIME_MODE, 'research')


# ---------------------------------------------------------------------------
# apply_runtime_mode — ValueError for unknown mode
# ---------------------------------------------------------------------------

class TestApplyRuntimeModeValueError(unittest.TestCase):

    def test_unknown_mode_raises_value_error(self):
        with self.assertRaises(ValueError):
            apply_runtime_mode(_cfg(), 'unknown')

    def test_error_message_contains_mode_name(self):
        try:
            apply_runtime_mode(_cfg(), 'invalid_mode')
        except ValueError as exc:
            self.assertIn('invalid_mode', str(exc))
        else:
            self.fail('ValueError not raised')

    def test_partial_mode_name_raises(self):
        with self.assertRaises(ValueError):
            apply_runtime_mode(_cfg(), 'embed')


# ---------------------------------------------------------------------------
# research vs operator differ on key fields
# ---------------------------------------------------------------------------

class TestModesDiffer(unittest.TestCase):

    def test_research_vs_operator_show_gt_overlay(self):
        r = apply_runtime_mode(_cfg(), 'research')
        o = apply_runtime_mode(_cfg(), 'operator')
        self.assertNotEqual(r.SHOW_GT_OVERLAY, o.SHOW_GT_OVERLAY)

    def test_research_vs_operator_minimal_overlay(self):
        r = apply_runtime_mode(_cfg(), 'research')
        o = apply_runtime_mode(_cfg(), 'operator')
        self.assertNotEqual(r.OPERATOR_MINIMAL_OVERLAY, o.OPERATOR_MINIMAL_OVERLAY)

    def test_operator_vs_embedded_roi_assist(self):
        o = apply_runtime_mode(_cfg(), 'operator')
        e = apply_runtime_mode(_cfg(), 'embedded')
        self.assertTrue(o.ROI_ASSIST_ENABLED)
        self.assertFalse(e.ROI_ASSIST_ENABLED)

    def test_operator_vs_embedded_night_enabled(self):
        o = apply_runtime_mode(_cfg(), 'operator')
        e = apply_runtime_mode(_cfg(), 'embedded')
        self.assertTrue(o.NIGHT_ENABLED)
        self.assertFalse(e.NIGHT_ENABLED)


if __name__ == '__main__':
    unittest.main()
