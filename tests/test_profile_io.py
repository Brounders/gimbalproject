"""Unit tests for src/uav_tracker/profile_io.py.

Covers:
  A) config_to_profile and apply_overrides — pure functions
  B) save_profile and load_profile — round-trip via tempfile
  C) load_yaml — valid YAML and missing file via tempfile
  D) available_presets — monkeypatched PRESET_DIR
  E) load_preset — monkeypatched PRESET_DIR

Runs without cv2, ultralytics, torch, or hardware.

Usage:
    PYTHONPATH=src python3 -m unittest -v tests.test_profile_io
"""

import os
import tempfile
import unittest
import yaml
from pathlib import Path
from unittest.mock import patch

from uav_tracker.config import Config
from uav_tracker.profile_io import (
    apply_overrides,
    available_presets,
    config_to_profile,
    load_preset,
    load_profile,
    load_yaml,
    save_profile,
)


# ---------------------------------------------------------------------------
# A) Pure functions: config_to_profile and apply_overrides
# ---------------------------------------------------------------------------

class TestConfigToProfile(unittest.TestCase):
    """config_to_profile converts Config to a plain dict."""

    def setUp(self):
        self.cfg = Config()
        self.profile = config_to_profile(self.cfg)

    def test_returns_dict(self):
        self.assertIsInstance(self.profile, dict)

    def test_contains_conf_thresh(self):
        self.assertIn('CONF_THRESH', self.profile)

    def test_contains_img_size(self):
        self.assertIn('IMG_SIZE', self.profile)

    def test_contains_device(self):
        self.assertIn('DEVICE', self.profile)

    def test_contains_runtime_mode(self):
        self.assertIn('RUNTIME_MODE', self.profile)

    def test_contains_model_path(self):
        self.assertIn('MODEL_PATH', self.profile)

    def test_conf_thresh_value_matches_config(self):
        self.assertAlmostEqual(self.profile['CONF_THRESH'], self.cfg.CONF_THRESH)

    def test_img_size_value_matches_config(self):
        self.assertEqual(self.profile['IMG_SIZE'], self.cfg.IMG_SIZE)

    def test_non_empty(self):
        self.assertGreater(len(self.profile), 10)

    def test_custom_conf_thresh_reflected(self):
        cfg = Config(CONF_THRESH=0.77)
        profile = config_to_profile(cfg)
        self.assertAlmostEqual(profile['CONF_THRESH'], 0.77)


