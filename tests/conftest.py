"""pytest configuration — adds src/ to sys.path so tests can import uav_tracker."""
import sys
from pathlib import Path

# Allow `from uav_tracker.xxx import yyy` without PYTHONPATH=src in env
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
