"""Regression tests for uav_tracker package import boundary.

Verifies that config and tracking submodules can be imported without
pulling in heavy runtime dependencies (cv2, ultralytics, torch).

Run:
    PYTHONPATH=src python3 -m unittest -q tests.test_package_import
"""

import pathlib
import sys
import unittest

_SRC = pathlib.Path(__file__).parent.parent / 'src'
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestPackageImportBoundary(unittest.TestCase):

    def test_config_import_is_isolated(self):
        """from uav_tracker.config import Config must work without pipeline/cv2."""
        from uav_tracker.config import Config
        cfg = Config()
        self.assertEqual(cfg.PREFER_CLASS_ID, 0)

    def test_target_manager_import_is_isolated(self):
        """from uav_tracker.tracking.target_manager import TargetManager must work without cv2/ultralytics."""
        from uav_tracker.tracking.target_manager import TargetManager
        from uav_tracker.config import Config
        mgr = TargetManager(Config())
        self.assertIsNone(mgr.active_id)

    def test_package_level_config_export(self):
        """from uav_tracker import Config must work (eager export preserved)."""
        from uav_tracker import Config
        self.assertTrue(hasattr(Config(), 'LOCK_CONFIRM_FRAMES'))


if __name__ == '__main__':
    unittest.main()