class TestApplyOverrides(unittest.TestCase):
    """apply_overrides applies preset keys to Config and returns same object."""

    def test_returns_same_object(self):
        cfg = Config()
        result = apply_overrides(cfg, {})
        self.assertIs(result, cfg)

    def test_applies_conf_thresh(self):
        cfg = Config()
        result = apply_overrides(cfg, {'conf_thresh': 0.55})
        self.assertAlmostEqual(result.CONF_THRESH, 0.55)

    def test_applies_img_size(self):
        cfg = Config()
        result = apply_overrides(cfg, {'imgsz': 1280})
        self.assertEqual(result.IMG_SIZE, 1280)

    def test_applies_device(self):
        cfg = Config()
        result = apply_overrides(cfg, {'device': 'cpu'})
        self.assertEqual(result.DEVICE, 'cpu')

    def test_applies_night_enabled_false(self):
        cfg = Config()
        result = apply_overrides(cfg, {'night_enabled': False})
        self.assertFalse(result.NIGHT_ENABLED)

    def test_applies_global_scan_interval(self):
        cfg = Config()
        result = apply_overrides(cfg, {'global_scan_interval': 12})
        self.assertEqual(result.GLOBAL_SCAN_INTERVAL, 12)

    def test_ignores_unknown_key(self):
        """Unknown keys must not raise — they are silently skipped."""
        cfg = Config()
        original_thresh = cfg.CONF_THRESH
        try:
            result = apply_overrides(cfg, {'totally_unknown_key': 'value', 'another_bad': 42})
        except Exception as exc:
            self.fail(f'apply_overrides raised on unknown key: {exc}')
        # Unrelated fields must be unchanged
        self.assertAlmostEqual(result.CONF_THRESH, original_thresh)

    def test_ignores_small_target_mode_key(self):
        """small_target_mode maps to None in mapping — must not raise."""
        cfg = Config()
        try:
            apply_overrides(cfg, {'small_target_mode': True})
        except Exception as exc:
            self.fail(f'apply_overrides raised on small_target_mode: {exc}')

    def test_multiple_overrides_applied(self):
        cfg = Config()
        apply_overrides(cfg, {'conf_thresh': 0.42, 'imgsz': 320, 'device': 'cpu'})
        self.assertAlmostEqual(cfg.CONF_THRESH, 0.42)
        self.assertEqual(cfg.IMG_SIZE, 320)
        self.assertEqual(cfg.DEVICE, 'cpu')

    def test_apply_overrides_with_known_runtime_mode(self):
        """runtime_mode key triggers apply_runtime_mode side-effect."""
        cfg = Config()
        result = apply_overrides(cfg, {'runtime_mode': 'operator'})
        self.assertEqual(result.RUNTIME_MODE, 'operator')

    def test_empty_overrides_leaves_config_unchanged(self):
        default = Config()
        cfg = Config()
        apply_overrides(cfg, {})
        self.assertEqual(cfg.CONF_THRESH, default.CONF_THRESH)
        self.assertEqual(cfg.IMG_SIZE, default.IMG_SIZE)
        self.assertEqual(cfg.DEVICE, default.DEVICE)

    def test_small_target_preset_disables_night_detector_for_eo_day(self):
        cfg, data = load_preset('small_target', Config())

        self.assertIs(data.get('night_enabled'), False)
        self.assertFalse(cfg.NIGHT_ENABLED)


# ---------------------------------------------------------------------------
# B) I/O functions: save_profile and load_profile
# ---------------------------------------------------------------------------

class TestSaveLoadProfile(unittest.TestCase):
    """save_profile writes YAML; load_profile reads it back identically."""

    def test_round_trip_simple_dict(self):
        profile = {'key1': 'value1', 'key2': 42, 'key3': 3.14}
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / 'test_profile.yaml'
            save_profile(path, profile)
            loaded = load_profile(path)
        self.assertEqual(loaded, profile)

    def test_save_creates_file(self):
        profile = {'CONF_THRESH': 0.3, 'IMG_SIZE': 640}
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / 'profile.yaml'
            self.assertFalse(path.exists())
            save_profile(path, profile)
            self.assertTrue(path.exists())

    def test_round_trip_config_profile(self):
        cfg = Config()
        profile = config_to_profile(cfg)
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / 'config.yaml'
            save_profile(path, profile)
            loaded = load_profile(path)
        self.assertEqual(loaded['CONF_THRESH'], profile['CONF_THRESH'])
        self.assertEqual(loaded['IMG_SIZE'], profile['IMG_SIZE'])
        self.assertEqual(loaded['DEVICE'], profile['DEVICE'])

    def test_round_trip_bool_values(self):
        profile = {'NIGHT_ENABLED': True, 'BUDGET_ENABLED': False}
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / 'bools.yaml'
            save_profile(path, profile)
            loaded = load_profile(path)
        self.assertIs(loaded['NIGHT_ENABLED'], True)
        self.assertIs(loaded['BUDGET_ENABLED'], False)

    def test_save_creates_parent_dirs(self):
        """save_profile must create missing parent directories."""
        profile = {'x': 1}
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / 'subdir' / 'nested' / 'profile.yaml'
            save_profile(path, profile)
            self.assertTrue(path.exists())

    def test_load_profile_missing_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing = Path(tmp_dir) / 'does_not_exist.yaml'
            with self.assertRaises((FileNotFoundError, OSError)):
                load_profile(missing)

    def test_round_trip_numeric_types_preserved(self):
        profile = {'int_val': 640, 'float_val': 0.30}
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / 'types.yaml'
            save_profile(path, profile)
            loaded = load_profile(path)
        self.assertEqual(loaded['int_val'], 640)
        self.assertAlmostEqual(loaded['float_val'], 0.30)


