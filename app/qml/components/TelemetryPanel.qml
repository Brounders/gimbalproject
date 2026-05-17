import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: Qt.rgba(0.08, 0.13, 0.22, 0.48)
    radius: 10
    border.color: Qt.rgba(1,1,1,0.26); border.width: 1
    clip: true
    property real panelMaxH: 9999
    height: collapsed ? 38 : Math.min(385, 38 + panelMaxH)
    Behavior on height { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }

    property int  fps:           0
    property int  latencyMs:     0
    property int  activeTargets: 0
    property int  idSwitches:    0
    property real falseLockRisk: 0.0
    property string targetLifecycle: "OFFLINE"
    property string activeSource: "—"
    property real lockScore: 0.0
    property real reliability: 0.0
    property bool isRunning:     false
    property real confidence:    0.0
    property bool collapsed:     false

    signal collapseToggled()

    property real  _dist:    142.0
    property int   _course:  87
    property real  _alt:     142.5
    property real  _speed:   11.4
    property int   _battery: 68
    property int   _signal:  91

    Timer {
        interval: 1800; running: root.isRunning; repeat: true
        onTriggered: {
            root._dist   = Math.round((120 + root.confidence * 100) * 10) / 10
            root._course = (root._course + Math.floor(Math.random() * 3 - 1) + 360) % 360
            root._alt    = Math.round((130 + root.fps * 0.4) * 10) / 10
            root._speed  = Math.round((8 + Math.random() * 6) * 10) / 10
            root._signal = Math.round(70 + root.confidence * 25)
        }
    }

    function stageLabel(stage) {
        var labels = {
            "OFFLINE": "OFFLINE",
            "SEARCH": "ПОИСК",
            "DETECTED": "ОБНАР.",
            "CANDIDATE": "КАНД.",
            "ACQUIRE": "ЗАХВАТ",
            "VERIFYING": "ПРОВ.",
            "VERIFIED": "ПОДТВ.",
            "LOCKED": "LOCK",
            "TRACKING": "TRACK",
            "WEAK_TRACK": "СЛАБ.",
            "REACQUIRE": "REACQ",
            "LOST": "ПОТЕРЯ"
        }
        return labels[stage] || stage
    }

    ColumnLayout {
        anchors.top: parent.top; anchors.left: parent.left; anchors.right: parent.right
        spacing: 0

        // Header
        Rectangle {
            Layout.fillWidth: true; height: 38; color: "transparent"
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Qt.rgba(1,1,1,0.07) }

            Text {
                anchors.left: parent.left; anchors.leftMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                text: "ТЕЛЕМЕТРИЯ"; color: "#5A7080"
                font.pixelSize: 9; font.family: "Menlo"
                font.letterSpacing: 2; font.weight: Font.DemiBold
            }

            // Collapse button — anchored to right
            Rectangle {
                anchors.right: parent.right; anchors.rightMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                width: 20; height: 20; radius: 4
                color: tColMa.containsMouse ? Qt.rgba(1,1,1,0.08) : "transparent"
                border.color: Qt.rgba(1,1,1,0.10); border.width: 1
                Text { anchors.centerIn: parent; text: root.collapsed ? "+" : "−"; color: "#5A7080"
                       font.pixelSize: 12; font.family: "Menlo" }
                MouseArea { id: tColMa; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor; onClicked: root.collapseToggled() }
            }
        }

        // Navigation grid
        GridLayout {
            Layout.fillWidth: true; Layout.margins: 10
            columns: 2; columnSpacing: 6; rowSpacing: 6

            MetricCard { label: "ДИСТ.";    value: root.isRunning ? root._dist.toFixed(1) + " м"              : "—" }
            MetricCard { label: "КУРС";     value: root.isRunning ? String(root._course).padStart(3, "0") + "°" : "—" }
            MetricCard { label: "ВЫСОТА";   value: root.isRunning ? root._alt.toFixed(1) + " м"               : "—" }
            MetricCard { label: "СКОРОСТЬ"; value: root.isRunning ? root._speed.toFixed(1) + " м/с"           : "—" }
            MetricCard {
                label: "БАТАРЕЯ"; value: root._battery + "%"; showBar: true
                barValue: root._battery / 100
                barColor: root._battery > 40 ? "#52D273" : root._battery > 20 ? "#E8B547" : "#E26B6B"
            }
            MetricCard {
                label: "СИГНАЛ"; value: root.isRunning ? root._signal + "%" : "—"; showBar: true
                barValue: root.isRunning ? root._signal / 100 : 0
                barColor: root._signal > 60 ? "#8FA4B8" : "#E8B547"
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#151E28"; Layout.leftMargin: 10; Layout.rightMargin: 10 }

        // Pipeline metrics
        GridLayout {
            Layout.fillWidth: true; Layout.margins: 10; Layout.topMargin: 7
            columns: 2; columnSpacing: 6; rowSpacing: 6

            MetricCard { label: "ЭТАП";      value: root.isRunning ? root.stageLabel(root.targetLifecycle) : "OFFLINE"; small: true }
            MetricCard { label: "SOURCE";    value: root.isRunning ? root.activeSource : "—"; small: true }
            MetricCard { label: "LOCK";      value: root.isRunning ? root.lockScore.toFixed(2) : "—"; small: true }
            MetricCard { label: "НАДЁЖН.";   value: root.isRunning ? root.reliability.toFixed(2) : "—"; small: true }
            MetricCard { label: "FPS";       value: root.fps > 0 ? root.fps + "" : "—"; small: true }
            MetricCard { label: "ЗАДЕРЖКА";  value: root.latencyMs > 0 ? root.latencyMs + " мс" : "—"; small: true }
            MetricCard {
                label: "FALSE LOCK"; small: true
                value: root.isRunning ? Math.round(root.falseLockRisk * 100) + "%" : "—"
                valueColor: root.falseLockRisk > 0.20 ? "#E26B6B"
                          : root.falseLockRisk > 0.10 ? "#E8B547" : "#52D273"
            }
            MetricCard { label: "ID SW"; value: root.idSwitches + ""; small: true }
        }

        // Footer
        Rectangle {
            Layout.fillWidth: true; height: 28; color: "transparent"
            Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: Qt.rgba(1,1,1,0.04) }
            Row {
                anchors.fill: parent; anchors.leftMargin: 14; anchors.rightMargin: 14
                Text { text: "УСТРОЙСТВО"; color: "#3A5060"; font.pixelSize: 8; font.family: "Menlo"
                       font.letterSpacing: 1.2; anchors.verticalCenter: parent.verticalCenter; width: 80 }
                Text { text: "LOCAL"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"
                       anchors.verticalCenter: parent.verticalCenter }
            }
        }
    }

    component MetricCard: Rectangle {
        id: mc
        property string label:      ""
        property string value:      "—"
        property bool   showBar:    false
        property real   barValue:   0.0
        property color  barColor:   "#8FA4B8"
        property color  valueColor: "#E6ECF3"
        property bool   small:      false

        Layout.fillWidth: true
        height: small ? 44 : 56; radius: 6
        color: "#0A1018"
        border.color: Qt.rgba(1,1,1,0.06); border.width: 1

        Column {
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 9; topMargin: 8 }
            spacing: 3
            Text { text: mc.label; color: "#4A5E6E"; font.pixelSize: 8; font.family: "Menlo"
                   font.letterSpacing: 1.2; font.weight: Font.Normal }
            Text { text: mc.value; color: mc.valueColor
                   font.pixelSize: mc.small ? 12 : 15; font.family: "Menlo"; font.weight: Font.DemiBold }
        }

        Rectangle {
            visible: mc.showBar
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 9; bottomMargin: 7 }
            height: 3; radius: 1.5; color: Qt.rgba(1,1,1,0.08)
            Rectangle {
                height: parent.height; radius: parent.radius; color: mc.barColor
                width: parent.width * mc.barValue
                Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
            }
        }
    }
}
