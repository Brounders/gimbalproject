#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PySide6.QtCore import QCoreApplication, QTimer

from app.qml_bridge import FrameProvider, TrackerBridge


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test the QML MVP bridge without opening a UI window.")
    parser.add_argument("--source", default="test_videos/cli_smoke_test.mp4")
    parser.add_argument("--duration-ms", type=int, default=5000)
    parser.add_argument("--min-frames", type=int, default=5)
    parser.add_argument("--cycles", type=int, default=1)
    return parser.parse_args()


def run_cycle(source: str, duration_ms: int) -> dict:
    app = QCoreApplication.instance() or QCoreApplication([])
    provider = FrameProvider()
    bridge = TrackerBridge(provider)
    seen = {"frames": 0, "stats": 0}
    bridge.frameIdChanged.connect(lambda: seen.__setitem__("frames", bridge.frameId))
    bridge.fpsChanged.connect(lambda: seen.__setitem__("stats", seen["stats"] + 1))
    bridge.startTracking("video", source, 0)
    QTimer.singleShot(duration_ms, app.quit)
    app.exec()
    bridge.shutdown()
    return {
        "frames": int(seen["frames"]),
        "stats_updates": int(seen["stats"]),
        "running": bool(bridge.isRunning),
        "state": str(bridge.trackingState),
        "fps": int(bridge.fps),
        "last_action": str(bridge.lastAction),
    }


def main() -> int:
    args = parse_args()
    failures = []
    for idx in range(max(1, int(args.cycles))):
        result = run_cycle(args.source, int(args.duration_ms))
        print(f"[cycle {idx + 1}] {result}")
        if result["frames"] < int(args.min_frames):
            failures.append(f"cycle {idx + 1}: frames<{args.min_frames}")
        if result["running"]:
            failures.append(f"cycle {idx + 1}: bridge still running after shutdown")
        if result["state"] != "SEARCH":
            failures.append(f"cycle {idx + 1}: state={result['state']!r}")
    if failures:
        for failure in failures:
            print(f"[fail] {failure}")
        return 1
    print("[pass] qml bridge smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
