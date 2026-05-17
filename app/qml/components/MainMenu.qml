import QtQuick 2.15

Rectangle {
    id: menu
    width: 220
    color: "#0B1219"

    property bool open: false

    signal close()
    signal dtsRequested()

    // Right border
    Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: "#1C2A38" }

    // Slide animation
    x: open ? 0 : -width
    Behavior on x { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }

    // Shadow when open
    Rectangle {
        anchors.left: parent.right
        width: 20; height: parent.height
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: Qt.rgba(0,0,0,0.25) }
            GradientStop { position: 1.0; color: Qt.rgba(0,0,0,0.00) }
        }
        visible: menu.open
    }

    Column {
        anchors.top: parent.top; anchors.topMargin: 54  // below topbar
        anchors.left: parent.left; anchors.right: parent.right
        spacing: 0

        // ── Section: ИНСТРУМЕНТЫ ───────────────────────────────
        Text {
            leftPadding: 16; topPadding: 14; bottomPadding: 8
            text: "ИНСТРУМЕНТЫ"; color: "#2A4050"
            font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 2
        }

        MenuBtn {
            label: "DTS"
            desc:  "Обучающий стол"
            accent: "#8FA4B8"
            onActivated: { menu.dtsRequested(); menu.close() }
        }
        MenuBtn {
            label: "ЭКСПЕРТ"
            desc:  "Расширенные настройки"
            stub: true
        }

        Rectangle { width: parent.width; height: 1; color: "#151E28" }

        // ── Section: СИСТЕМА ───────────────────────────────────
        Text {
            leftPadding: 16; topPadding: 14; bottomPadding: 8
            text: "СИСТЕМА"; color: "#2A4050"
            font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 2
        }

        MenuBtn { label: "КАЛИБРОВКА";   stub: true }
        MenuBtn { label: "ДИАГНОСТИКА";  stub: true }
        MenuBtn { label: "НАСТРОЙКИ";    stub: true }
        MenuBtn { label: "О СИСТЕМЕ";    stub: true }
    }

    // ── Inline: menu button row ───────────────────────────────────────
    component MenuBtn: Item {
        id: mb
        property string label:  ""
        property string desc:   ""
        property bool   stub:   false
        property color  accent: "#6F7E8E"

        signal activated()

        width: parent.width; height: desc !== "" ? 52 : 40

        Rectangle {
            anchors.fill: parent
            color: mMa.containsMouse && !mb.stub ? Qt.rgba(1,1,1,0.04) : "transparent"
        }

        Rectangle {
            anchors.bottom: parent.bottom; width: parent.width; height: 1
            color: Qt.rgba(1,1,1,0.04)
        }

        Column {
            anchors.left: parent.left; anchors.leftMargin: 16
            anchors.verticalCenter: parent.verticalCenter; spacing: 3

            Text {
                text: mb.label
                color: mb.stub ? "#2A4050" : mb.accent
                font.pixelSize: 11; font.family: "Menlo"; font.weight: Font.Normal
            }
            Text {
                visible: mb.desc !== ""
                text: mb.desc; color: "#253040"
                font.pixelSize: 9; font.family: "Menlo"
            }
        }

        // Lock icon for stubs
        Text {
            visible: mb.stub
            anchors.right: parent.right; anchors.rightMargin: 14
            anchors.verticalCenter: parent.verticalCenter
            text: "⊘"; color: "#1C2A38"; font.pixelSize: 13
        }

        MouseArea {
            id: mMa; anchors.fill: parent; hoverEnabled: true
            cursorShape: mb.stub ? Qt.ArrowCursor : Qt.PointingHandCursor
            onClicked: if (!mb.stub) mb.activated()
        }
    }
}
