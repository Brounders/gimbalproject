import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: Qt.rgba(0.08, 0.13, 0.22, 0.48)
    radius: 10
    border.color: Qt.rgba(1,1,1,0.26); border.width: 1
    clip: true

    property real panelMaxH: 9999
    height: collapsed ? 38 : expanded ? implicitHeight : Math.min(248, 38 + panelMaxH)
    implicitHeight: expanded ? 520 : 248
    Behavior on height { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
    Behavior on opacity { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

    property bool   collapsed:     false
    property bool   expanded:      false
    property bool   isRunning:     false
    property string trackingState: "SEARCH"
    property int    targetId:      0
    property real   confidence:    0.0
    property int    fps:           0
    property int    latencyMs:     0
    property int    activeTargets: 0
    property int    idSwitches:    0
    property real   falseLockRisk: 0.0
    property real   deviceLat:     59.9386
    property real   deviceLon:     30.3141
    property real   deviceAltM:    25.0
    property real   headingDeg:    87.0
    property real   yawOffsetDeg:  0.0
    property real   cameraPitchDeg:-8.0
    property real   fovHDeg:       62.0
    property real   manualRangeM:  500.0
    property real   mapZoom:       1.0
    property real   mapRotationDeg:0.0
    property bool   targetValid:   false
    property real   targetX:       0.5
    property real   targetY:       0.5
    property real   targetBearingDeg: headingDeg + yawOffsetDeg
    property real   targetRangeM:  manualRangeM
    property string trailJson:     "[]"
    property real   course:        headingDeg + yawOffsetDeg       // degrees, 0=N
    property real   speed:         0.0     // m/s
    property real   lat:           deviceLat
    property real   lon:           deviceLon

    signal collapseToggled()
    signal expandToggled()

    property real _viewZoom: Math.max(0.5, mapZoom)
    property real _viewRotation: mapRotationDeg
    property var  _trail: []

    onMapZoomChanged: { _viewZoom = Math.max(0.5, mapZoom); mapCanvas.requestPaint() }
    onMapRotationDegChanged: { _viewRotation = mapRotationDeg; mapCanvas.requestPaint() }
    onDeviceLatChanged: mapCanvas.requestPaint()
    onDeviceLonChanged: mapCanvas.requestPaint()
    onHeadingDegChanged: mapCanvas.requestPaint()
    onYawOffsetDegChanged: mapCanvas.requestPaint()
    onManualRangeMChanged: mapCanvas.requestPaint()
    onExpandedChanged: mapCanvas.requestPaint()
    onTargetXChanged: mapCanvas.requestPaint()
    onTargetYChanged: mapCanvas.requestPaint()
    onTargetBearingDegChanged: mapCanvas.requestPaint()
    onTargetValidChanged: mapCanvas.requestPaint()
    onTrailJsonChanged: {
        try { _trail = JSON.parse(trailJson) } catch (e) { _trail = [] }
        mapCanvas.requestPaint()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── Header ───────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true; height: 38; color: "transparent"
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Qt.rgba(1,1,1,0.07) }

            Text {
                anchors.left: parent.left; anchors.leftMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                text: "КАРТА"; color: "#5A7080"
                font.pixelSize: 9; font.family: "Menlo"
                font.letterSpacing: 2; font.weight: Font.DemiBold
            }

            Text {
                anchors.centerIn: parent
                text: root.deviceLat.toFixed(4) + "°  " + root.deviceLon.toFixed(4) + "°"
                color: "#3A5060"; font.pixelSize: 7; font.family: "Menlo"
                font.letterSpacing: 0.3
            }

            Rectangle {
                id: mapColBtn
                anchors.right: parent.right; anchors.rightMargin: 42
                anchors.verticalCenter: parent.verticalCenter
                width: 20; height: 20; radius: 4
                color: mapColMa.containsMouse ? Qt.rgba(1,1,1,0.08) : "transparent"
                border.color: Qt.rgba(1,1,1,0.10); border.width: 1
                Text { anchors.centerIn: parent; text: root.collapsed ? "+" : "−"
                       color: "#5A7080"; font.pixelSize: 12; font.family: "Menlo" }
                MouseArea { id: mapColMa; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor; onClicked: root.collapseToggled() }
            }

            Rectangle {
                id: mapExpandBtn
                anchors.right: parent.right; anchors.rightMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                width: 20; height: 20; radius: 4
                color: mapExpandMa.containsMouse ? Qt.rgba(1,1,1,0.08) : "transparent"
                border.color: Qt.rgba(1,1,1,0.10); border.width: 1
                Text { anchors.centerIn: parent; text: root.expanded ? "›" : "‹"
                       color: "#5A7080"; font.pixelSize: 12; font.family: "Menlo" }
                MouseArea { id: mapExpandMa; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor; onClicked: root.expandToggled() }
            }
        }

        // ── Expanded summary — target + telemetry ───────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: root.expanded ? 152 : 0
            visible: root.expanded && !root.collapsed
            opacity: root.expanded && !root.collapsed ? 1 : 0
            color: Qt.rgba(0.03, 0.06, 0.09, 0.42)
            clip: true
            Behavior on Layout.preferredHeight { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
            Behavior on opacity { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Qt.rgba(1,1,1,0.07) }

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 7
                    color: Qt.rgba(1,1,1,0.035)
                    border.color: Qt.rgba(1,1,1,0.10)
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "ЦЕЛЬ"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.8 }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text {
                                text: root.targetId > 0 ? "T-" + (root.targetId < 10 ? "0" : "") + root.targetId : "T-—"
                                color: "#E6ECF3"
                                font.pixelSize: 18
                                font.family: "Menlo"
                            }
                            Item { Layout.fillWidth: true }
                            Rectangle {
                                width: stateLbl.implicitWidth + 14
                                height: 22
                                radius: 4
                                color: Qt.rgba(0,0,0,0.24)
                                border.color: root.trackingState === "LOCK" ? "#52D273" : root.trackingState === "LOST" ? "#E26B6B" : "#E8B547"
                                border.width: 1
                                Text {
                                    id: stateLbl
                                    anchors.centerIn: parent
                                    text: root.trackingState
                                    color: parent.border.color
                                    font.pixelSize: 9
                                    font.family: "Menlo"
                                }
                            }
                        }

                        MetricLine { label: "CONF"; value: Math.round(root.confidence * 100) + "%" }
                        MetricLine { label: "RANGE"; value: root.targetValid ? Math.round(root.targetRangeM) + " м" : "—" }
                        MetricLine { label: "BEARING"; value: root.targetValid ? Math.round(root.targetBearingDeg) + "°" : "—" }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 7
                    color: Qt.rgba(1,1,1,0.035)
                    border.color: Qt.rgba(1,1,1,0.10)
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "ТЕЛЕМЕТРИЯ"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.8 }
                        MetricLine { label: "FPS"; value: root.fps > 0 ? root.fps : "—" }
                        MetricLine { label: "LATENCY"; value: root.latencyMs > 0 ? root.latencyMs + " мс" : "—" }
                        MetricLine { label: "TARGETS"; value: root.activeTargets }
                        MetricLine { label: "FALSE LOCK"; value: Math.round(root.falseLockRisk * 100) + "%" }
                        MetricLine { label: "ID SWITCH"; value: root.idSwitches }
                    }
                }
            }
        }

        // ── Map canvas ───────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 60
            visible: !root.collapsed
            color: "#05090F"
            border.color: Qt.rgba(1,1,1,0.14); border.width: 1
            radius: 4; clip: true

        Canvas {
            id: mapCanvas
            anchors.fill: parent
            anchors.margins: 1

            Component.onCompleted: requestPaint()

            onPaint: {
                var ctx = getContext("2d")
                var W = width, H = height
                ctx.clearRect(0, 0, W, H)
                var CX = W / 2
                var CY = H / 2
                var viewZoom = Math.max(0.45, root._viewZoom)
                var viewRot = -root._viewRotation * Math.PI / 180.0

                // ── Background ────────────────────────────────────
                ctx.fillStyle = "#05090F"
                ctx.fillRect(0, 0, W, H)

                ctx.save()
                ctx.translate(CX, CY)
                ctx.rotate(viewRot)
                ctx.scale(viewZoom, viewZoom)
                ctx.translate(-CX, -CY)

                // ── Terrain blobs (radial gradient patches) ───────
                var blobs = [
                    {x:0.12, y:0.25, r:0.22, a:0.65},
                    {x:0.72, y:0.18, r:0.26, a:0.55},
                    {x:0.50, y:0.72, r:0.28, a:0.60},
                    {x:0.88, y:0.80, r:0.20, a:0.50},
                    {x:0.18, y:0.82, r:0.24, a:0.55},
                    {x:0.40, y:0.35, r:0.18, a:0.45},
                ]
                blobs.forEach(function(b) {
                    var grd = ctx.createRadialGradient(b.x*W, b.y*H, 0, b.x*W, b.y*H, b.r*W)
                    grd.addColorStop(0, "rgba(18,36,52," + b.a + ")")
                    grd.addColorStop(0.6, "rgba(10,20,32,0.3)")
                    grd.addColorStop(1,   "rgba(5,9,15,0)")
                    ctx.fillStyle = grd
                    ctx.beginPath(); ctx.arc(b.x*W, b.y*H, b.r*W, 0, Math.PI*2); ctx.fill()
                })

                // ── Coordinate grid ───────────────────────────────
                ctx.strokeStyle = "rgba(24,42,58,0.80)"
                ctx.lineWidth = 0.5
                var gs = Math.floor(W / 8)
                for (var gx = gs; gx < W; gx += gs) {
                    ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, H); ctx.stroke()
                }
                var gy2 = Math.floor(H / 6)
                for (var gy = gy2; gy < H; gy += gy2) {
                    ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(W, gy); ctx.stroke()
                }

                // ── "River" / road features ───────────────────────
                ctx.strokeStyle = "rgba(14,28,44,0.95)"
                ctx.lineWidth = 2.5
                ctx.beginPath()
                ctx.moveTo(0, H*0.44)
                ctx.bezierCurveTo(W*0.22, H*0.40, W*0.48, H*0.55, W*0.75, H*0.47)
                ctx.bezierCurveTo(W*0.88, H*0.44, W*0.95, H*0.42, W, H*0.40)
                ctx.stroke()

                ctx.strokeStyle = "rgba(12,24,38,0.90)"
                ctx.lineWidth = 1.5
                ctx.beginPath()
                ctx.moveTo(W*0.33, 0)
                ctx.bezierCurveTo(W*0.36, H*0.28, W*0.40, H*0.50, W*0.44, H)
                ctx.stroke()

                ctx.strokeStyle = "rgba(14,28,42,0.75)"
                ctx.lineWidth = 1
                ctx.beginPath()
                ctx.moveTo(W*0.60, 0)
                ctx.bezierCurveTo(W*0.62, H*0.15, W*0.58, H*0.30, W*0.65, H*0.55)
                ctx.bezierCurveTo(W*0.70, H*0.72, W*0.68, H*0.85, W*0.72, H)
                ctx.stroke()

                // ── Trail ─────────────────────────────────────────
                var trail = root._trail
                if (trail.length > 0) {
                    // Gradient trail segments
                    for (var ti = 1; ti < trail.length; ti++) {
                        var alpha = 0.15 + (ti / trail.length) * 0.55
                        ctx.strokeStyle = "rgba(82,210,115," + alpha + ")"
                        ctx.lineWidth = 1.8
                        ctx.beginPath()
                        ctx.moveTo(trail[ti-1].x * W, trail[ti-1].y * H)
                        ctx.lineTo(trail[ti].x * W,   trail[ti].y * H)
                        ctx.stroke()
                    }
                    // Connect last trail point → current
                    ctx.strokeStyle = "rgba(82,210,115,0.75)"
                    ctx.lineWidth = 1.8
                    ctx.beginPath()
                    ctx.moveTo(trail[trail.length-1].x * W, trail[trail.length-1].y * H)
                    ctx.lineTo(root._ox * W, root._oy * H)
                    ctx.stroke()

                    // Trail dots
                    for (var td = 0; td < trail.length; td++) {
                        var da = 0.12 + (td / trail.length) * 0.55
                        ctx.fillStyle = "rgba(82,210,115," + da + ")"
                        ctx.beginPath()
                        ctx.arc(trail[td].x*W, trail[td].y*H, 2, 0, Math.PI*2)
                        ctx.fill()
                    }
                }

                // ── Predicted trajectory ──────────────────────────
                if (root.targetValid) {
                    var rad = root.targetBearingDeg * Math.PI / 180.0
                    var predDist = root.speed * 0.020   // normalized canvas distance
                    var predSteps = 12

                    ctx.save()
                    ctx.setLineDash([4, 5])
                    ctx.strokeStyle = "rgba(232,181,71,0.55)"
                    ctx.lineWidth = 1.3
                    ctx.beginPath()
                    ctx.moveTo(root.targetX * W, root.targetY * H)
                    for (var ps = 1; ps <= predSteps; ps++) {
                        var frac = ps / predSteps
                        var px = root.targetX + Math.sin(rad) * predDist * frac
                        var py = root.targetY - Math.cos(rad) * predDist * frac
                        ctx.lineTo(px * W, py * H)
                    }
                    ctx.stroke()
                    ctx.setLineDash([])
                    ctx.restore()

                    // Prediction endpoint
                    var epx = (root.targetX + Math.sin(rad) * predDist) * W
                    var epy = (root.targetY - Math.cos(rad) * predDist) * H
                    ctx.fillStyle = "rgba(232,181,71,0.35)"
                    ctx.beginPath(); ctx.arc(epx, epy, 4, 0, Math.PI*2); ctx.fill()
                    ctx.strokeStyle = "rgba(232,181,71,0.55)"
                    ctx.lineWidth = 0.8
                    ctx.beginPath(); ctx.arc(epx, epy, 7, 0, Math.PI*2); ctx.stroke()
                }

                // ── Device and field of view ──────────────────────
                var devX = W / 2
                var devY = H / 2
                var head = root.course * Math.PI / 180.0
                var coneLen = Math.min(W, H) * 0.28
                var halfFov = root.fovHDeg * Math.PI / 360.0

                ctx.fillStyle = "rgba(111,142,170,0.10)"
                ctx.beginPath()
                ctx.moveTo(devX, devY)
                ctx.lineTo(devX + Math.sin(head - halfFov) * coneLen, devY - Math.cos(head - halfFov) * coneLen)
                ctx.lineTo(devX + Math.sin(head + halfFov) * coneLen, devY - Math.cos(head + halfFov) * coneLen)
                ctx.closePath()
                ctx.fill()

                ctx.strokeStyle = "rgba(143,164,184,0.42)"
                ctx.lineWidth = 1.2
                ctx.beginPath()
                ctx.moveTo(devX, devY)
                ctx.lineTo(devX + Math.sin(head) * coneLen, devY - Math.cos(head) * coneLen)
                ctx.stroke()

                ctx.fillStyle = "#8FA4B8"
                ctx.beginPath(); ctx.arc(devX, devY, 4.5, 0, Math.PI*2); ctx.fill()
                ctx.strokeStyle = "rgba(143,164,184,0.50)"
                ctx.beginPath(); ctx.arc(devX, devY, 11, 0, Math.PI*2); ctx.stroke()

                // ── Object ────────────────────────────────────────
                var ox = root.targetX * W
                var oy = root.targetY * H
                var isLock  = root.trackingState === "LOCK"
                var isLost  = root.trackingState === "LOST"
                var objHex  = isLock ? "#52D273" : isLost ? "#E26B6B" : "#E8B547"
                var objRgba = isLock ? [82,210,115] : isLost ? [226,107,107] : [232,181,71]

                if (root.targetValid) {
                    // Outer halo
                    ctx.strokeStyle = "rgba(" + objRgba[0] + "," + objRgba[1] + "," + objRgba[2] + ",0.18)"
                    ctx.lineWidth = 1
                    ctx.beginPath(); ctx.arc(ox, oy, 16, 0, Math.PI*2); ctx.stroke()

                    // Middle ring
                    ctx.strokeStyle = "rgba(" + objRgba[0] + "," + objRgba[1] + "," + objRgba[2] + ",0.45)"
                    ctx.lineWidth = 1.2
                    ctx.beginPath(); ctx.arc(ox, oy, 9, 0, Math.PI*2); ctx.stroke()

                    // Core fill
                    ctx.fillStyle = objHex
                    ctx.beginPath(); ctx.arc(ox, oy, 4, 0, Math.PI*2); ctx.fill()
                }

                // Direction arrow
                if (root.targetValid) {
                    var rad2   = root.targetBearingDeg * Math.PI / 180.0
                    var aLen   = 20
                    var ax     = ox + Math.sin(rad2) * aLen
                    var ay     = oy - Math.cos(rad2) * aLen
                    ctx.strokeStyle = "rgba(255,255,255,0.55)"
                    ctx.lineWidth = 1.5
                    ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(ax, ay); ctx.stroke()
                    // Arrowhead
                    var ha = 0.45, hl = 6
                    ctx.beginPath()
                    ctx.moveTo(ax, ay)
                    ctx.lineTo(ax - hl*Math.sin(rad2+ha), ay + hl*Math.cos(rad2+ha))
                    ctx.moveTo(ax, ay)
                    ctx.lineTo(ax - hl*Math.sin(rad2-ha), ay + hl*Math.cos(rad2-ha))
                    ctx.stroke()
                }

                // ── Legend ────────────────────────────────────────
                // Trail label
                ctx.fillStyle = "rgba(82,210,115,0.55)"
                ctx.font = "6px monospace"
                ctx.fillText("ТРЕК", 6, H - 22)

                // Prediction label
                ctx.fillStyle = "rgba(232,181,71,0.55)"
                ctx.fillText("ПРОГНОЗ", 6, H - 13)

                // ── Scale bar ─────────────────────────────────────
                ctx.fillStyle = "rgba(58,80,96,0.70)"
                ctx.fillRect(W - 46, H - 10, 38, 1.5)
                ctx.font = "6px monospace"
                ctx.fillText("500 м", W - 46, H - 3)

                // ── N arrow ───────────────────────────────────────
                ctx.fillStyle = "rgba(90,112,128,0.65)"
                ctx.font = "7px monospace"
                ctx.fillText("N", W - 14, 11)
                ctx.strokeStyle = "rgba(90,112,128,0.45)"
                ctx.lineWidth = 0.8
                ctx.beginPath(); ctx.moveTo(W - 10, 13); ctx.lineTo(W - 10, 20); ctx.stroke()

                // ── Corner coords ─────────────────────────────────
                ctx.restore()
                ctx.fillStyle = "rgba(42,64,80,0.60)"
                ctx.font = "6px monospace"
                ctx.fillText(root.deviceLat.toFixed(4) + " LAT", 4, 10)
                ctx.fillText(root.deviceLon.toFixed(4) + " LON", 4, H - 3)
                ctx.fillText("Z " + root._viewZoom.toFixed(1) + "  R " + Math.round(root._viewRotation) + "°", W - 76, 10)
            }
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            onWheel: {
                if (wheel.angleDelta.y > 0) root._viewZoom = Math.min(6.0, root._viewZoom * 1.12)
                else root._viewZoom = Math.max(0.45, root._viewZoom / 1.12)
                mapCanvas.requestPaint()
            }
        }

        Row {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 8
            spacing: 5
            Repeater {
                model: [
                    {t:"+", a:"zin"},
                    {t:"−", a:"zout"},
                    {t:"↺", a:"rl"},
                    {t:"↻", a:"rr"},
                ]
                Rectangle {
                    required property var modelData
                    width: 24; height: 22; radius: 4
                    color: ctrlMa.containsMouse ? Qt.rgba(1,1,1,0.12) : Qt.rgba(0,0,0,0.35)
                    border.color: Qt.rgba(1,1,1,0.12); border.width: 1
                    Text { anchors.centerIn: parent; text: modelData.t; color: "#8FA4B8"; font.pixelSize: 11; font.family: "Menlo" }
                    MouseArea {
                        id: ctrlMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (modelData.a === "zin") root._viewZoom = Math.min(6.0, root._viewZoom * 1.18)
                            else if (modelData.a === "zout") root._viewZoom = Math.max(0.45, root._viewZoom / 1.18)
                            else if (modelData.a === "rl") root._viewRotation -= 10
                            else if (modelData.a === "rr") root._viewRotation += 10
                            mapCanvas.requestPaint()
                        }
                    }
                }
            }
        }
        } // Rectangle border wrapper
    }

    component MetricLine: RowLayout {
        required property string label
        required property var value
        Layout.fillWidth: true
        height: 16
        spacing: 6

        Text {
            Layout.fillWidth: true
            text: label
            color: "#3A5060"
            font.pixelSize: 9
            font.family: "Menlo"
            font.letterSpacing: 0.8
            elide: Text.ElideRight
        }
        Text {
            text: value
            color: "#A9B5C2"
            font.pixelSize: 10
            font.family: "Menlo"
            horizontalAlignment: Text.AlignRight
        }
    }
}
