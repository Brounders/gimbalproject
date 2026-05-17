import QtQuick 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    height: 44

    property bool   isRunning:     false
    property bool   isRecording:   false
    property string currentMode:   "ДЕНЬ"
    property string currentSource: ""
    property string trackingState: "SEARCH"
    property int    targetId:      1

    // Internal menu state
    property bool _menuOpen: false

    signal modeChanged(string mode)
    signal recordToggled()
    signal sourceChanged(string source)
    signal targetLabRequested()
    signal dtsRequested()
    signal expertRequested()
    signal gtAssistRequested()
    signal calibRequested()
    signal diagRequested()
    signal settingsRequested()
    signal aboutRequested()

    // ── Background (glassy) ──────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0.05, 0.09, 0.15, 0.70)
        // Bottom border
        Rectangle {
            anchors.bottom: parent.bottom; width: parent.width; height: 1
            color: Qt.rgba(1,1,1, 0.16)
        }
        // Top specular highlight (iOS glass)
        Rectangle {
            anchors.top: parent.top; width: parent.width; height: 1
            color: Qt.rgba(1,1,1, 0.18)
        }
    }

    // ── RIGHT area — date + time ─────────────────────────────────────
    Item {
        id: rightArea
        width: dateTimeLbl.implicitWidth
        height: dateTimeLbl.implicitHeight
        anchors.right:          parent.right
        anchors.rightMargin:    16
        anchors.verticalCenter: parent.verticalCenter
        property string dateTimeText: ""

        function refreshDateTime() {
            var now = new Date()
            dateTimeText = Qt.formatDate(now, "dd.MM.yyyy") + "  " + Qt.formatTime(now, "HH:mm:ss")
        }

        Component.onCompleted: refreshDateTime()

        Timer {
            interval: 1000
            running: true
            repeat: true
            onTriggered: rightArea.refreshDateTime()
        }

        Text {
            id: dateTimeLbl
            anchors.centerIn: parent
            text: rightArea.dateTimeText
            color: "#A9B5C2"
            font.pixelSize: 12
            font.family: "Menlo"
            font.weight: Font.Normal
        }
    }

    // ── NORMAL content (logo + modes + target) ───────────────────────
    Item {
        id: normalContent
        anchors.left:  parent.left;  anchors.leftMargin:  10
        anchors.top:   parent.top;   anchors.bottom: parent.bottom
        anchors.right: rightArea.left
        opacity: root._menuOpen ? 0 : 1
        visible: opacity > 0.01
        Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

        Row {
            anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
            spacing: 8

            // Hamburger
            Rectangle {
                width: 32; height: 32; radius: 6
                anchors.verticalCenter: parent.verticalCenter
                color: hbMa.containsMouse ? Qt.rgba(1,1,1,0.09) : "transparent"
                border.color: Qt.rgba(1,1,1,0.12); border.width: 1
                Column { anchors.centerIn: parent; spacing: 4
                    Repeater { model: 3
                        Rectangle { width: 13; height: 1.5; radius: 1; color: hbMa.containsMouse ? "#8FA4B8" : "#4A5E6E" }
                    }
                }
                MouseArea { id: hbMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: root._menuOpen = true }
            }

            Rectangle { width: 1; height: 24; color: Qt.rgba(1,1,1,0.08); anchors.verticalCenter: parent.verticalCenter }

            // Logo
            Item { width: 22; height: 22; anchors.verticalCenter: parent.verticalCenter
                Rectangle { anchors.fill: parent; radius: 11; color: "transparent"; border.color: "#3A5060"; border.width: 1.5 }
                Rectangle { anchors.centerIn: parent; width: 8; height: 8; radius: 4; color: "#3A5060" }
            }
            Column { anchors.verticalCenter: parent.verticalCenter; spacing: 2
                Text { text: "GIMBAL"; color: "#A9B5C2"; font.pixelSize: 11; font.family: "Menlo"; font.letterSpacing: 3; font.weight: Font.DemiBold }
                Text { text: "ОПЕРАТОРСКАЯ СТАНЦИЯ"; color: "#3A5060"; font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 1.2 }
            }

            Rectangle { width: 1; height: 24; color: Qt.rgba(1,1,1,0.08); anchors.verticalCenter: parent.verticalCenter }

            // Mode pills
            Row {
                spacing: 3; anchors.verticalCenter: parent.verticalCenter
                Repeater {
                    model: [
                        {lbl:"ЭО", mode:"ДЕНЬ", hex:"#6B9EC2"},
                        {lbl:"НВ", mode:"НОЧЬ", hex:"#4EA87A"},
                        {lbl:"ИК", mode:"ИК",   hex:"#C2845A"},
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        width: 36; height: 24; radius: 5
                        property bool on: root.currentMode === modelData.mode
                        property color ac: modelData.hex
                        color: on ? Qt.rgba(ac.r, ac.g, ac.b, 0.22) : "transparent"
                        border.color: on ? Qt.rgba(ac.r, ac.g, ac.b, 0.60) : Qt.rgba(1,1,1,0.10)
                        border.width: 1
                        Text { anchors.centerIn: parent; text: modelData.lbl
                               color: parent.on ? parent.ac : "#5A6E7E"
                               font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 0.5; font.weight: Font.Normal }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.modeChanged(modelData.mode) }
                    }
                }
            }

            Rectangle { width: 1; height: 24; color: Qt.rgba(1,1,1,0.08); anchors.verticalCenter: parent.verticalCenter }

            // Active target
            Row { spacing: 7; anchors.verticalCenter: parent.verticalCenter; visible: root.isRunning
                Rectangle { width: 6; height: 6; radius: 3; color: "#52D273"; anchors.verticalCenter: parent.verticalCenter
                    SequentialAnimation on opacity { running: root.isRunning; loops: Animation.Infinite
                        NumberAnimation { to: 0.3; duration: 800 }
                        NumberAnimation { to: 1.0; duration: 800 }
                    }
                }
                Text { text: "ЦЕЛЬ  T-" + (root.targetId < 10 ? "0" : "") + root.targetId
                       color: "#8FA4B8"; font.pixelSize: 10; font.family: "Menlo"
                       font.letterSpacing: 0.8; anchors.verticalCenter: parent.verticalCenter }
            }
        }
    }

    // ── MENU content (replaces normal when _menuOpen) ────────────────
    Item {
        id: menuContent
        anchors.left:  parent.left;  anchors.leftMargin:  10
        anchors.top:   parent.top;   anchors.bottom: parent.bottom
        anchors.right: rightArea.left
        opacity: root._menuOpen ? 1 : 0
        visible: opacity > 0.01
        Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

        Row {
            anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
            spacing: 10

            // Close / back button
            Rectangle {
                width: 32; height: 32; radius: 6
                anchors.verticalCenter: parent.verticalCenter
                color: closeMa.containsMouse ? Qt.rgba(1,1,1,0.09) : "transparent"
                border.color: Qt.rgba(1,1,1,0.12); border.width: 1
                Text { anchors.centerIn: parent; text: "✕"; color: closeMa.containsMouse ? "#E6ECF3" : "#5A7080"
                       font.pixelSize: 12; font.family: "Menlo" }
                MouseArea { id: closeMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: root._menuOpen = false }
            }

            Rectangle { width: 1; height: 24; color: Qt.rgba(1,1,1,0.08); anchors.verticalCenter: parent.verticalCenter }

            Text { text: "МЕНЮ"; color: "#3A5060"; font.pixelSize: 9; font.family: "Menlo"
                   font.letterSpacing: 2.5; anchors.verticalCenter: parent.verticalCenter }

            Rectangle { width: 1; height: 24; color: Qt.rgba(1,1,1,0.08); anchors.verticalCenter: parent.verticalCenter }

            // Nav items
            Repeater {
                model: [
                    { lbl: "TARGET LAB",  desc: "Цели/обучение",    accent: "#E8B547" },
                    { lbl: "ЭКСПЕРТ",     desc: "Расш. параметры",  accent: "#8FA4B8" },
                    { lbl: "КАЛИБРОВКА",  desc: "Гимбал",           accent: "#8FA4B8" },
                    { lbl: "ДИАГНОСТИКА", desc: "Система",          accent: "#8FA4B8" },
                    { lbl: "НАСТРОЙКИ",   desc: "Конфигурация",     accent: "#8FA4B8" },
                    { lbl: "О СИСТЕМЕ",   desc: "Версия",           accent: "#8FA4B8" },
                ]
                delegate: Rectangle {
                    required property var modelData
                    anchors.verticalCenter: parent.verticalCenter
                    width: navLbl.implicitWidth + 46; height: 32; radius: 7
                    color: navMa.containsMouse ? Qt.rgba(1,1,1,0.09) : "transparent"
                    border.color: navMa.containsMouse ? Qt.rgba(0.561,0.643,0.722,0.40) : Qt.rgba(1,1,1,0.09)
                    border.width: 1

                    Column {
                        anchors.centerIn: parent; spacing: 1
                        Text { id: navLbl; text: modelData.lbl; color: modelData.accent
                               font.pixelSize: 10; font.family: "Menlo"
                               font.letterSpacing: 0.8; font.weight: Font.Normal
                               anchors.horizontalCenter: parent.horizontalCenter }
                        Text { text: modelData.desc; color: "#3A5060"
                               font.pixelSize: 8; font.family: "Menlo"
                               anchors.horizontalCenter: parent.horizontalCenter }
                    }

                    MouseArea { id: navMa; anchors.fill: parent; hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root._menuOpen = false
                                    if      (modelData.lbl === "TARGET LAB")  root.targetLabRequested()
                                    else if (modelData.lbl === "ЭКСПЕРТ")     root.expertRequested()
                                    else if (modelData.lbl === "КАЛИБРОВКА")  root.calibRequested()
                                    else if (modelData.lbl === "ДИАГНОСТИКА") root.diagRequested()
                                    else if (modelData.lbl === "НАСТРОЙКИ")   root.settingsRequested()
                                    else if (modelData.lbl === "О СИСТЕМЕ")   root.aboutRequested()
                                }
                    }
                }
            }
        }
    }
}
