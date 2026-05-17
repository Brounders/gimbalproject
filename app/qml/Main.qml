import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import "components"

ApplicationWindow {
    id: root
    visible: true
    width: 1440
    height: 900
    title: "GIMBAL · OPERATOR STATION"
    color: "#0A0F14"

    Component.onCompleted: showMaximized()

    // ── Общее состояние ──────────────────────────────────────────────
    property string trackingState:    bridge ? bridge.trackingState : "SEARCH"
    property string targetLifecycle:  bridge ? bridge.targetLifecycle : "OFFLINE"
    property string activeSource:     bridge ? bridge.activeSource : "—"
    property bool   isRunning:        bridge ? bridge.isRunning : false
    property bool   isRecording:      bridge ? bridge.isRecording : false
    property string currentMode:      bridge ? bridge.currentMode : "ДЕНЬ"
    property string currentSource:    bridge ? bridge.currentSource : ""
    property int    targetId:         bridge ? bridge.targetId : 0
    property real   confidence:       bridge ? bridge.confidence : 0.0
    property int    fps:              bridge ? bridge.fps : 0
    property int    latencyMs:        bridge ? bridge.latencyMs : 0
    property int    activeTargets:    bridge ? bridge.activeTargets : 0
    property int    idSwitches:       bridge ? bridge.idSwitches : 0
    property real   falseLockRisk:    bridge ? bridge.falseLockRisk : 0.0
    property real   lockScore:        bridge ? bridge.lockScore : 0.0
    property real   targetReliability: bridge ? bridge.targetReliability : 0.0
    property real   targetPresentProbability: bridge ? bridge.targetPresentProbability : 0.0
    property string activeBboxJson:   bridge ? bridge.activeBboxJson : "[]"
    property string displayTargetsJson: bridge ? bridge.displayTargetsJson : "[]"
    property int    frameWidth:       bridge ? bridge.frameWidth : 0
    property int    frameHeight:      bridge ? bridge.frameHeight : 0
    property string lastAction:       bridge ? bridge.lastAction : "Система готова"
    property int    frameId:          bridge ? bridge.frameId : 0
    property bool   targetLabOpen:    false
    property bool   dtsOpen:          false
    property bool   settingsOpen:     false
    property bool   expertOpen:       false
    property bool   gtAssistOpen:     false
    property bool   calibOpen:        false
    property bool   diagOpen:         false
    property bool   aboutOpen:        false
    property bool   markBBoxFlash:    false
    property bool   showSourceDialog: false
    property bool   _targetCollapsed: false
    property bool   _telCollapsed:    true
    property bool   _mapCollapsed:    false
    property bool   _mapExpanded:     false

    // ── Right panel height distribution ──────────────────────────────
    property int  _openPanelCount: (!_targetCollapsed ? 1 : 0) + (!_telCollapsed ? 1 : 0) + (!_mapCollapsed ? 1 : 0)
    // available = window - topBar(44) - drawer(32) - margins(20) - 3 headers(114) - 2 gaps(16)
    property real _panelContentMaxH: Math.max(80, (height - 226) / Math.max(1, _openPanelCount))

    // ── Mock-таймер (1 сек) ──────────────────────────────────────────
    Timer {
        interval: 1000
        running: false
        repeat: true
        onTriggered: {
            root.fps           = 24 + Math.floor(Math.random() * 7)
            root.latencyMs     = 10 + Math.floor(Math.random() * 9)
            root.confidence    = 0.60 + Math.random() * 0.38
            root.falseLockRisk = Math.random() * 0.28
            root.activeTargets = root.trackingState !== "SEARCH" ? 1 : 0
            if (Math.random() < 0.07) root.idSwitches++
            var r = Math.random()
            if      (r < 0.62) root.trackingState = "LOCK"
            else if (r < 0.78) root.trackingState = "TRACK"
            else if (r < 0.92) root.trackingState = "SEARCH"
            else { root.trackingState = "LOST"; root.lastAction = "Цель потеряна" }
        }
    }

    Timer { id: markTimer; interval: 700; onTriggered: root.markBBoxFlash = false }
    Timer { id: dtsReloadAfterClickTimer; interval: 1100; onTriggered: if (dtsBridge) dtsBridge.reload() }

    // ── VideoSurface — FULL SCREEN (z=0) ────────────────────────────
    VideoSurface {
        anchors.fill: parent
        trackingState: root.trackingState
        targetLifecycle: root.targetLifecycle
        isRunning:     root.isRunning
        targetId:      root.targetId
        confidence:    root.confidence
        currentMode:   root.currentMode
        fps:           root.fps
        frameId:       root.frameId
        markBBoxFlash: root.markBBoxFlash
        frameWidth:    root.frameWidth
        frameHeight:   root.frameHeight
        activeBboxJson: root.activeBboxJson
        displayTargetsJson: root.displayTargetsJson
        onTargetClicked: function(frameX, frameY) {
            bridge.selectTargetAtFrame(frameX, frameY)
            bottomDrawer.addLog("ok", "Цель выбрана кликом: " + frameX + "," + frameY)
            dtsReloadAfterClickTimer.restart()
        }
    }

    // ── TopBar — floating at top (z=20) ─────────────────────────────
    TopBar {
        id: topBar
        anchors.top:   parent.top
        anchors.left:  parent.left
        anchors.right: parent.right
        height: 44
        z: 20
        isRunning:     root.isRunning
        isRecording:   root.isRecording
        currentMode:   root.currentMode
        currentSource: root.currentSource
        trackingState: root.trackingState
        targetId:      root.targetId
        onModeChanged:      function(m) { bridge.setMode(m) }
        onRecordToggled:    bridge.toggleRecording()
        onSourceChanged:    function(s) { }
        onTargetLabRequested: root.targetLabOpen = true
        onDtsRequested:     root.targetLabOpen = true
        onExpertRequested:  root.expertOpen   = true
        onGtAssistRequested: root.gtAssistOpen = true
        onCalibRequested:   root.calibOpen    = true
        onDiagRequested:    root.diagOpen     = true
        onSettingsRequested: root.settingsOpen = true
        onAboutRequested:   root.aboutOpen    = true
    }

    // ── LeftSidebar — floating left-center (z=10) ───────────────────
    LeftSidebar {
        id: leftSidebar
        anchors.left:           parent.left
        anchors.leftMargin:     16
        anchors.verticalCenter: parent.verticalCenter
        z: 10
        isRunning:     root.isRunning
        isRecording:   root.isRecording
        trackingState: root.trackingState
        currentSource: root.currentSource
        targetLifecycle: root.targetLifecycle
        activeSource:   root.activeSource
        lockScore:      root.lockScore
        reliability:    root.targetReliability

        onStartClicked: {
            root.showSourceDialog = true
        }
        onStopClicked: {
            bridge.stopTracking()
            bottomDrawer.addLog("info", "Трекинг остановлен")
        }
        onRecToggled: {
            bridge.toggleRecording()
            bottomDrawer.addLog(root.isRecording ? "ok" : "info",
                                root.isRecording ? "Запись начата" : "Запись остановлена")
        }
        onLockClicked: {
            if (root.isRunning) {
                bridge.confirmTarget()
                bottomDrawer.addLog("ok", "LOCK подтверждён")
            }
        }
        onNextTargetClicked: {
            bridge.nextTarget()
        }
        onMarkBBoxClicked: {
            root.markBBoxFlash = true
            markTimer.restart()
            bridge.markBBox()
        }
    }

    // ── Right panel scrollable stack (z=10) ─────────────────────────
    Flickable {
        id: rightStack
        anchors.top:         topBar.bottom
        anchors.topMargin:   12
        anchors.right:       parent.right
        anchors.rightMargin: 16
        anchors.bottom:      bottomDrawer.top
        anchors.bottomMargin: 8
        width: 224
        opacity: root._mapExpanded ? 0 : 1
        visible: opacity > 0.01
        z: 10
        Behavior on opacity { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
        contentWidth:  width
        contentHeight: rightCol.implicitHeight
        clip:          false
        flickableDirection: Flickable.VerticalFlick
        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
            anchors.right:      parent.right
            anchors.rightMargin: -10
        }

        Column {
            id: rightCol
            width: parent.width
            spacing: 8

            TargetPanel {
                id: targetPanelWgt
                visible: !root._mapExpanded
                width: parent.width
                panelMaxH:     root._panelContentMaxH
                collapsed:     root._targetCollapsed
                trackingState: root.trackingState
                lifecycleState: root.targetLifecycle
                activeSource:  root.activeSource
                targetId:      root.targetId
                confidence:    root.confidence
                lockScore:     root.lockScore
                reliability:   root.targetReliability
                presentProbability: root.targetPresentProbability
                currentMode:   root.currentMode
                isRunning:     root.isRunning
                onCollapseToggled: root._targetCollapsed = !root._targetCollapsed
            }

            TelemetryPanel {
                id: telemetryPanelWgt
                visible: !root._mapExpanded
                width: parent.width
                panelMaxH:     root._panelContentMaxH
                collapsed:     root._telCollapsed
                fps:           root.fps
                latencyMs:     root.latencyMs
                activeTargets: root.activeTargets
                idSwitches:    root.idSwitches
                falseLockRisk: root.falseLockRisk
                targetLifecycle: root.targetLifecycle
                activeSource:   root.activeSource
                lockScore:      root.lockScore
                reliability:    root.targetReliability
                isRunning:     root.isRunning
                confidence:    root.confidence
                onCollapseToggled: root._telCollapsed = !root._telCollapsed
            }

            MapPanel {
                id: mapPanelWgt
                width: parent.width
                panelMaxH:     root._panelContentMaxH
                collapsed:     root._mapCollapsed
                expanded:      false
                isRunning:     root.isRunning
                trackingState: root.trackingState
                targetId:      root.targetId
                confidence:    root.confidence
                fps:           root.fps
                latencyMs:     root.latencyMs
                activeTargets: root.activeTargets
                idSwitches:    root.idSwitches
                falseLockRisk: root.falseLockRisk
                deviceLat:     settingsBridge ? settingsBridge.deviceLat : 59.9386
                deviceLon:     settingsBridge ? settingsBridge.deviceLon : 30.3141
                deviceAltM:    settingsBridge ? settingsBridge.deviceAltM : 25
                headingDeg:    settingsBridge ? settingsBridge.headingDeg : 87
                yawOffsetDeg:  settingsBridge ? settingsBridge.gimbalYawOffsetDeg : 0
                cameraPitchDeg: settingsBridge ? settingsBridge.cameraPitchDeg : -8
                fovHDeg:       settingsBridge ? settingsBridge.cameraFovHDeg : 62
                manualRangeM:  settingsBridge ? settingsBridge.manualRangeM : 500
                mapZoom:       settingsBridge ? settingsBridge.mapZoom : 1.0
                mapRotationDeg: settingsBridge ? settingsBridge.mapRotationDeg : 0
                targetValid:   geoBridge ? geoBridge.targetValid : false
                targetX:       geoBridge ? geoBridge.targetX : 0.5
                targetY:       geoBridge ? geoBridge.targetY : 0.5
                targetBearingDeg: geoBridge ? geoBridge.targetBearingDeg : 0
                targetRangeM:  geoBridge ? geoBridge.targetRangeM : 0
                trailJson:     geoBridge ? geoBridge.trailJson : "[]"
                onCollapseToggled: root._mapCollapsed = !root._mapCollapsed
                onExpandToggled: {
                    root._mapExpanded = !root._mapExpanded
                    if (root._mapExpanded) root._mapCollapsed = false
                }
            }
        }
    }

    // ── Expanded Map — right 30% workspace overlay (z=12) ────────────
    MapPanel {
        id: expandedMapPanel
        anchors.top: topBar.bottom
        anchors.topMargin: 12
        anchors.right: parent.right
        anchors.rightMargin: 16
        anchors.bottom: bottomDrawer.top
        anchors.bottomMargin: 8
        width: Math.round(root.width * 0.30)
        z: 12
        opacity: root._mapExpanded ? 1 : 0
        visible: opacity > 0.01
        enabled: root._mapExpanded
        Behavior on opacity { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }
        Behavior on width { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
        panelMaxH: height - 38
        collapsed: false
        expanded: true
        isRunning: root.isRunning
        trackingState: root.trackingState
        targetId: root.targetId
        confidence: root.confidence
        fps: root.fps
        latencyMs: root.latencyMs
        activeTargets: root.activeTargets
        idSwitches: root.idSwitches
        falseLockRisk: root.falseLockRisk
        deviceLat: settingsBridge ? settingsBridge.deviceLat : 59.9386
        deviceLon: settingsBridge ? settingsBridge.deviceLon : 30.3141
        deviceAltM: settingsBridge ? settingsBridge.deviceAltM : 25
        headingDeg: settingsBridge ? settingsBridge.headingDeg : 87
        yawOffsetDeg: settingsBridge ? settingsBridge.gimbalYawOffsetDeg : 0
        cameraPitchDeg: settingsBridge ? settingsBridge.cameraPitchDeg : -8
        fovHDeg: settingsBridge ? settingsBridge.cameraFovHDeg : 62
        manualRangeM: settingsBridge ? settingsBridge.manualRangeM : 500
        mapZoom: settingsBridge ? settingsBridge.mapZoom : 1.0
        mapRotationDeg: settingsBridge ? settingsBridge.mapRotationDeg : 0
        targetValid: geoBridge ? geoBridge.targetValid : false
        targetX: geoBridge ? geoBridge.targetX : 0.5
        targetY: geoBridge ? geoBridge.targetY : 0.5
        targetBearingDeg: geoBridge ? geoBridge.targetBearingDeg : 0
        targetRangeM: geoBridge ? geoBridge.targetRangeM : 0
        trailJson: geoBridge ? geoBridge.trailJson : "[]"
        onCollapseToggled: root._mapExpanded = false
        onExpandToggled: root._mapExpanded = false
    }

    // ── BottomDrawer — full-width at bottom (z=8) ───────────────────
    BottomDrawer {
        id: bottomDrawer
        anchors.left:   parent.left
        anchors.right:  parent.right
        anchors.bottom: parent.bottom
        z: 8
        fps:           root.fps
        trackingState: root.trackingState
        targetLifecycle: root.targetLifecycle
        activeSource:   root.activeSource
        targetId:      root.targetId
        lockScore:      root.lockScore
        reliability:    root.targetReliability
        isRunning:     root.isRunning
        confidence:    root.confidence
        latencyMs:     root.latencyMs
        falseLockRisk: root.falseLockRisk
        idSwitches:    root.idSwitches
        activeTargets: root.activeTargets
        isRecording:   root.isRecording
        lastAction:    root.lastAction
    }

    // ── Source dialog dim backdrop (z=94) ────────────────────────────
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.55)
        visible: root.showSourceDialog
        z: 94
        MouseArea { anchors.fill: parent; onClicked: root.showSourceDialog = false }
    }

    // ── SourceDialog modal (z=95) ────────────────────────────────────
    SourceDialog {
        id: sourceDialog
        anchors.centerIn: parent
        visible: root.showSourceDialog
        z: 95
        onSourceSelected: function(sourceType, sourceValue, cameraIndex) {
            if (bridge && bridge.isRunning) bridge.stopTracking()
            bridge.startTracking(sourceType, sourceValue, cameraIndex)
            root.showSourceDialog = false
            bottomDrawer.addLog("ok", "Трекинг запущен")
        }
        onCancelled: root.showSourceDialog = false
    }

    // ── DTS Overlay (z=100) ──────────────────────────────────────────
    TargetLabOverlay {
        anchors.fill: parent
        visible: root.targetLabOpen
        z: 100
        onClosed: root.targetLabOpen = false
        Keys.onEscapePressed: root.targetLabOpen = false
    }

    DtsOverlay {
        anchors.fill: parent
        visible: root.dtsOpen
        z: 100
        onClosed: root.dtsOpen = false
    }

    // ── Expert Overlay (z=100) ───────────────────────────────────────
    ExpertOverlay {
        anchors.fill: parent
        visible: root.expertOpen
        z: 100
        onClosed: root.expertOpen = false
        Keys.onEscapePressed: root.expertOpen = false
    }

    // ── GT Assist Overlay (z=100) ──────────────────────────────────────
    GtAssistOverlay {
        anchors.fill: parent
        visible: root.gtAssistOpen
        z: 100
        onClosed: root.gtAssistOpen = false
        Keys.onEscapePressed: root.gtAssistOpen = false
    }

    // ── Calibration Overlay (z=100) ──────────────────────────────────
    CalibOverlay {
        anchors.fill: parent
        visible: root.calibOpen
        z: 100
        onClosed: root.calibOpen = false
        Keys.onEscapePressed: root.calibOpen = false
    }

    // ── Diagnostics Overlay (z=100) ──────────────────────────────────
    DiagOverlay {
        anchors.fill: parent
        visible: root.diagOpen
        z: 100
        onClosed: root.diagOpen = false
        Keys.onEscapePressed: root.diagOpen = false
    }

    // ── Settings Overlay (z=100) ─────────────────────────────────────
    SettingsOverlay {
        anchors.fill: parent
        visible: root.settingsOpen
        z: 100
        onClosed: root.settingsOpen = false
        Keys.onEscapePressed: root.settingsOpen = false
    }

    // ── About Overlay (z=100) ────────────────────────────────────────
    AboutOverlay {
        anchors.fill: parent
        visible: root.aboutOpen
        z: 100
        onClosed: root.aboutOpen = false
        Keys.onEscapePressed: root.aboutOpen = false
    }
}
