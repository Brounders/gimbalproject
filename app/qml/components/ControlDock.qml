import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    height: 54
    color: "#0D141C"

    property bool   isRunning:     false
    property string trackingState: "SEARCH"

    signal startClicked()
    signal stopClicked()
    signal nextTargetClicked()
    signal confirmClicked()
    signal releaseClicked()
    signal markBBoxClicked()

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 14
        spacing: 8

        // START / STOP
        DockButton {
            text:   root.isRunning ? "СТОП" : "СТАРТ"
            accent: root.isRunning ? "#E26B6B" : "#52D273"
            minWidth: 84
            onClicked: root.isRunning ? root.stopClicked() : root.startClicked()
        }

        Rectangle { width: 1; height: 28; color: "#1C2A38" }

        DockButton {
            text: "СЛЕД. ЦЕЛЬ"
            enabled: root.isRunning
            onClicked: root.nextTargetClicked()
        }

        DockButton {
            text: "ЗАХВАТ"
            accent: "#8FA4B8"
            enabled: root.isRunning && root.trackingState !== "LOCK"
            onClicked: root.confirmClicked()
        }

        DockButton {
            text: "ОТПУСТИТЬ"
            enabled: root.isRunning && root.trackingState === "LOCK"
            onClicked: root.releaseClicked()
        }

        Rectangle { width: 1; height: 28; color: "#1C2A38" }

        DockButton {
            text: "MARK BBOX"
            enabled: root.isRunning
            onClicked: root.markBBoxClicked()
        }

        Item { Layout.fillWidth: true }

        // State readout
        Column {
            spacing: 2
            visible: root.isRunning
            Text {
                text: "РЕЖИМ УПРАВЛЕНИЯ"
                color: "#4A5E6E"
                font.pixelSize: 8
                font.family: "Menlo"
                font.letterSpacing: 1.5
            }
            Text {
                text: root.trackingState
                color: root.trackingState === "LOCK"  ? "#52D273"
                     : root.trackingState === "TRACK" ? "#8FA4B8"
                     : root.trackingState === "LOST"  ? "#E26B6B"
                     : "#E8B547"
                font.pixelSize: 14
                font.family: "Menlo"
                font.weight: Font.Normal
            }
        }
    }

    // Inline button component
    component DockButton: Rectangle {
        id: db
        property string text:     ""
        property color  accent:   "#8FA4B8"
        property int    minWidth: 0
        property bool   enabled:  true
        signal clicked()

        width:  Math.max(minWidth, dblbl.implicitWidth + 22)
        height: 34
        radius: 6
        opacity: db.enabled ? 1.0 : 0.35

        color: !db.enabled    ? "transparent"
             : dbma.pressed   ? Qt.rgba(db.accent.r, db.accent.g, db.accent.b, 0.20)
             : dbma.containsMouse ? Qt.rgba(db.accent.r, db.accent.g, db.accent.b, 0.10)
             : "transparent"

        border.color: db.enabled
                      ? Qt.rgba(db.accent.r, db.accent.g, db.accent.b, dbma.containsMouse ? 0.55 : 0.30)
                      : Qt.rgba(1.000, 1.000, 1.000, 0.08)
        border.width: 1

        Text {
            id: dblbl
            anchors.centerIn: parent
            text: db.text
            color: db.enabled ? db.accent : "#4A5E6E"
            font.pixelSize: 10
            font.family: "Menlo"
            font.letterSpacing: 1
        }

        MouseArea {
            id: dbma
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: db.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: if (db.enabled) db.clicked()
        }
    }
}
