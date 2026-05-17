from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from app.qml_bridge import (
    AppState,
    DtsBridge,
    DtsFrameProvider,
    FrameProvider,
    GeoBridge,
    GtAssistBridge,
    GtFrameProvider,
    SettingsBridge,
    TargetLabBridge,
    TrackerBridge,
)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Gimbal Operator Station")
    app.setOrganizationName("GimbalAI")

    engine = QQmlApplicationEngine()
    frame_provider = FrameProvider()
    dts_frame_provider = DtsFrameProvider()
    gt_frame_provider = GtFrameProvider()
    settings_bridge = SettingsBridge()
    geo_bridge = GeoBridge(settings_bridge)
    bridge = TrackerBridge(frame_provider, geo_bridge=geo_bridge, settings_bridge=settings_bridge)
    dts_bridge = DtsBridge(dts_frame_provider)
    gt_assist_bridge = GtAssistBridge(gt_frame_provider)
    target_lab_bridge = TargetLabBridge(dts_bridge=dts_bridge, gt_assist_bridge=gt_assist_bridge)

    engine.addImageProvider("frames", frame_provider)
    engine.addImageProvider("dtsFrames", dts_frame_provider)
    engine.addImageProvider("gtFrames", gt_frame_provider)
    app_state = AppState(tracker_bridge=bridge, dts_bridge=dts_bridge)

    engine.rootContext().setContextProperty("bridge", bridge)
    engine.rootContext().setContextProperty("dtsBridge", dts_bridge)
    engine.rootContext().setContextProperty("gtAssistBridge", gt_assist_bridge)
    engine.rootContext().setContextProperty("targetLabBridge", target_lab_bridge)
    engine.rootContext().setContextProperty("appState", app_state)
    engine.rootContext().setContextProperty("dtsRecordsModel", dts_bridge.recordsModel)
    engine.rootContext().setContextProperty("settingsBridge", settings_bridge)
    engine.rootContext().setContextProperty("geoBridge", geo_bridge)

    qml_file = ROOT / "app" / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        print("ERROR: не удалось загрузить QML")
        return 1

    app.aboutToQuit.connect(bridge.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
