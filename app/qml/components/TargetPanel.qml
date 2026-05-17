import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: Qt.rgba(0.08, 0.13, 0.22, 0.48)
    radius: 10
    border.color: Qt.rgba(1,1,1,0.26); border.width: 1
    clip: true
    property real panelMaxH: 9999
    height: collapsed ? 38 : Math.min(318, 38 + panelMaxH)
    Behavior on height { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }

    property string trackingState: "SEARCH"
    property string lifecycleState: "OFFLINE"
    property string activeSource: "—"
    property bool   isRunning:     false
    property int    targetId:      1
    property real   confidence:    0.0
    property real   lockScore:     0.0
    property real   reliability:   0.0
    property real   presentProbability: 0.0
    property string currentMode:   "ДЕНЬ"
    property bool   collapsed:     false

    signal collapseToggled()

    property color stateColor: lifecycleState === "LOCKED"    ? "#52D273"
                             : lifecycleState === "TRACKING"  ? "#5FD2C8"
                             : lifecycleState === "VERIFIED"  ? "#52D273"
                             : lifecycleState === "REACQUIRE" ? "#E8B547"
                             : lifecycleState === "VERIFYING" ? "#E8B547"
                             : lifecycleState === "WEAK_TRACK"? "#E8B547"
                             : lifecycleState === "LOST"      ? "#E26B6B"
                             : lifecycleState === "CANDIDATE" ? "#8FA4B8"
                             : lifecycleState === "ACQUIRE"   ? "#E8B547"
                             : lifecycleState === "DETECTED"  ? "#9BB0C2"
                             : "#4A5E6E"

    property int _trackSec: 0
    Timer {
        interval: 1000
        running: root.isRunning && ["VERIFYING", "VERIFIED", "LOCKED", "TRACKING", "WEAK_TRACK", "REACQUIRE"].indexOf(root.lifecycleState) >= 0
        repeat: true
        onTriggered: root._trackSec++
        onRunningChanged: if (!running) root._trackSec = 0
    }

    function fmtTime(s) {
        var m = Math.floor(s / 60); var sec = s % 60
        return (m < 10 ? "0" : "") + m + ":" + (sec < 10 ? "0" : "") + sec
    }

    function camLabel() {
        return currentMode === "ИК" ? "ИК" : currentMode === "НОЧЬ" ? "НВ" : "ЭО"
    }

    function stageLabel(stage) {
        var labels = {
            "OFFLINE": "OFFLINE",
            "SEARCH": "ПОИСК",
            "DETECTED": "ОБНАРУЖЕНО",
            "CANDIDATE": "КАНДИДАТ",
            "ACQUIRE": "ЗАХВАТ",
            "VERIFYING": "ПРОВЕРКА",
            "VERIFIED": "ПОДТВЕРЖДЕНО",
            "LOCKED": "LOCK",
            "TRACKING": "TRACK",
            "WEAK_TRACK": "СЛАБЫЙ ТРЕК",
            "REACQUIRE": "REACQUIRE",
            "LOST": "ПОТЕРЯ"
        }
        return labels[stage] || stage
    }

    function metricText(value) {
        return root.isRunning ? Number(Math.max(0, Math.min(1, value))).toFixed(2) : "—"
    }

    function stageGroup(stage) {
        if (stage === "DETECTED" || stage === "CANDIDATE") return "detect"
        if (stage === "ACQUIRE" || stage === "VERIFYING" || stage === "VERIFIED") return "acquire"
        if (stage === "LOCKED" || stage === "TRACKING" || stage === "WEAK_TRACK" || stage === "REACQUIRE") return "track"
        return "idle"
    }

    ColumnLayout {
        anchors.top: parent.top; anchors.left: parent.left; anchors.right: parent.right
        spacing: 0

        // ── Header ───────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true; height: 38; color: "transparent"
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Qt.rgba(1,1,1,0.07) }

            Text {
                anchors.left: parent.left; anchors.leftMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                text: "ЦЕЛЬ"; color: "#5A7080"; font.pixelSize: 9; font.family: "Menlo"
                font.letterSpacing: 2; font.weight: Font.DemiBold
            }

            // Collapse button — anchored to right
            Rectangle {
                id: tpColBtn
                anchors.right: parent.right; anchors.rightMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                width: 20; height: 20; radius: 4
                color: tpColMa.containsMouse ? Qt.rgba(1,1,1,0.08) : "transparent"
                border.color: Qt.rgba(1,1,1,0.10); border.width: 1
                Text { anchors.centerIn: parent; text: root.collapsed ? "+" : "−"
                       color: "#5A7080"; font.pixelSize: 12; font.family: "Menlo" }
                MouseArea { id: tpColMa; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor; onClicked: root.collapseToggled() }
            }

            // Class chip — anchored left of collapse button
            Rectangle {
                anchors.right: tpColBtn.left; anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                width: clsLbl.implicitWidth + 14; height: 20; radius: 4
                color: Qt.rgba(1,1,1,0.06); border.color: Qt.rgba(1,1,1,0.12); border.width: 1
                Text { id: clsLbl; anchors.centerIn: parent; text: root.isRunning ? root.activeSource : "—"
                       color: root.stateColor; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1 }
            }
        }

        // ── Этап цели ────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            height: 58
            color: "transparent"
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Qt.rgba(1,1,1,0.04) }

            Column {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                anchors.topMargin: 8
                spacing: 7

                Row {
                    width: parent.width
                    height: 18
                    Text {
                        text: "ЭТАП ЦЕЛИ"
                        color: "#4A5E6E"
                        font.pixelSize: 9
                        font.family: "Menlo"
                        font.letterSpacing: 1.5
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Item { width: Math.max(0, parent.width - 86 - stageText.implicitWidth); height: 1 }
                    Text {
                        id: stageText
                        text: root.isRunning ? root.stageLabel(root.lifecycleState) : "OFFLINE"
                        color: root.isRunning ? root.stateColor : "#4A5E6E"
                        font.pixelSize: 12
                        font.family: "Menlo"
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                        width: Math.min(104, implicitWidth)
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Row {
                    width: parent.width
                    height: 22
                    spacing: 4
                    Repeater {
                        model: [
                            {key:"detect",  label:"ДЕТЕКЦИЯ"},
                            {key:"acquire", label:"ЗАХВАТ"},
                            {key:"track",   label:"ВЕДЕНИЕ"}
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            property bool active: root.stageGroup(root.lifecycleState) === modelData.key
                            width: (parent.width - 8) / 3
                            height: 22
                            radius: 4
                            color: active ? Qt.rgba(root.stateColor.r, root.stateColor.g, root.stateColor.b, 0.20)
                                          : Qt.rgba(1,1,1,0.035)
                            border.color: active ? root.stateColor : Qt.rgba(1,1,1,0.08)
                            border.width: 1
                            Behavior on color { ColorAnimation { duration: 180 } }
                            Text {
                                anchors.centerIn: parent
                                text: modelData.label
                                color: parent.active ? root.stateColor : "#4A5E6E"
                                font.family: "Menlo"
                                font.pixelSize: 8
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                                width: parent.width - 6
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }
                }
            }
        }

        // ── Data rows ────────────────────────────────────────────────
        Repeater {
            model: [
                {lbl:"ID",           val: function() { return root.isRunning ? "T-" + (root.targetId < 10 ? "0" : "") + root.targetId : "—" }},
                {lbl:"ВРЕМЯ",        val: function() { return root.isRunning ? root.fmtTime(root._trackSec) : "—:—" }},
                {lbl:"КАМЕРА",       val: function() { return root.camLabel() + " / " + root.activeSource }},
            ]
            delegate: Rectangle {
                required property var modelData
                required property int index
                Layout.fillWidth: true; height: 30; color: "transparent"
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Qt.rgba(1,1,1,0.04) }

                Row {
                    anchors.fill: parent; anchors.leftMargin: 14; anchors.rightMargin: 14

                    Text {
                        text: modelData.lbl
                        color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"
                        font.letterSpacing: 1.5; width: 82; anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        text: modelData.val()
                        color: "#A9B5C2"
                        font.pixelSize: 12; font.family: "Menlo"; font.weight: Font.Normal
                        elide: Text.ElideRight
                        width: parent.width - 82
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }

        // ── УВЕРЕННОСТЬ ──────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            height: confSection.implicitHeight + 18
            color: "transparent"
            Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: "#151E28" }

            Column {
                id: confSection
                anchors { left: parent.left; right: parent.right; margins: 14; verticalCenter: parent.verticalCenter }
                spacing: 8

                Row {
                    width: parent.width
                    Text {
                        text: "УВЕРЕННОСТЬ"
                        color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"
                        font.letterSpacing: 1.5; anchors.verticalCenter: parent.verticalCenter
                    }
                    Item { width: parent.width - 110 - confPct.implicitWidth - 28; height: 1 }
                    Text {
                        id: confPct
                        text: root.isRunning ? Math.round(root.confidence * 100) + "%" : "—"
                        font.pixelSize: 24; font.family: "Menlo"; font.weight: Font.Bold
                        color: root.isRunning
                               ? (root.confidence > 0.80 ? "#52D273"
                                : root.confidence > 0.55 ? "#E8B547" : "#E26B6B")
                               : "#3A5060"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Rectangle {
                    width: parent.width; height: 4; radius: 2; color: Qt.rgba(1,1,1,0.07)
                    Rectangle {
                        height: parent.height; radius: parent.radius
                        width: parent.width * (root.isRunning ? root.confidence : 0)
                        color: root.confidence > 0.80 ? "#52D273"
                             : root.confidence > 0.55 ? "#E8B547" : "#E26B6B"
                        Behavior on width { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 42
            color: "transparent"
            Row {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 8
                Repeater {
                    model: [
                        {lbl:"LOCK", value: function() { return root.metricText(root.lockScore) }},
                        {lbl:"НАДЁЖН.", value: function() { return root.metricText(Math.max(root.reliability, root.presentProbability)) }}
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        width: (parent.width - 8) / 2
                        height: 30
                        radius: 5
                        anchors.verticalCenter: parent.verticalCenter
                        color: Qt.rgba(1,1,1,0.035)
                        border.color: Qt.rgba(1,1,1,0.08)
                        border.width: 1
                        Text {
                            anchors.left: parent.left
                            anchors.leftMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.lbl
                            color: "#4A5E6E"
                            font.family: "Menlo"
                            font.pixelSize: 8
                            font.weight: Font.DemiBold
                        }
                        Text {
                            anchors.right: parent.right
                            anchors.rightMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.value()
                            color: "#A9B5C2"
                            font.family: "Menlo"
                            font.pixelSize: 11
                        }
                    }
                }
            }
        }

    }
}