# ---------------------------------------------------------------------------
# C) load_yaml
# ---------------------------------------------------------------------------

class TestLoadYaml(unittest.TestCase):
    """load_yaml parses valid YAML and raises on missing file."""

    def test_loads_simple_dict(self):
        content = 'key1: value1\nkey2: 42\n'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = load_yaml(tmp_path)
        finally:
            os.unlink(tmp_path)
        self.assertEqual(result['key1'], 'value1')
        self.assertEqual(result['key2'], 42)

    def test_loads_nested_dict(self):
        content = 'outer:\n  inner: 99\n'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = load_yaml(tmp_path)
        finally:
            os.unlink(tmp_path)
        self.assertEqual(result['outer']['inner'], 99)

    def test_empty_yaml_returns_empty_dict(self):
        """An empty YAML file must return {} not None."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write('')
            tmp_path = f.name
        try:
            result = load_yaml(tmp_path)
        finally:
            os.unlink(tmp_path)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_returns_dict(self):
        content = 'conf_thresh: 0.3\n'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = load_yaml(tmp_path)
        finally:
            os.unlink(tmp_path)
        self.assertIsInstance(result, dict)

    def test_missing_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing = Path(tmp_dir) / 'no_such_file.yaml'
            with self.assertRaises((FileNotFoundError, OSError)):
                load_yaml(missing)

    def test_accepts_pathlib_path(self):
        content = 'device: cpu\n'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = load_yaml(Path(tmp_path))
        finally:
            os.unlink(tmp_path)
        self.assertEqual(result['device'], 'cpu')


# ---------------------------------------------------------------------------
# D) available_presets — monkeypatched PRESET_DIR
# ---------------------------------------------------------------------------

class TestAvailablePresets(unittest.TestCase):
    """available_presets scans PRESET_DIR for preset-style YAML files."""

    def test_empty_dir_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                result = available_presets()
        self.assertEqual(result, [])

    def test_single_preset_yaml_returned(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            preset_path = Path(tmp_dir) / 'night.yaml'
            # Write a preset-style dict (no PROFILE_KEYS)
            preset_path.write_text(
                yaml.safe_dump({'conf_thresh': 0.25, 'imgsz': 640}),
                encoding='utf-8'
            )
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                result = available_presets()
        self.assertIn('night', result)

    def test_multiple_preset_yamls_returned(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for name in ('day', 'night', 'ir'):
                p = Path(tmp_dir) / f'{name}.yaml'
                p.write_text(
                    yaml.safe_dump({'conf_thresh': 0.3}),
                    encoding='utf-8'
                )
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                result = available_presets()
        self.assertIn('day', result)
        self.assertIn('night', result)
        self.assertIn('ir', result)
        self.assertEqual(len(result), 3)

    def test_txt_file_not_included(self):
        """Non-YAML files must be excluded from results."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            txt_path = Path(tmp_dir) / 'not_a_preset.txt'
            txt_path.write_text('conf_thresh: 0.3\n', encoding='utf-8')
            yaml_path = Path(tmp_dir) / 'real_preset.yaml'
            yaml_path.write_text(
                yaml.safe_dump({'conf_thresh': 0.3}),
                encoding='utf-8'
            )
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                result = available_presets()
        self.assertNotIn('not_a_preset', result)
        self.assertIn('real_preset', result)

    def test_profile_yaml_excluded(self):
        """Files with PROFILE_KEYS (preset/source/record_output/output_path) are not presets."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # This is a profile, not a preset — has 'preset' key
            profile_path = Path(tmp_dir) / 'myprofile.yaml'
            profile_path.write_text(
                yaml.safe_dump({'preset': 'night', 'source': '/dev/video0'}),
                encoding='utf-8'
            )
            # This is a true preset — no PROFILE_KEYS
            preset_path = Path(tmp_dir) / 'night.yaml'
            preset_path.write_text(
                yaml.safe_dump({'conf_thresh': 0.25}),
                encoding='utf-8'
            )
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                result = available_presets()
        self.assertNotIn('myprofile', result)
        self.assertIn('night', result)

    def test_result_is_sorted(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for name in ('zebra', 'alpha', 'mango'):
                p = Path(tmp_dir) / f'{name}.yaml'
                p.write_text(
                    yaml.safe_dump({'conf_thresh': 0.3}),
                    encoding='utf-8'
                )
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                result = available_presets()
        self.assertEqual(result, sorted(result))

    def test_nonexistent_preset_dir_returns_empty(self):
        """If PRESET_DIR does not exist, return []."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            nonexistent = Path(tmp_dir) / 'does_not_exist'
            with patch('uav_tracker.profile_io.PRESET_DIR', new=nonexistent):
                result = available_presets()
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# E) load_preset — monkeypatched PRESET_DIR
# ---------------------------------------------------------------------------

