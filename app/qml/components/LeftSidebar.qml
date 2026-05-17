import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: _manualOpen ? 192 : 72
    Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
    radius: 10
    color: Qt.rgba(0.08, 0.13, 0.22, 0.48)
    border.color: Qt.rgba(1,1,1,0.26); border.width: 1

    // ── Public props ──────────────────────────────────────────────────
    property bool   isRunning:     false
    property string trackingState: "SEARCH"
    property real   zoomLevel:     1.0
    property bool   isRecording:   false
    property string currentSource: ""
    property string targetLifecycle: "OFFLINE"
    property string activeSource: "—"
    property real   lockScore: 0.0
    property real   reliability: 0.0

    // ── Internal state ────────────────────────────────────────────────
    property bool   _manualOpen:   false
    property int    _manSpeed:     1
    property bool   _stabOn:       true
    property int    _recSecs:      0

    Timer {
        interval: 1000; running: root.isRecording; repeat: true
        onTriggered: root._recSecs++
        onRunningChanged: if (!running) root._recSecs = 0
    }

    function fmtRec(s) {
        var m = Math.floor(s / 60); var sec = s % 60
        return (m < 10 ? "0" : "") + m + ":" + (sec < 10 ? "0" : "") + sec
    }

    function canAcceptTarget() {
        return root.isRunning && ["CANDIDATE", "VERIFYING", "TRACKING", "WEAK_TRACK", "LOST"].indexOf(root.targetLifecycle) >= 0
    }

    // ── Signals ───────────────────────────────────────────────────────
    signal startClicked()
    signal stopClicked()
    signal recToggled()
    signal lockClicked()
    signal nextTargetClicked()
    signal markBBoxClicked()

    implicitHeight: sideCol.implicitHeight + 20

    ColumnLayout {
        id: sideCol
        anchors { top: parent.top; left: parent.left; right: parent.right; margins: 10; topMargin: 10 }
        spacing: 5

        // ── START / STOP ──────────────────────────────────────────────
        Rectangle {
            id: startBtn
            Layout.fillWidth: true
            height: 54; radius: 7
            property color accent: root.isRunning ? "#E26B6B" : "#52D273"
            color: stMa.pressed       ? Qt.rgba(accent.r, accent.g, accent.b, 0.25)
                 : stMa.containsMouse ? Qt.rgba(accent.r, accent.g, accent.b, 0.12)
                 : Qt.rgba(accent.r, accent.g, accent.b, 0.07)
            border.color: Qt.rgba(accent.r, accent.g, accent.b, 0.40); border.width: 1

            Column { anchors.centerIn: parent; spacing: 3
                Canvas {
                    id: startIcon; width: 20; height: 20; anchors.horizontalCenter: parent.horizontalCenter
                    property string iconColor: root.isRunning ? "#E26B6B" : "#52D273"
                    onIconColorChanged: requestPaint(); Component.onCompleted: requestPaint()
                    onPaint: {
                        var ctx = getContext("2d"); ctx.clearRect(0, 0, 20, 20)
                        ctx.fillStyle = iconColor
                        if (root.isRunning) { ctx.fillRect(4,4,5,12); ctx.fillRect(11,4,5,12) }
                        else { ctx.beginPath(); ctx.moveTo(5,2); ctx.lineTo(17,10); ctx.lineTo(5,18); ctx.closePath(); ctx.fill() }
                    }
                }
                Text { anchors.horizontalCenter: parent.horizontalCenter
                       text: root.isRunning ? "СТОП" : "СТАРТ"; color: startBtn.accent
                       font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 1.5; font.weight: Font.Bold }
            }
            MouseArea { id: stMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: root.isRunning ? root.stopClicked() : root.startClicked() }
        }

        // ── SEPARATOR ─────────────────────────────────────────────────
        Rectangle { Layout.fillWidth: true; height: 1; color: "#1C2A38" }

        // ── COMPACT ROW [LOCK | REC | NT] — visible when manual open ──
        Row {
            Layout.alignment: Qt.AlignHCenter
            visible: root._manualOpen
            spacing: 5

            // LOCK compact
            Rectangle {
                width: 56; height: 48; radius: 7
                property bool ena: root.canAcceptTarget()
                opacity: ena ? 1.0 : 0.28
                color: cLkMa.pressed ? Qt.rgba(0.196,0.784,0.447,0.22)
                     : cLkMa.containsMouse ? Qt.rgba(0.196,0.784,0.447,0.09) : "transparent"
                border.color: cLkMa.containsMouse ? Qt.rgba(0.196,0.784,0.447,0.45) : "#1C2A38"; border.width: 1
                Column { anchors.centerIn: parent; spacing: 3
                    Canvas { width: 18; height: 18; anchors.horizontalCenter: parent.horizontalCenter
                        Component.onCompleted: requestPaint()
                        onPaint: {
                            var ctx = getContext("2d"); ctx.clearRect(0,0,18,18)
                            ctx.strokeStyle = "#52D273"; ctx.lineWidth = 1.4
                            ctx.beginPath(); ctx.arc(9,7,4,Math.PI,0,true); ctx.stroke()
                            ctx.fillStyle = "#52D273"
                            root._roundRect(ctx,3,8,12,8,2); ctx.fill()
                            ctx.fillStyle = "#0C1520"
                            ctx.beginPath(); ctx.arc(9,12,1.8,0,Math.PI*2); ctx.fill()
                        }
                    }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: "ПРИН"; color: "#52D273"
                           font.pixelSize: 7; font.family: "Menlo"; font.letterSpacing: 1 }
                }
                MouseArea { id: cLkMa; anchors.fill: parent; hoverEnabled: true
                            cursorShape: parent.ena ? Qt.PointingHandCursor : Qt.ArrowCursor
                            onClicked: if (parent.ena) root.lockClicked() }
            }

            // REC compact
            Rectangle {
                width: 56; height: 48; radius: 7
                property color ac: root.isRecording ? "#E26B6B" : "#5A6E7E"
                color: cRcMa.pressed ? Qt.rgba(ac.r,ac.g,ac.b,0.22)
                     : cRcMa.containsMouse ? Qt.rgba(ac.r,ac.g,ac.b,0.09) : "transparent"
                border.color: cRcMa.containsMouse ? Qt.rgba(ac.r,ac.g,ac.b,0.45) : "#1C2A38"; border.width: 1
                Column { anchors.centerIn: parent; spacing: 3
                    Row { anchors.horizontalCenter: parent.horizontalCenter; spacing: 3
                        Rectangle { width: 6; height: 6; radius: 3; anchors.verticalCenter: parent.verticalCenter
                                    color: root.isRecording ? "#E26B6B" : "#3A4E5E"
                            SequentialAnimation on opacity { running: root.isRecording; loops: Animation.Infinite
                                NumberAnimation { to: 0.2; duration: 600 }
                                NumberAnimation { to: 1.0; duration: 600 }
                            }
                        }
                        Text { text: "REC"; color: root.isRecording ? "#E26B6B" : "#4A5E6E"
                               font.pixelSize: 7; font.family: "Menlo"; font.letterSpacing: 1
                               anchors.verticalCenter: parent.verticalCenter }
                    }
                    Text { anchors.horizontalCenter: parent.horizontalCenter
                           text: root.isRecording ? root.fmtRec(root._recSecs) : "—"
                           color: root.isRecording ? "#E26B6B" : "#3A4E5E"
                           font.pixelSize: 7; font.family: "Menlo" }
                }
                MouseArea { id: cRcMa; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor; onClicked: root.recToggled() }
            }

            // NT compact
            Rectangle {
                width: 56; height: 48; radius: 7
                opacity: root.isRunning ? 1.0 : 0.28
                color: cNtMa.pressed ? Qt.rgba(0.561,0.643,0.722,0.22)
                     : cNtMa.containsMouse ? Qt.rgba(0.561,0.643,0.722,0.09) : "transparent"
                border.color: cNtMa.containsMouse ? Qt.rgba(0.561,0.643,0.722,0.45) : "#1C2A38"; border.width: 1
                Column { anchors.centerIn: parent; spacing: 3
                    Canvas { width: 18; height: 18; anchors.horizontalCenter: parent.horizontalCenter
                        Component.onCompleted: requestPaint()
                        onPaint: {
                            var ctx = getContext("2d"); ctx.clearRect(0,0,18,18)
                            ctx.strokeStyle = "#8FA4B8"; ctx.lineWidth = 1.2
                            var cx=9,cy=9,r=4,arm=4,gap=2
                            ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2); ctx.stroke()
                            ctx.beginPath(); ctx.moveTo(cx-arm-gap,cy); ctx.lineTo(cx-gap,cy); ctx.stroke()
                            ctx.beginPath(); ctx.moveTo(cx+gap,cy); ctx.lineTo(cx+arm+gap,cy); ctx.stroke()
                            ctx.beginPath(); ctx.moveTo(cx,cy-arm-gap); ctx.lineTo(cx,cy-gap); ctx.stroke()
                            ctx.beginPath(); ctx.moveTo(cx,cy+gap); ctx.lineTo(cx,cy+arm+gap); ctx.stroke()
                        }
                    }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: "СЛЕД"; color: "#8FA4B8"
                           font.pixelSize: 7; font.family: "Menlo"; font.letterSpacing: 1 }
                }
                MouseArea { id: cNtMa; anchors.fill: parent; hoverEnabled: true
                            cursorShape: root.isRunning ? Qt.PointingHandCursor : Qt.ArrowCursor
                            onClicked: if (root.isRunning) root.nextTargetClicked() }
            }
        }

        // ── ACCEPT TARGET (normal mode only) ───────────────────────────
        SbButton {
            visible: !root._manualOpen
            Layout.fillWidth: true; label: "ПРИН"; accent: "#52D273"
            enabled: root.canAcceptTarget()
            onClicked: root.lockClicked()
            iconPaint: function(ctx, w, h, col) {
                ctx.strokeStyle = col; ctx.lineWidth = 1.6
                ctx.beginPath(); ctx.arc(w/2, h/2-1, 5, Math.PI, 0, true); ctx.stroke()
                ctx.fillStyle = col
                _roundRect(ctx, w/2-6, h/2+1, 12, 9, 2); ctx.fill()
                ctx.fillStyle = "#0C1520"
                ctx.beginPath(); ctx.arc(w/2, h/2+5, 2, 0, Math.PI*2); ctx.fill()
            }
        }

        // ── REC (normal mode only) ────────────────────────────────────
        Rectangle {
            visible: !root._manualOpen
            Layout.fillWidth: true
            height: 52; radius: 7
            property color accent: root.isRecording ? "#E26B6B" : "#5A6E7E"
            color: recMa.pressed       ? Qt.rgba(accent.r,accent.g,accent.b,0.25)
                 : recMa.containsMouse ? Qt.rgba(accent.r,accent.g,accent.b,0.10)
                 : Qt.rgba(accent.r,accent.g,accent.b,0.06)
            border.color: Qt.rgba(accent.r,accent.g,accent.b,0.35); border.width: 1
            Column { anchors.centerIn: parent; spacing: 3
                Row { anchors.horizontalCenter: parent.horizontalCenter; spacing: 4
                    Rectangle { width: 7; height: 7; radius: 3.5; anchors.verticalCenter: parent.verticalCenter
                                color: root.isRecording ? "#E26B6B" : "#3A4E5E"
                        SequentialAnimation on opacity { running: root.isRecording; loops: Animation.Infinite
                            NumberAnimation { to: 0.2; duration: 600 }
                            NumberAnimation { to: 1.0; duration: 600 }
                        }
                        opacity: 1
                    }
                    Text { text: "REC"; color: root.isRecording ? "#E26B6B" : "#4A5E6E"
                           font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 1.5; font.weight: Font.Bold
                           anchors.verticalCenter: parent.verticalCenter }
                }
                Text { anchors.horizontalCenter: parent.horizontalCenter
                       text: root.isRecording ? root.fmtRec(root._recSecs) : "--:--"
                       color: root.isRecording ? "#E26B6B" : "#3A4E5E"
                       font.pixelSize: 8; font.family: "Menlo"
                       opacity: root.isRecording ? 1.0 : 0.6 }
            }
            MouseArea { id: recMa; anchors.fill: parent; hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor; onClicked: root.recToggled() }
        }

        // ── NEXT TARGET (normal mode only) ────────────────────────────
        SbButton {
            visible: !root._manualOpen
            Layout.fillWidth: true; label: "СЛЕД"; accent: "#8FA4B8"
            enabled: root.isRunning
            onClicked: root.nextTargetClicked()
            iconPaint: function(ctx, w, h, col) {
                ctx.strokeStyle = col; ctx.lineWidth = 1.3
                var cx = w/2, cy = h/2, arm = 5, gap = 2
                ctx.beginPath(); ctx.arc(cx,cy,5,0,Math.PI*2); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(cx-arm-gap,cy); ctx.lineTo(cx-gap,cy); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(cx+gap,cy); ctx.lineTo(cx+arm+gap,cy); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(cx,cy-arm-gap); ctx.lineTo(cx,cy-gap); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(cx,cy+gap); ctx.lineTo(cx,cy+arm+gap); ctx.stroke()
            }
        }

        // ── MANUAL CONTROL BUTTON (УПРВЛ / ЗАКР) ─────────────────────
        SbButton {
            Layout.fillWidth: true
            label: root._manualOpen ? "ЗАКР" : "УПРВЛ"
            accent: root._manualOpen ? "#E8B547" : "#8FA4B8"
            enabled: true
            onClicked: root._manualOpen = !root._manualOpen
            iconPaint: function(ctx, w, h, col) {
                ctx.strokeStyle = col; ctx.lineWidth = 1.4
                var cx = w/2, cy = h/2, a = 4
                ctx.beginPath(); ctx.arc(cx,cy,6,0,Math.PI*2); ctx.stroke()
                ctx.fillStyle = col
                ctx.beginPath(); ctx.arc(cx,cy,2.5,0,Math.PI*2); ctx.fill()
                ctx.beginPath(); ctx.moveTo(cx,cy-10); ctx.lineTo(cx-a,cy-6); ctx.lineTo(cx+a,cy-6); ctx.closePath(); ctx.fill()
                ctx.beginPath(); ctx.moveTo(cx,cy+10); ctx.lineTo(cx-a,cy+6); ctx.lineTo(cx+a,cy+6); ctx.closePath(); ctx.fill()
                ctx.beginPath(); ctx.moveTo(cx-10,cy); ctx.lineTo(cx-6,cy-a); ctx.lineTo(cx-6,cy+a); ctx.closePath(); ctx.fill()
                ctx.beginPath(); ctx.moveTo(cx+10,cy); ctx.lineTo(cx+6,cy-a); ctx.lineTo(cx+6,cy+a); ctx.closePath(); ctx.fill()
            }
        }

        // ── MANUAL CONTROLS (expandable) ──────────────────────────────
        Item {
            Layout.fillWidth: true
            implicitHeight: root._manualOpen ? manualCol.implicitHeight + 8 : 0
            clip: true
            Behavior on implicitHeight { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

            Column {
                id: manualCol
                width: parent.width
                spacing: 6
                topPadding: 4

                Grid {
                    anchors.horizontalCenter: parent.horizontalCenter
                    columns: 3; spacing: 4

                    Item    { width: 38; height: 38 }
                    DpadBtn { arrowChar: "▲" }
                    Item    { width: 38; height: 38 }

                    DpadBtn { arrowChar: "◄" }
                    Rectangle {
                        width: 38; height: 38; radius: 19
                        color: homeMa.pressed ? Qt.rgba(1,1,1,0.18) : homeMa.containsMouse ? Qt.rgba(1,1,1,0.10) : Qt.rgba(1,1,1,0.06)
                        border.color: Qt.rgba(1,1,1,0.22); border.width: 1
                        Text { anchors.centerIn: parent; text: "⌂"; color: "#8FA4B8"; font.pixelSize: 15 }
                        MouseArea { id: homeMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor }
                    }
                    DpadBtn { arrowChar: "►" }

                    Item    { width: 38; height: 38 }
                    DpadBtn { arrowChar: "▼" }
                    Item    { width: 38; height: 38 }
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter; spacing: 4
                    Repeater {
                        model: ["МДЛ", "НРМ", "БСТ"]
                        delegate: Rectangle {
                            required property string modelData
                            required property int index
                            width: 48; height: 22; radius: 4
                            property bool sel: root._manSpeed === index
                            color: sel ? Qt.rgba(0.561,0.643,0.722,0.22) : Qt.rgba(1,1,1,0.04)
                            border.color: sel ? Qt.rgba(0.561,0.643,0.722,0.55) : Qt.rgba(1,1,1,0.12); border.width: 1
                            Text { anchors.centerIn: parent; text: modelData
                                   color: parent.sel ? "#8FA4B8" : "#4A5E6E"
                                   font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 0.5 }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root._manSpeed = index }
                        }
                    }
                }

                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 148; height: 24; radius: 5
                    color: root._stabOn ? Qt.rgba(0.196,0.784,0.447,0.14) : Qt.rgba(1,1,1,0.04)
                    border.color: root._stabOn ? Qt.rgba(0.196,0.784,0.447,0.45) : Qt.rgba(1,1,1,0.12); border.width: 1
                    Row { anchors.centerIn: parent; spacing: 5
                        Rectangle { width: 5; height: 5; radius: 2.5; color: root._stabOn ? "#52D273" : "#4A5E6E"; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: "СТАБИЛИЗАЦИЯ"; color: root._stabOn ? "#52D273" : "#4A5E6E"
                               font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 0.8 }
                    }
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root._stabOn = !root._stabOn }
                }
            }
        }

        // ── SEPARATOR ─────────────────────────────────────────────────
        Rectangle { Layout.fillWidth: true; height: 1; color: "#1C2A38" }

        // ── ZOOM: вертикально (закрытое) / горизонтально (открытое) ──────
        // Вертикальный стек — в закрытом состоянии
        Column {
            visible: !root._manualOpen
            Layout.alignment: Qt.AlignHCenter
            spacing: 3
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: "ZOOM"; color: "#4A5E6E"
                   font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 1.5 }
            ZoomBtn { anchors.horizontalCenter: parent.horizontalCenter; label: "+"
                      onClicked: root.zoomLevel = Math.min(8.0, Math.round((root.zoomLevel+0.2)*10)/10) }
            Text { anchors.horizontalCenter: parent.horizontalCenter
                   text: "×" + root.zoomLevel.toFixed(1); color: "#A9B5C2"
                   font.pixelSize: 11; font.family: "Menlo"; font.weight: Font.Normal }
            ZoomBtn { anchors.horizontalCenter: parent.horizontalCenter; label: "−"
                      onClicked: root.zoomLevel = Math.max(1.0, Math.round((root.zoomLevel-0.2)*10)/10) }
        }
        // Горизонтальный ряд — в открытом состоянии
        Row {
            visible: root._manualOpen
            Layout.alignment: Qt.AlignHCenter
            spacing: 5
            ZoomBtn { label: "−"; onClicked: root.zoomLevel = Math.max(1.0, Math.round((root.zoomLevel-0.2)*10)/10) }
            Column {
                anchors.verticalCenter: parent.verticalCenter; spacing: 1
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: "ZOOM"; color: "#4A5E6E"
                       font.pixelSize: 7; font.family: "Menlo"; font.letterSpacing: 1.5 }
                Text { anchors.horizontalCenter: parent.horizontalCenter
                       text: "×" + root.zoomLevel.toFixed(1); color: "#A9B5C2"
                       font.pixelSize: 11; font.family: "Menlo"; font.weight: Font.Normal }
            }
            ZoomBtn { label: "+"; onClicked: root.zoomLevel = Math.min(8.0, Math.round((root.zoomLevel+0.2)*10)/10) }
        }

        // ── MARK BBOX ─────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true; height: 22; radius: 5; visible: root.isRunning
            color: mbMa.containsMouse ? "#1C2A38" : "transparent"
            border.color: "#1C2A38"; border.width: 1
            Text { anchors.centerIn: parent; text: "РАЗМЕТ."; color: "#4A5E6E"
                   font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 1.5 }
            MouseArea { id: mbMa; anchors.fill: parent; hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor; onClicked: root.markBBoxClicked() }
        }

        Item { implicitHeight: 0 }
    }

    // ── Helper ────────────────────────────────────────────────────────
    function _roundRect(ctx, x, y, w, h, r) {
        ctx.beginPath()
        ctx.moveTo(x+r,y); ctx.lineTo(x+w-r,y)
        ctx.arcTo(x+w,y,x+w,y+r,r); ctx.lineTo(x+w,y+h-r)
        ctx.arcTo(x+w,y+h,x+w-r,y+h,r); ctx.lineTo(x+r,y+h)
        ctx.arcTo(x,y+h,x,y+h-r,r); ctx.lineTo(x,y+r)
        ctx.arcTo(x,y,x+r,y,r); ctx.closePath()
    }

    // ── Inline Components ─────────────────────────────────────────────
    component SbButton: Rectangle {
        id: sb
        height: 52; radius: 7
        property string label:     ""
        property color  accent:    "#8FA4B8"
        property bool   enabled:   true
        property var    iconPaint: null
        signal clicked()

        opacity: sb.enabled ? 1.0 : 0.28
        color: sbMa.pressed       ? Qt.rgba(accent.r, accent.g, accent.b, 0.22)
             : sbMa.containsMouse ? Qt.rgba(accent.r, accent.g, accent.b, 0.09)
             : "transparent"
        border.color: sbMa.containsMouse ? Qt.rgba(accent.r, accent.g, accent.b, 0.45) : "#1C2A38"
        border.width: 1

        Column { anchors.centerIn: parent; spacing: 4
            Canvas {
                id: sbCvs; width: 22; height: 22; anchors.horizontalCenter: parent.horizontalCenter
                property string colorStr: sb.accent.toString()
                onColorStrChanged: requestPaint(); Component.onCompleted: requestPaint()
                onPaint: {
                    var ctx = getContext("2d"); ctx.clearRect(0, 0, 22, 22)
                    if (sb.iconPaint) sb.iconPaint(ctx, 22, 22, colorStr)
                }
            }
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: sb.label; color: sb.accent
                   font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 1.5; font.weight: Font.Normal }
        }
        MouseArea { id: sbMa; anchors.fill: parent; hoverEnabled: true
                    cursorShape: sb.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onClicked: if (sb.enabled) sb.clicked() }
    }

    component ZoomBtn: Rectangle {
        id: zb
        width: 30; height: 30; radius: 5
        property string label: "+"
        signal clicked()
        color: zbMa.containsMouse ? "#1C2A38" : "transparent"
        border.color: "#1C2A38"; border.width: 1
        Text { anchors.centerIn: parent; text: zb.label; color: "#8FA4B8"; font.pixelSize: 15; font.family: "Menlo" }
        MouseArea { id: zbMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: zb.clicked() }
    }

    component DpadBtn: Rectangle {
        id: db
        width: 38; height: 38; radius: 6
        property string arrowChar: "▲"
        signal clicked()
        color: dbMa.pressed       ? Qt.rgba(0.561, 0.643, 0.722, 0.28)
             : dbMa.containsMouse ? Qt.rgba(1,1,1,0.12) : Qt.rgba(1,1,1,0.06)
        border.color: Qt.rgba(1,1,1,0.20); border.width: 1
        Text { anchors.centerIn: parent; text: db.arrowChar; color: "#8FA4B8"; font.pixelSize: 16 }
        MouseArea { id: dbMa; anchors.fill: parent; hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor; onClicked: db.clicked() }
    }
}
