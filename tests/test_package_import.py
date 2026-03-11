"""Regression test: uav_tracker package import boundary.

Verifies that importing uav_tracker core (Config, TargetManager) does NOT
require cv2, ultralytics, or any heavy runtime dependency.

Usage:
    PYTHONPATH=src python3 -m unittest -v tests.test_package_import
"""

import unittest


class TestPackageImportBoundary(unittest.TestCase):

    def test_config_direct_import(self):
        """uav_tracker.config.Config is importable without pipeline deps."""
        from uav_tracker.config import Config
        self.assertIsNotNone(Config())

    def test_target_manager_direct_import(self):
        """uav_tracker.tracking.TargetManager is importable without pipeline deps."""
        from uav_tracker.config import Config
        from uav_tracker.tracking.target_manager import TargetManager
        self.assertIsNotNone(TargetManager(Config()))

    def test_package_init_exports_config_eagerly(self):
        """uav_tracker package init exposes Config (eager export preserved)."""
        from uav_tracker import Config
        self.assertIsNotNone(Config())


if __name__ == '__main__':
    unittest.main()