class TestLoadPreset(unittest.TestCase):
    """load_preset reads a preset YAML and applies overrides to Config."""

    def _write_preset(self, tmp_dir: str, name: str, data: dict) -> None:
        path = Path(tmp_dir) / f'{name}.yaml'
        path.write_text(yaml.safe_dump(data), encoding='utf-8')

    def test_returns_tuple_of_config_and_dict(self):
        preset_data = {'conf_thresh': 0.20, 'imgsz': 320}
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._write_preset(tmp_dir, 'test_preset', preset_data)
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                result = load_preset('test_preset')
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_first_element_is_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._write_preset(tmp_dir, 'simple', {'conf_thresh': 0.40})
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                cfg, data = load_preset('simple')
        self.assertIsInstance(cfg, Config)

    def test_second_element_is_dict(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._write_preset(tmp_dir, 'simple', {'conf_thresh': 0.40})
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                cfg, data = load_preset('simple')
        self.assertIsInstance(data, dict)

    def test_conf_thresh_override_applied_to_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._write_preset(tmp_dir, 'night', {'conf_thresh': 0.18})
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                cfg, data = load_preset('night')
        self.assertAlmostEqual(cfg.CONF_THRESH, 0.18)

    def test_img_size_override_applied(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._write_preset(tmp_dir, 'small', {'imgsz': 320})
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                cfg, data = load_preset('small')
        self.assertEqual(cfg.IMG_SIZE, 320)

    def test_device_override_applied(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._write_preset(tmp_dir, 'embedded', {'device': 'cpu'})
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                cfg, data = load_preset('embedded')
        self.assertEqual(cfg.DEVICE, 'cpu')

    def test_raw_data_dict_matches_yaml_contents(self):
        preset_data = {'conf_thresh': 0.25, 'imgsz': 640, 'device': 'mps'}
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._write_preset(tmp_dir, 'verify', preset_data)
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                cfg, data = load_preset('verify')
        self.assertEqual(data['conf_thresh'], 0.25)
        self.assertEqual(data['imgsz'], 640)

    def test_existing_cfg_is_used_when_provided(self):
        """load_preset should accept an existing Config and mutate it."""
        existing_cfg = Config(IMG_SIZE=1280)
        preset_data = {'conf_thresh': 0.35}
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._write_preset(tmp_dir, 'partial', preset_data)
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                result_cfg, data = load_preset('partial', cfg=existing_cfg)
        # conf_thresh overridden
        self.assertAlmostEqual(result_cfg.CONF_THRESH, 0.35)

    def test_missing_preset_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                with self.assertRaises((FileNotFoundError, OSError)):
                    load_preset('nonexistent_preset')

    def test_multiple_overrides_in_preset(self):
        preset_data = {
            'conf_thresh': 0.22,
            'imgsz': 960,
            'night_enabled': False,
            'global_scan_interval': 10,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._write_preset(tmp_dir, 'full', preset_data)
            with patch('uav_tracker.profile_io.PRESET_DIR', new=Path(tmp_dir)):
                cfg, data = load_preset('full')
        self.assertAlmostEqual(cfg.CONF_THRESH, 0.22)
        self.assertEqual(cfg.IMG_SIZE, 960)
        self.assertFalse(cfg.NIGHT_ENABLED)
        self.assertEqual(cfg.GLOBAL_SCAN_INTERVAL, 10)


if __name__ == '__main__':
    unittest.main()
