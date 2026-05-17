import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    height: 28
    color: "#080D12"

    property string trackingState: "SEARCH"
    property string currentMode:   "ДЕНЬ"
    property string currentSource: "КАМЕРА"
    property bool   isRecording:   false
    property string lastAction:    "Система готова"
    property int    fps:           0

    // Mock GPS coords (slowly drifting)
    property real _lat: 59.938
    property real _lon: 30.314
    property int  _sig: -64

    Timer {
        interval: 4000; running: true; repeat: true
        onTriggered: {
            root._lat = Math.round((root._lat + (Math.random()-0.5)*0.001) * 1000) / 1000
            root._lon = Math.round((root._lon + (Math.random()-0.5)*0.001) * 1000) / 1000
            root._sig = -60 + Math.floor(Math.random() * -10)
        }
    }

    // Top border
    Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: "#151E28" }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 14
        spacing: 0

        component Sep: Rectangle {
            width: 1; height: 12; color: "#1C2A38"
            Layout.leftMargin: 12; Layout.rightMargin: 12
        }

        // GPS coordinates
        Text {
            text: root._lat.toFixed(3) + "° N   " + root._lon.toFixed(3) + "° E"
            color: "#4A5E6E"; font.pixelSize: 10; font.family: "Menlo"
            font.letterSpacing: 0.5
        }

        Sep {}

        // Signal
        Text {
            text: "SIG " + root._sig + " dBm"
            color: root._sig > -70 ? "#52D273" : root._sig > -80 ? "#E8B547" : "#E26B6B"
            font.pixelSize: 10; font.family: "Menlo"
        }

        Sep {}

        // REC indicator
        Row {
            spacing: 5
            Rectangle {
                width: 6; height: 6; radius: 3
                color: root.isRecording ? "#E26B6B" : "#2A3A4A"
                anchors.verticalCenter: parent.verticalCenter
                SequentialAnimation on opacity {
                    running: root.isRecording; loops: Animation.Infinite
                    NumberAnimation { to: 0.25; duration: 600 }
                    NumberAnimation { to: 1.0;  duration: 600 }
                }
                opacity: 1
            }
            Text {
                text: root.isRecording ? "REC" : "NO REC"
                color: root.isRecording ? "#E26B6B" : "#3A4E5E"
                font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Sep {}

        // Last action
        Text {
            text: root.lastAction; color: "#4A5E6E"
            font.pixelSize: 10; font.family: "Menlo"
            elide: Text.ElideRight; Layout.maximumWidth: 300
        }

        Item { Layout.fillWidth: true }

        // FPS counter (right side — reference style)
        Text {
            text: root.fps > 0 ? "FPS " + root.fps : "FPS —"
            color: root.fps > 20 ? "#4A5E6E" : root.fps > 0 ? "#E8B547" : "#3A4E5E"
            font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 0.5
        }
    }
}
