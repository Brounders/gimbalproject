import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: Qt.rgba(0, 0, 0, 0.72)

    signal closed()

    property int _step: 0

    MouseArea { anchors.fill: parent; onClicked: root.closed() }

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(640, parent.width - 80)
        height: Math.min(480, parent.height - 80)
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
                        Text { text: "КАЛИБРОВКА"; color: "#E6ECF3"; font.pixelSize: 12; font.family: "Menlo"; font.letterSpacing: 1.5 }
                        Text { text: "Мастер настройки гимбала"; color: "#3A5060"; font.pixelSize: 9; font.family: "Menlo" }
                    }
                    Item { Layout.fillWidth: true }
                    // Step dots
                    Row { spacing: 8; Layout.alignment: Qt.AlignVCenter
                        Repeater { model: 4; delegate: Rectangle {
                            required property int index
                            width: 8; height: 8; radius: 4
                            color: index <= root._step ? "#52D273" : "#1C2A38"
                            border.color: index === root._step ? "#52D273" : "#2A3A4A"; border.width: 1
                            Behavior on color { ColorAnimation { duration: 300 } }
                        }}
                    }
                    Item { width: 12 }
                    Rectangle {
                        width: 72; height: 28; radius: 6; color: "transparent"
                        border.color: Qt.rgba(0.886,0.420,0.420,0.35); border.width: 1
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.closed() }
                        Text { anchors.centerIn: parent; text: "ЗАКРЫТЬ"; color: "#E26B6B"
                               font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1 }
                    }
                }
            }

            // Content area
            Item {
                Layout.fillWidth: true; Layout.fillHeight: true

                // Step 0 — Подготовка
                Column {
                    anchors.centerIn: parent; spacing: 24; visible: root._step === 0
                    width: parent.width * 0.65

                    Rectangle {
                        width: 72; height: 72; radius: 36; color: "#0A1018"
                        anchors.horizontalCenter: parent.horizontalCenter
                        border.color: "#2A4A3A"; border.width: 2
                        Text { anchors.centerIn: parent; text: "⚙"; font.pixelSize: 32; color: "#3A6A5A" }
                    }
                    Text { text: "Подготовка"; color: "#8FA4B8"; font.pixelSize: 18; font.family: "Menlo"
                           horizontalAlignment: Text.AlignHCenter; width: parent.width }
                    Text {
                        text: "Убедитесь, что гимбал установлен горизонтально.\nОтключите питание моторов перед началом калибровки."
                        color: "#6F7E8E"; font.pixelSize: 11; font.family: "Menlo"
                        wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter; width: parent.width
                    }
                }

                // Step 1 — Обнуление
                Column {
                    anchors.centerIn: parent; spacing: 24; visible: root._step === 1
                    width: parent.width * 0.65

                    Rectangle {
                        width: 72; height: 72; radius: 36; color: "#0A1018"
                        anchors.horizontalCenter: parent.horizontalCenter
                        border.color: "#2A3A5A"; border.width: 2
                        Text { anchors.centerIn: parent; text: "↻"; font.pixelSize: 36; color: "#3A5A8A"
                               NumberAnimation on rotation { from: 0; to: 360; duration: 1200; loops: Animation.Infinite; running: root._step === 1 } }
                    }
                    Text { text: "Обнуление осей"; color: "#8FA4B8"; font.pixelSize: 18; font.family: "Menlo"
                           horizontalAlignment: Text.AlignHCenter; width: parent.width }
                    Text {
                        text: "Система обнуляет все оси гимбала.\nПожалуйста, не двигайте устройство во время процедуры."
                        color: "#6F7E8E"; font.pixelSize: 11; font.family: "Menlo"
                        wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter; width: parent.width
                    }
                }

                // Step 2 — Юстировка
                Column {
                    anchors.centerIn: parent; spacing: 24; visible: root._step === 2
                    width: parent.width * 0.65

                    Rectangle {
                        width: 72; height: 72; radius: 36; color: "#0A1018"
                        anchors.horizontalCenter: parent.horizontalCenter
                        border.color: "#4A4A2A"; border.width: 2
                        Text { anchors.centerIn: parent; text: "◎"; font.pixelSize: 32; color: "#8A8A3A" }
                    }
                    Text { text: "Юстировка камеры"; color: "#8FA4B8"; font.pixelSize: 18; font.family: "Menlo"
                           horizontalAlignment: Text.AlignHCenter; width: parent.width }
                    Text {
                        text: "Наведите камеру на калибровочную мишень.\nЦентр перекрестия должен совпасть с маркером."
                        color: "#6F7E8E"; font.pixelSize: 11; font.family: "Menlo"
                        wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter; width: parent.width
                    }
                }

                // Step 3 — Завершено
                Column {
                    anchors.centerIn: parent; spacing: 24; visible: root._step === 3
                    width: parent.width * 0.65

                    Rectangle {
                        width: 72; height: 72; radius: 36; color: "#0A1A0A"
                        anchors.horizontalCenter: parent.horizontalCenter
                        border.color: "#2A5A2A"; border.width: 2
                        Text { anchors.centerIn: parent; text: "✓"; font.pixelSize: 32; color: "#52D273" }
                    }
                    Text { text: "Калибровка завершена"; color: "#52D273"; font.pixelSize: 18; font.family: "Menlo"
                           horizontalAlignment: Text.AlignHCenter; width: parent.width }
                    Text {
                        text: "Все параметры сохранены.\nГимбал готов к работе."
                        color: "#6F7E8E"; font.pixelSize: 11; font.family: "Menlo"
                        wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter; width: parent.width
                    }
                }
            }

            // Footer nav
            Rectangle {
                Layout.fillWidth: true; height: 58; color: "#080D12"
                Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: "#1C2A38" }
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 20

                    Rectangle {
                        width: 100; height: 34; radius: 6; color: "transparent"; visible: root._step > 0
                        border.color: Qt.rgba(1,1,1,0.12); border.width: 1
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    onClicked: if (root._step > 0) root._step-- }
                        Text { anchors.centerIn: parent; text: "НАЗАД"; color: "#5A7080"
                               font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1 }
                    }
                    Item { Layout.fillWidth: true }
                    Text { text: "Шаг " + (root._step + 1) + " из 4"; color: "#3A5060"
                           font.pixelSize: 10; font.family: "Menlo" }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                        width: 120; height: 34; radius: 6
                        color: root._step < 3 ? Qt.rgba(0.322,0.827,0.451,0.10) : Qt.rgba(0.322,0.827,0.451,0.18)
                        border.color: Qt.rgba(0.322,0.827,0.451,0.38); border.width: 1
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    onClicked: { if (root._step < 3) root._step++; else { root._step = 0; root.closed() } } }
                        Text { anchors.centerIn: parent; text: root._step < 3 ? "ДАЛЕЕ" : "ГОТОВО"; color: "#52D273"
                               font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1; font.weight: Font.DemiBold }
                    }
                }
            }
        }
    }
}
