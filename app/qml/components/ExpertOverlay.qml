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
                        Text { text: "ЭКСПЕРТ"; color: "#E6ECF3"; font.pixelSize: 12; font.family: "Menlo"; font.letterSpacing: 1.5 }
                        Text { text: "Расширенные параметры детектора"; color: "#3A5060"; font.pixelSize: 9; font.family: "Menlo" }
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

            // Param grid
            GridLayout {
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.margins: 16; Layout.topMargin: 18
                columns: 2; columnSpacing: 12; rowSpacing: 10

                Repeater {
                    model: [
                        {lbl:"IOU threshold",         val:"0.45", cat:"YOLO",  clr:"#6B9EC2"},
                        {lbl:"NMS conf threshold",    val:"0.35", cat:"YOLO",  clr:"#6B9EC2"},
                        {lbl:"Max detections",        val:"10",   cat:"YOLO",  clr:"#6B9EC2"},
                        {lbl:"Input resolution",      val:"640",  cat:"YOLO",  clr:"#6B9EC2"},
                        {lbl:"MOG2 history",          val:"200",  cat:"НОЧЬ",  clr:"#4EA87A"},
                        {lbl:"MOG2 varThreshold",     val:"25",   cat:"НОЧЬ",  clr:"#4EA87A"},
                        {lbl:"Night confirm frames",  val:"5",    cat:"НОЧЬ",  clr:"#4EA87A"},
                        {lbl:"Night min area (px²)",  val:"80",   cat:"НОЧЬ",  clr:"#4EA87A"},
                        {lbl:"Lock hysteresis",       val:"0.12", cat:"LOCK",  clr:"#52D273"},
                        {lbl:"Reacquire timeout (s)", val:"3.0",  cat:"LOCK",  clr:"#52D273"},
                        {lbl:"Budget controller",     val:"AUTO", cat:"ПРОЦ.", clr:"#8FA4B8"},
                        {lbl:"ROI padding factor",    val:"1.5",  cat:"ПРОЦ.", clr:"#8FA4B8"},
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true; height: 58; radius: 8
                        color: "#0A1018"; border.color: Qt.rgba(1,1,1,0.06); border.width: 1

                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12; spacing: 8
                            Column {
                                spacing: 4; Layout.fillWidth: true
                                Rectangle {
                                    height: 16; width: catLbl.implicitWidth + 12; radius: 3
                                    color: Qt.rgba(modelData.clr === "#6B9EC2" ? 0.419 : modelData.clr === "#4EA87A" ? 0.306 : modelData.clr === "#52D273" ? 0.322 : 0.561,
                                                   modelData.clr === "#6B9EC2" ? 0.620 : modelData.clr === "#4EA87A" ? 0.659 : modelData.clr === "#52D273" ? 0.827 : 0.643,
                                                   modelData.clr === "#6B9EC2" ? 0.761 : modelData.clr === "#4EA87A" ? 0.478 : modelData.clr === "#52D273" ? 0.451 : 0.722,
                                                   0.12)
                                    Text { id: catLbl; anchors.centerIn: parent; text: modelData.cat; color: modelData.clr
                                           font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 1 }
                                }
                                Text { text: modelData.lbl; color: "#6F7E8E"; font.pixelSize: 10; font.family: "Menlo" }
                            }
                            Text { text: modelData.val; color: "#E8B547"
                                   font.pixelSize: 15; font.family: "Menlo"; font.weight: Font.DemiBold }
                        }
                    }
                }
            }

            // Footer warning
            Rectangle {
                Layout.fillWidth: true; height: 38; color: Qt.rgba(0.910,0.714,0.279,0.05)
                Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: "#1C2A38" }
                Text {
                    anchors.centerIn: parent
                    text: "⚠  Изменения вступят в силу при следующем запуске трекинга"
                    color: "#6A5A30"; font.pixelSize: 10; font.family: "Menlo"
                }
            }
        }
    }
}
