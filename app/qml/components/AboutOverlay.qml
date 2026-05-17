import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: Qt.rgba(0, 0, 0, 0.72)

    signal closed()

    MouseArea { anchors.fill: parent; onClicked: root.closed() }

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(500, parent.width - 80)
        height: Math.min(500, parent.height - 80)
        color: "#0C1219"; radius: 12
        border.color: Qt.rgba(1,1,1,0.14); border.width: 1; clip: true

        MouseArea { anchors.fill: parent }

        ColumnLayout {
            anchors.fill: parent; spacing: 0

            // Header
            Rectangle {
                Layout.fillWidth: true; height: 46; color: "transparent"
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#1C2A38" }
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 16
                    Text { text: "О СИСТЕМЕ"; color: "#E6ECF3"; font.pixelSize: 12; font.family: "Menlo"; font.letterSpacing: 1.5 }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                        width: 72; height: 28; radius: 6; color: "transparent"
                        border.color: Qt.rgba(0.886,0.420,0.420,0.35); border.width: 1
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.closed() }
                        Text { anchors.centerIn: parent; text: "ЗАКРЫТЬ"; color: "#E26B6B"
                               font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1 }
                    }
                }
            }

            // Logo area
            Rectangle {
                Layout.fillWidth: true; height: 110; color: "transparent"
                Column {
                    anchors.centerIn: parent; spacing: 10
                    Item {
                        width: 48; height: 48; anchors.horizontalCenter: parent.horizontalCenter
                        Rectangle { anchors.fill: parent; radius: 24; color: "transparent"; border.color: "#2A4A60"; border.width: 2 }
                        Rectangle { anchors.centerIn: parent; width: 18; height: 18; radius: 9; color: "transparent"; border.color: "#2A4A60"; border.width: 1.5 }
                        Rectangle { anchors.centerIn: parent; width: 6; height: 6; radius: 3; color: "#2A4A60" }
                    }
                    Text { text: "GIMBAL OPERATOR STATION"; color: "#8FA4B8"; font.pixelSize: 12; font.family: "Menlo"
                           font.letterSpacing: 2; anchors.horizontalCenter: parent.horizontalCenter }
                    Text { text: "v0.9.1-prototype"; color: "#3A5060"; font.pixelSize: 10; font.family: "Menlo"
                           anchors.horizontalCenter: parent.horizontalCenter }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#131E2A" }

            // Info
            ColumnLayout {
                Layout.fillWidth: true; Layout.margins: 24; Layout.topMargin: 16; spacing: 0

                Repeater {
                    model: [
                        {lbl:"Базовая модель",   val:"drone_bird_probe_fast"},
                        {lbl:"SHA256 (8 hex)",   val:"bedc77fe"},
                        {lbl:"Платформа",        val:"Mac M1 · MPS"},
                        {lbl:"Python",           val:"3.11"},
                        {lbl:"Qt / PySide6",     val:"6.10.2"},
                        {lbl:"ultralytics",      val:"8.x · YOLOv8n"},
                        {lbl:"OpenCV",           val:"4.x"},
                        {lbl:"Лицензия",         val:"Internal — No Distribution"},
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true; height: 36; color: "transparent"
                        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#0F1820" }
                        RowLayout {
                            anchors.fill: parent
                            Text { text: modelData.lbl; color: "#4A5E6E"; font.pixelSize: 11; font.family: "Menlo"; Layout.preferredWidth: 160 }
                            Text { text: modelData.val; color: "#8FA4B8"; font.pixelSize: 11; font.family: "Menlo" }
                        }
                    }
                }
            }
            Item { Layout.fillHeight: true }
        }
    }
}
