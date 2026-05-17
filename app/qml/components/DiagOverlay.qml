import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: Qt.rgba(0, 0, 0, 0.72)

    signal closed()

    MouseArea { anchors.fill: parent; onClicked: root.closed() }

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(760, parent.width - 80)
        height: Math.min(560, parent.height - 80)
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
                    Column { spacing: 2
                        Text { text: "ДИАГНОСТИКА"; color: "#E6ECF3"; font.pixelSize: 12; font.family: "Menlo"; font.letterSpacing: 1.5 }
                        Text { text: "Состояние компонентов системы"; color: "#3A5060"; font.pixelSize: 9; font.family: "Menlo" }
                    }
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

            // Status grid
            GridLayout {
                Layout.fillWidth: true; Layout.margins: 16; Layout.topMargin: 18; Layout.bottomMargin: 0
                columns: 3; columnSpacing: 10; rowSpacing: 10

                Repeater {
                    model: [
                        {lbl:"ДЕТЕКТОР",     status:"OK",   val:"YOLOv8n",  color:"#52D273"},
                        {lbl:"НОЧНОЙ ДЕТ.", status:"OK",   val:"MOG2",     color:"#52D273"},
                        {lbl:"LOCK TRACKER", status:"OK",   val:"Template", color:"#52D273"},
                        {lbl:"GIMBAL CTL",   status:"IDLE", val:"—",        color:"#8FA4B8"},
                        {lbl:"ВИДЕО ПОТОК",  status:"IDLE", val:"—",        color:"#8FA4B8"},
                        {lbl:"ЗАПИСЬ",       status:"IDLE", val:"—",        color:"#8FA4B8"},
                        {lbl:"GPU / MPS",    status:"OK",   val:"M1",       color:"#52D273"},
                        {lbl:"ПАМЯТЬ",       status:"OK",   val:"2.1 ГБ",   color:"#52D273"},
                        {lbl:"ХРАНИЛИЩЕ",    status:"WARN", val:"82%",      color:"#E8B547"},
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true; height: 62; radius: 8
                        color: "#0A1018"; border.color: Qt.rgba(1,1,1,0.06); border.width: 1

                        Column {
                            anchors.left: parent.left; anchors.right: parent.right
                            anchors.margins: 12; anchors.verticalCenter: parent.verticalCenter
                            spacing: 6
                            Text { text: modelData.lbl; color: "#4A5E6E"; font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 1.5 }
                            Row { spacing: 6
                                Rectangle { width: 6; height: 6; radius: 3; color: modelData.color; anchors.verticalCenter: parent.verticalCenter }
                                Text { text: modelData.status; color: modelData.color; font.pixelSize: 11; font.family: "Menlo"; font.weight: Font.DemiBold; anchors.verticalCenter: parent.verticalCenter }
                                Text { text: "·"; color: "#2A3A4A"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                                Text { text: modelData.val; color: "#6F7E8E"; font.pixelSize: 11; font.family: "Menlo"; anchors.verticalCenter: parent.verticalCenter }
                            }
                        }
                    }
                }
            }

            // System log
            Rectangle {
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.leftMargin: 16; Layout.rightMargin: 16; Layout.bottomMargin: 16; Layout.topMargin: 12
                color: "#050A0F"; radius: 8; clip: true
                border.color: "#131E2A"; border.width: 1

                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 12; spacing: 6

                    Text { text: "ЖУРНАЛ СИСТЕМЫ"; color: "#2A3A4A"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 2 }

                    Repeater {
                        model: [
                            {t:"08:41:02", msg:"Система инициализирована",        lvl:"info"},
                            {t:"08:41:03", msg:"YOLOv8n загружена · 14.2 мс",     lvl:"ok"},
                            {t:"08:41:03", msg:"MOG2 инициализирован",            lvl:"ok"},
                            {t:"08:41:04", msg:"Budget controller: AUTO",         lvl:"info"},
                            {t:"08:41:04", msg:"Готов к работе",                  lvl:"ok"},
                        ]
                        delegate: Row {
                            required property var modelData; spacing: 12
                            Text { text: modelData.t; color: "#2A3A4A"; font.pixelSize: 10; font.family: "Menlo" }
                            Text {
                                text: modelData.msg; font.pixelSize: 10; font.family: "Menlo"
                                color: modelData.lvl === "ok" ? "#3A6A4A" : "#3A4A5A"
                            }
                        }
                    }
                }
            }
        }
    }
}
