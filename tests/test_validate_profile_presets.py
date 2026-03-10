#!/usr/bin/env python3
"""Unit tests for python_scripts/validate_profile_presets.py.

Tests exercise the core logic (extract_mapping_keys / validate_file /
validate_files) without running the CLI or touching the real configs dir.
"""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# Allow running as: python tests/test_validate_profile_presets.py
sys.path.insert(0, str(Path(__file__).parent.parent / 'python_scripts'))

from validate_profile_presets import (
    FileResult,
    build_type_rules,
    extract_mapping_keys,
    validate_file,
    validate_files,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROFILE_IO = Path(__file__).parent.parent / 'src' / 'uav_tracker' / 'profile_io.py'
_SRC_DIR = Path(__file__).parent.parent / 'src'


def _write_yaml(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content), encoding='utf-8')


# ---------------------------------------------------------------------------
# extract_mapping_keys
# ---------------------------------------------------------------------------

class TestExtractMappingKeys(unittest.TestCase):
    def test_extracts_keys_from_real_profile_io(self):
        keys = extract_mapping_keys(_PROFILE_IO)
        self.assertGreater(len(keys), 80, 'Expected 80+ mapping keys')
        self.assertIn('conf_thresh', keys)
        self.assertIn('night_enabled', keys)
        self.assertIn('lock_mode_acquire_frames', keys)

    def test_returns_empty_for_nonexistent_file(self):
        keys = extract_mapping_keys(Path('/tmp/__no_such_file__.py'))
        self.assertEqual(keys, frozenset())

    def test_returns_empty_for_file_without_mapping(self):
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as fh:
            fh.write('x = 1\n')
            tmp = Path(fh.name)
        try:
            keys = extract_mapping_keys(tmp)
            self.assertEqual(keys, frozenset())
        finally:
            tmp.unlink()

    def test_parses_synthetic_mapping(self):
        src = textwrap.dedent("""\
            def apply_overrides(cfg, overrides):
                mapping = {
                    'alpha': 'ALPHA',
                    'beta': 'BETA',
                }
                for k, v in mapping.items():
                    pass
        """)
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as fh:
            fh.write(src)
            tmp = Path(fh.name)
        try:
            keys = extract_mapping_keys(tmp)
            self.assertEqual(keys, frozenset({'alpha', 'beta'}))
        finally:
            tmp.unlink()


# ---------------------------------------------------------------------------
# validate_file
# ---------------------------------------------------------------------------

class TestValidateFile(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.known = extract_mapping_keys(_PROFILE_IO)
        self.type_rules = build_type_rules(_PROFILE_IO, _SRC_DIR)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _yaml(self, name: str, content: str) -> Path:
        p = self.tmp / name
        _write_yaml(p, content)
        return p

    def test_valid_preset_is_ok(self):
        p = self._yaml('good.yaml', 'conf_thresh: 0.30\nnight_enabled: true\n')
        result = validate_file(p, self.known, self.type_rules)
        self.assertTrue(result.ok)
        self.assertEqual(result.unknown, [])
        self.assertEqual(result.type_errors, [])

    def test_unknown_key_detected(self):
        p = self._yaml('bad.yaml', 'totally_fake_key: 99\n')
        result = validate_file(p, self.known, self.type_rules)
        self.assertFalse(result.ok)
        self.assertIn('totally_fake_key', result.unknown)

    def test_informational_name_key_is_allowed(self):
        p = self._yaml('named.yaml', 'name: my_preset\nconf_thresh: 0.25\n')
        result = validate_file(p, self.known, self.type_rules)
        self.assertTrue(result.ok)
        self.assertNotIn('name', result.unknown)

    def test_profile_only_key_is_allowed(self):
        p = self._yaml('profile.yaml', 'preset: night\nsource: /dev/video0\n')
        result = validate_file(p, self.known, self.type_rules)
        self.assertTrue(result.ok)

    def test_type_error_bool_expected(self):
        # night_enabled must be bool; integer 1 should fail
        p = self._yaml('type_err.yaml', 'night_enabled: 1\n')
        result = validate_file(p, self.known, self.type_rules)
        self.assertFalse(result.ok)
        self.assertTrue(any('night_enabled' in te for te in result.type_errors))

    def test_type_int_with_float_rejected_where_int_required(self):
        # lock_mode_acquire_frames must be int, float should fail
        p = self._yaml('float_for_int.yaml', 'lock_mode_acquire_frames: 3.5\n')
        result = validate_file(p, self.known, self.type_rules)
        self.assertFalse(result.ok)
        self.assertTrue(any('lock_mode_acquire_frames' in te for te in result.type_errors))

    def test_non_flat_yaml_is_skipped(self):
        p = self._yaml('nested.yaml', 'train:\n  epochs: 100\n  batch: 8\n')
        result = validate_file(p, self.known, self.type_rules)
        self.assertTrue(result.skipped)
        self.assertIn('non-flat', result.skipped)

    def test_empty_yaml_is_ok(self):
        p = self._yaml('empty.yaml', '')
        result = validate_file(p, self.known, self.type_rules)
        self.assertTrue(result.ok)


# ---------------------------------------------------------------------------
# validate_files
# ---------------------------------------------------------------------------

class TestValidateFiles(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.known = extract_mapping_keys(_PROFILE_IO)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_returns_one_result_per_file(self):
        p1 = self.tmp / 'a.yaml'
        p2 = self.tmp / 'b.yaml'
        _write_yaml(p1, 'conf_thresh: 0.3\n')
        _write_yaml(p2, 'imgsz: 640\n')
        results = validate_files([p1, p2], self.known)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.ok for r in results))

    def test_real_configs_all_pass(self):
        """All *.yaml in configs/ that are flat should be valid."""
        configs_dir = Path(__file__).parent.parent / 'configs'
        paths = sorted(configs_dir.glob('*.yaml'))
        results = validate_files(paths, self.known)
        failures = [r for r in results if not r.ok and not r.skipped]
        self.assertEqual(
            failures, [],
            msg='Unexpected failures: ' + ', '.join(str(r.path.name) for r in failures),
        )


if __name__ == '__main__':
    unittest.main()
