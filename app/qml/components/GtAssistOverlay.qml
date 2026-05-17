import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: "#0C1219"
    focus: visible

    signal closed()

    property point dragStart: Qt.point(0, 0)
    property point dragEnd: Qt.point(0, 0)
    property bool dragging: false
    property bool embedded: false

    Keys.onEscapePressed: root.closed()

    function bboxArray() {
        if (!gtAssistBridge) return []
        try { return JSON.parse(gtAssistBridge.selectedBboxJson) }
        catch (e) { return [] }
    }

    function frameRect() {
        var fw = gtAssistBridge ? gtAssistBridge.frameWidth : 0
        var fh = gtAssistBridge ? gtAssistBridge.frameHeight : 0
        var margin = 18
        var availW = Math.max(1, videoPane.width - margin * 2)
        var availH = Math.max(1, videoPane.height - margin * 2)
        if (fw <= 0 || fh <= 0) return Qt.rect(margin, margin, availW, availH)
        var scale = Math.min(availW / fw, availH / fh)
        var w = fw * scale
        var h = fh * scale
        return Qt.rect(margin + (availW - w) / 2, margin + (availH - h) / 2, w, h)
    }

    function frameToViewX(x) {
        var r = frameRect()
        var fw = gtAssistBridge ? gtAssistBridge.frameWidth : 1
        return r.x + x * r.width / Math.max(1, fw)
    }

    function frameToViewY(y) {
        var r = frameRect()
        var fh = gtAssistBridge ? gtAssistBridge.frameHeight : 1
        return r.y + y * r.height / Math.max(1, fh)
    }

    function viewToFrameX(x) {
        var r = frameRect()
        var fw = gtAssistBridge ? gtAssistBridge.frameWidth : 0
        return Math.round((x - r.x) * fw / Math.max(1, r.width))
    }

    function viewToFrameY(y) {
        var r = frameRect()
        var fh = gtAssistBridge ? gtAssistBridge.frameHeight : 0
        return Math.round((y - r.y) * fh / Math.max(1, r.height))
    }

    function saveDragBbox() {
        var r = frameRect()
        var x1v = Math.max(r.x, Math.min(root.dragStart.x, root.dragEnd.x))
        var y1v = Math.max(r.y, Math.min(root.dragStart.y, root.dragEnd.y))
        var x2v = Math.min(r.x + r.width, Math.max(root.dragStart.x, root.dragEnd.x))
        var y2v = Math.min(r.y + r.height, Math.max(root.dragStart.y, root.dragEnd.y))
        if (x2v - x1v < 8 || y2v - y1v < 8) return
        gtAssistBridge.setBbox(root.viewToFrameX(x1v), root.viewToFrameY(y1v), root.viewToFrameX(x2v), root.viewToFrameY(y2v))
        gtAssistBridge.nextFrame()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            height: root.embedded ? 0 : 52
            visible: !root.embedded
            color: "#0A0F14"
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#1C2A38" }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 12

                ColumnLayout {
                    spacing: 1
                    Layout.preferredWidth: 360
                    Text { text: "GT ASSIST"; color: "#E8B547"; font.pixelSize: 12; font.family: "Menlo"; font.letterSpacing: 2.8 }
                    Text { text: "полуавтоматическая разметка bbox для tracking diagnostics"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo" }
                }

                Text {
                    Layout.fillWidth: true
                    text: gtAssistBridge ? gtAssistBridge.statusText : "bridge недоступен"
                    color: "#8FA4B8"
                    font.pixelSize: 11
                    font.family: "Menlo"
                    elide: Text.ElideRight
                }

                Rectangle {
                    width: 34; height: 32; radius: 6
                    color: closeMa.containsMouse ? Qt.rgba(1,1,1,0.09) : "transparent"
                    border.color: Qt.rgba(1,1,1,0.13)
                    Text { anchors.centerIn: parent; text: "✕"; color: closeMa.containsMouse ? "#E6ECF3" : "#5A7080"; font.pixelSize: 12; font.family: "Menlo" }
                    MouseArea { id: closeMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.closed() }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.preferredWidth: 286
                Layout.fillHeight: true
                color: "#0A0F14"
                Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: "#1C2A38" }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 10

                    GtButton {
                        label: "ОТКРЫТЬ ВИДЕО"
                        accent: "#8FA4B8"
                        onClicked: {
                            var p = gtAssistBridge ? gtAssistBridge.browseVideoFile() : ""
                            if (p !== "") gtAssistBridge.openVideo(p)
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 74
                        radius: 8
                        color: Qt.rgba(1,1,1,0.035)
                        border.color: "#1C2A38"
                        Column {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 6
                            Text { text: gtAssistBridge && gtAssistBridge.sourceName !== "" ? gtAssistBridge.sourceName : "Видео не открыто"; color: "#D5DEE8"; font.pixelSize: 11; font.family: "Menlo"; elide: Text.ElideRight; width: parent.width }
                            Text { text: gtAssistBridge ? ("F " + gtAssistBridge.frameIndex + " / " + Math.max(0, gtAssistBridge.frameCount - 1)) : "F —"; color: "#8FA4B8"; font.pixelSize: 10; font.family: "Menlo" }
                            Text { text: gtAssistBridge ? (gtAssistBridge.frameWidth + "×" + gtAssistBridge.frameHeight + " · rows " + gtAssistBridge.rowCount) : "—"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo" }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        GtButton { Layout.fillWidth: true; label: "←"; accent: "#8FA4B8"; enabled: gtAssistBridge && gtAssistBridge.hasSource; onClicked: gtAssistBridge.prevFrame() }
                        GtButton { Layout.fillWidth: true; label: "→"; accent: "#8FA4B8"; enabled: gtAssistBridge && gtAssistBridge.hasSource; onClicked: gtAssistBridge.nextFrame() }
                    }

                    GtButton {
                        label: "ЦЕЛЬ НЕ ВИДНА"
                        accent: "#E26B6B"
                        enabled: gtAssistBridge && gtAssistBridge.hasSource
                        onClicked: gtAssistBridge.markInvisible()
                    }

                    GtButton {
                        label: "ПРОТЯНУТЬ 10 КАДРОВ"
                        accent: "#52D273"
                        enabled: gtAssistBridge && gtAssistBridge.hasBbox
                        onClicked: gtAssistBridge.propagate(10)
                    }

                    GtButton {
                        label: "ОЧИСТИТЬ КАДР"
                        accent: "#E8B547"
                        enabled: gtAssistBridge && gtAssistBridge.hasSource
                        onClicked: gtAssistBridge.clearCurrent()
                    }

                    GtButton {
                        label: "ЭКСПОРТ CSV"
                        accent: "#64B5F6"
                        enabled: gtAssistBridge && gtAssistBridge.rowCount > 0
                        onClicked: gtAssistBridge.exportCsv()
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#1C2A38"
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Порядок: открыть видео → drag на цель → протянуть → поправить при сбое → экспорт. Разметка не влияет на трекер и обучение."
                        color: "#4A5E6E"
                        font.pixelSize: 10
                        font.family: "Menlo"
                        wrapMode: Text.WordWrap
                    }

                    Text {
                        Layout.fillWidth: true
                        text: gtAssistBridge && gtAssistBridge.exportPath !== "" ? ("CSV: " + gtAssistBridge.exportPath) : ""
                        color: "#64B5F6"
                        font.pixelSize: 10
                        font.family: "Menlo"
                        wrapMode: Text.WrapAnywhere
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            Rectangle {
                id: videoPane
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#050810"
                clip: true

                Image {
                    anchors.fill: parent
                    anchors.margins: 18
                    source: gtAssistBridge ? gtAssistBridge.previewSource : ""
                    fillMode: Image.PreserveAspectFit
                    cache: false
                    asynchronous: false
                    visible: gtAssistBridge && gtAssistBridge.hasSource
                }

                Text {
                    anchors.centerIn: parent
                    visible: !(gtAssistBridge && gtAssistBridge.hasSource)
                    text: "ОТКРОЙТЕ ВИДЕО ДЛЯ РАЗМЕТКИ"
                    color: Qt.rgba(0.561,0.643,0.722,0.16)
                    font.pixelSize: 24
                    font.family: "Menlo"
                    font.letterSpacing: 5
                }

                Rectangle {
                    visible: bboxArray().length >= 4
                    x: bboxArray().length >= 4 ? root.frameToViewX(bboxArray()[0]) : 0
                    y: bboxArray().length >= 4 ? root.frameToViewY(bboxArray()[1]) : 0
                    width: bboxArray().length >= 4 ? root.frameToViewX(bboxArray()[2]) - x : 0
                    height: bboxArray().length >= 4 ? root.frameToViewY(bboxArray()[3]) - y : 0
                    color: "transparent"
                    border.color: "#52D273"
                    border.width: 2
                }

                Rectangle {
                    visible: root.dragging
                    x: Math.min(root.dragStart.x, root.dragEnd.x)
                    y: Math.min(root.dragStart.y, root.dragEnd.y)
                    width: Math.abs(root.dragEnd.x - root.dragStart.x)
                    height: Math.abs(root.dragEnd.y - root.dragStart.y)
                    color: Qt.rgba(0.910,0.710,0.280,0.10)
                    border.color: "#E8B547"
                    border.width: 2
                }

                MouseArea {
                    anchors.fill: parent
                    enabled: gtAssistBridge && gtAssistBridge.hasSource
                    hoverEnabled: true
                    cursorShape: Qt.CrossCursor
                    onPressed: function(mouse) {
                        root.dragStart = Qt.point(mouse.x, mouse.y)
                        root.dragEnd = root.dragStart
                        root.dragging = true
                    }
                    onPositionChanged: function(mouse) {
                        if (root.dragging) root.dragEnd = Qt.point(mouse.x, mouse.y)
                    }
                    onReleased: function(mouse) {
                        root.dragEnd = Qt.point(mouse.x, mouse.y)
                        root.dragging = false
                        root.saveDragBbox()
                    }
                }
            }
        }
    }

    component GtButton: Rectangle {
        id: btn
        property string label: ""
        property color accent: "#8FA4B8"
        signal clicked()
        Layout.fillWidth: true
        height: 36
        radius: 7
        opacity: enabled ? 1.0 : 0.32
        color: ma.containsMouse && enabled ? Qt.rgba(1,1,1,0.065) : Qt.rgba(1,1,1,0.025)
        border.color: enabled ? accent : Qt.rgba(1,1,1,0.12)
        border.width: 1
        Text {
            anchors.centerIn: parent
            text: btn.label
            color: btn.accent
            font.pixelSize: 10
            font.family: "Menlo"
            font.letterSpacing: 1.2
        }
        MouseArea {
            id: ma
            anchors.fill: parent
            enabled: btn.enabled
            hoverEnabled: true
            cursorShape: btn.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: btn.clicked()
        }
    }
}
