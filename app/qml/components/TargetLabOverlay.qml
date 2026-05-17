import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: "#070B10"
    focus: visible

    signal closed()

    property int activeView: 0

    Keys.onEscapePressed: root.closed()
    onVisibleChanged: if (visible && targetLabBridge) targetLabBridge.refresh()

    function materialCards() {
        if (!targetLabBridge) return []
        try { return JSON.parse(targetLabBridge.materialCardsJson) }
        catch (e) { return [] }
    }

    function checkCards() {
        if (!targetLabBridge) return []
        try { return JSON.parse(targetLabBridge.checkCardsJson) }
        catch (e) { return [] }
    }

    function toneColor(tone) {
        var v = (tone || "idle").toLowerCase()
        if (v === "success") return "#52D273"
        if (v === "warn") return "#E8B547"
        if (v === "error") return "#E26B6B"
        if (v === "progress") return "#64B5F6"
        return "#8FA4B8"
    }

    function toneFill(tone) {
        var v = (tone || "idle").toLowerCase()
        if (v === "success") return Qt.rgba(0.322, 0.824, 0.451, 0.11)
        if (v === "warn") return Qt.rgba(0.910, 0.710, 0.280, 0.13)
        if (v === "error") return Qt.rgba(0.886, 0.420, 0.420, 0.12)
        if (v === "progress") return Qt.rgba(0.392, 0.710, 0.965, 0.12)
        return Qt.rgba(0.561, 0.643, 0.722, 0.075)
    }

    function runPrimaryAction() {
        if (!targetLabBridge) return
        var label = targetLabBridge.primaryActionLabel
        if (label === "РАЗМЕТИТЬ ВИДЕО") {
            root.activeView = 1
        } else if (label === "ПРОВЕРИТЬ ТРЕКЕР") {
            targetLabBridge.runGtDiagnostics()
        } else {
            root.activeView = 2
        }
    }

    function sceneLabel(scene) {
        var s = scene || ""
        if (s === "UNKNOWN") return "ДРУГОЕ"
        return s
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            height: 64
            color: "#090F15"
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#1C2A38" }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 14
                spacing: 14

                ColumnLayout {
                    Layout.preferredWidth: 340
                    spacing: 2
                    Text {
                        text: "TARGET LAB"
                        color: "#E8B547"
                        font.pixelSize: 14
                        font.family: "Menlo"
                        font.letterSpacing: 2.4
                    }
                    Text {
                        text: "материал учит · проверка отвечает · решение ведёт дальше"
                        color: "#4A5E6E"
                        font.pixelSize: 10
                        font.family: "Menlo"
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 34
                    radius: 8
                    color: root.toneFill(targetLabBridge ? targetLabBridge.nextActionTone : "idle")
                    border.color: root.toneColor(targetLabBridge ? targetLabBridge.nextActionTone : "idle")
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 10
                        Text {
                            text: targetLabBridge ? targetLabBridge.nextActionTitle : "Target Lab"
                            color: root.toneColor(targetLabBridge ? targetLabBridge.nextActionTone : "idle")
                            font.pixelSize: 12
                            font.family: "Menlo"
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: targetLabBridge ? targetLabBridge.nextActionBody : ""
                            color: "#D5DEE8"
                            font.pixelSize: 10
                            font.family: "Menlo"
                            elide: Text.ElideRight
                        }
                    }
                }

                HeaderButton { label: "⟳"; width: 34; accent: "#8FA4B8"; onClicked: { if (targetLabBridge) targetLabBridge.refresh(); if (dtsBridge) dtsBridge.reload() } }
                HeaderButton { label: "ЗАКРЫТЬ"; width: 78; accent: "#E26B6B"; onClicked: root.closed() }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.preferredWidth: 236
                Layout.fillHeight: true
                color: "#090F15"
                Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: "#1C2A38" }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 10

                    Text { text: "ЦИКЛ"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 2 }
                    StepNav { number: "1"; title: "Материал"; detail: targetLabBridge ? targetLabBridge.materialTitle : "—"; active: root.activeView === 0; onClicked: root.activeView = 0 }
                    StepNav { number: "2"; title: "Проверка"; detail: targetLabBridge ? targetLabBridge.checkTitle : "—"; active: root.activeView === 0; onClicked: root.activeView = 0 }
                    StepNav { number: "3"; title: "Улучшение"; detail: dtsBridge ? dtsBridge.candidateStatusLabel : "—"; active: root.activeView === 2; onClicked: root.activeView = 2 }

                    Rectangle { Layout.fillWidth: true; height: 1; color: "#1C2A38"; Layout.topMargin: 4; Layout.bottomMargin: 2 }

                    SideButton { label: "РАЗМЕТИТЬ"; detail: "видео / GT"; accent: "#64B5F6"; active: root.activeView === 1; onClicked: root.activeView = 1 }
                    SideButton { label: "РАЗОБРАТЬ"; detail: "клики / DTS"; accent: "#52D273"; active: root.activeView === 2; onClicked: root.activeView = 2 }
                    SideButton { label: "ДЕТАЛИ"; detail: "логи / файлы"; accent: "#8FA4B8"; active: root.activeView === 3; onClicked: root.activeView = 3 }

                    Item { Layout.fillHeight: true }

                    ActionButton {
                        Layout.fillWidth: true
                        label: targetLabBridge ? targetLabBridge.primaryActionLabel : "ГОТОВО"
                        accent: root.toneColor(targetLabBridge ? targetLabBridge.nextActionTone : "idle")
                        enabled: !(targetLabBridge && targetLabBridge.gtDiagnosticsRunning)
                        onClicked: root.runPrimaryAction()
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#080D12"
                clip: true

                Flickable {
                    anchors.fill: parent
                    visible: root.activeView === 0
                    contentWidth: width
                    contentHeight: dashboardCol.implicitHeight + 44
                    clip: true
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    ColumnLayout {
                        id: dashboardCol
                        width: parent.width
                        anchors.margins: 22
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        spacing: 16

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 16

                            BigCard {
                                Layout.fillWidth: true
                                title: "МАТЕРИАЛ"
                                value: targetLabBridge ? targetLabBridge.materialTitle : "0 клипов · 0 кадров"
                                subtitle: targetLabBridge ? targetLabBridge.materialSubtitle : "материал не собран"
                                accent: "#64B5F6"
                                Repeater {
                                    model: root.materialCards()
                                    delegate: ScenePill {
                                        required property var modelData
                                        scene: root.sceneLabel(modelData.scene)
                                        main: modelData.clips + " клип · " + modelData.frames + " кадров"
                                        note: modelData.role
                                        accent: modelData.scene.indexOf("NEGATIVE") >= 0 ? "#E8B547" : "#64B5F6"
                                    }
                                }
                            }

                            BigCard {
                                Layout.fillWidth: true
                                title: "ПРОВЕРКА ТРЕКЕРА"
                                value: targetLabBridge ? targetLabBridge.checkTitle : "не запускалась"
                                subtitle: targetLabBridge ? targetLabBridge.checkSubtitle : ""
                                accent: "#E8B547"
                                Repeater {
                                    model: root.checkCards()
                                    delegate: CheckPill {
                                        required property var modelData
                                        scene: root.sceneLabel(modelData.scene)
                                        recall: modelData.recall_pct
                                        falseLock: modelData.false_lock_pct
                                        fps: modelData.fps
                                        status: modelData.status
                                        tone: modelData.tone
                                    }
                                }
                                Text {
                                    visible: root.checkCards().length === 0
                                    text: "Нажмите «Проверить трекер», чтобы увидеть короткую оценку по сценам."
                                    color: "#4A5E6E"
                                    font.pixelSize: 11
                                    font.family: "Menlo"
                                    wrapMode: Text.Wrap
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: decisionCol.implicitHeight + 30
                            radius: 10
                            color: root.toneFill(targetLabBridge ? targetLabBridge.nextActionTone : "idle")
                            border.color: root.toneColor(targetLabBridge ? targetLabBridge.nextActionTone : "idle")
                            border.width: 1

                            ColumnLayout {
                                id: decisionCol
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 12

                                Text {
                                    text: "РЕШЕНИЕ"
                                    color: root.toneColor(targetLabBridge ? targetLabBridge.nextActionTone : "idle")
                                    font.pixelSize: 11
                                    font.family: "Menlo"
                                    font.letterSpacing: 2
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: targetLabBridge ? targetLabBridge.nextActionTitle : "—"
                                    color: "#E6ECF3"
                                    font.pixelSize: 28
                                    font.family: "Menlo"
                                    font.bold: true
                                    elide: Text.ElideRight
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: targetLabBridge ? targetLabBridge.nextActionBody : ""
                                    color: "#D5DEE8"
                                    font.pixelSize: 13
                                    font.family: "Menlo"
                                    wrapMode: Text.Wrap
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    ActionButton {
                                        label: targetLabBridge ? targetLabBridge.primaryActionLabel : "ГОТОВО"
                                        accent: root.toneColor(targetLabBridge ? targetLabBridge.nextActionTone : "idle")
                                        enabled: !(targetLabBridge && targetLabBridge.gtDiagnosticsRunning)
                                        onClicked: root.runPrimaryAction()
                                    }
                                    ActionButton {
                                        label: targetLabBridge && targetLabBridge.gtDiagnosticsRunning ? "ОСТАНОВИТЬ" : "ПРОВЕРИТЬ ТРЕКЕР"
                                        accent: targetLabBridge && targetLabBridge.gtDiagnosticsRunning ? "#E26B6B" : "#E8B547"
                                        enabled: targetLabBridge && (targetLabBridge.gtDiagnosticsRunning || targetLabBridge.gtDiagnosticsCanRun)
                                        onClicked: {
                                            if (!targetLabBridge) return
                                            if (targetLabBridge.gtDiagnosticsRunning) targetLabBridge.cancelGtDiagnostics()
                                            else targetLabBridge.runGtDiagnostics()
                                        }
                                    }
                                    Item { Layout.fillWidth: true }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 14
                            TruthCard { title: "Материал"; body: "кадры из live и видео"; accent: "#64B5F6" }
                            TruthCard { title: "Проверка"; body: "истина говорит, где трекер слабый"; accent: "#E8B547" }
                            TruthCard { title: "Улучшение"; body: "candidate принимается только после сравнения"; accent: "#52D273" }
                        }
                    }
                }

                GtAssistOverlay {
                    anchors.fill: parent
                    visible: root.activeView === 1
                    embedded: true
                    onClosed: root.activeView = 0
                }

                DtsOverlay {
                    anchors.fill: parent
                    visible: root.activeView === 2
                    embedded: true
                    onClosed: root.activeView = 0
                }

                Flickable {
                    anchors.fill: parent
                    visible: root.activeView === 3
                    contentWidth: width
                    contentHeight: detailsCol.implicitHeight + 44
                    clip: true
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    ColumnLayout {
                        id: detailsCol
                        width: parent.width
                        anchors.margins: 22
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        spacing: 14

                        Text { text: "ИНЖЕНЕРНЫЕ ДЕТАЛИ"; color: "#8FA4B8"; font.pixelSize: 13; font.family: "Menlo"; font.letterSpacing: 2 }
                        Text {
                            Layout.fillWidth: true
                            text: targetLabBridge && targetLabBridge.gtDiagnosticsResultDir !== "" ? targetLabBridge.gtDiagnosticsResultDir : "Отчет проверки еще не создан"
                            color: "#64B5F6"
                            font.pixelSize: 11
                            font.family: "Menlo"
                            elide: Text.ElideLeft
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            height: 110
                            radius: 8
                            color: Qt.rgba(1,1,1,0.035)
                            border.color: "#1C2A38"
                            clip: true
                            Text {
                                anchors.fill: parent
                                anchors.margins: 10
                                text: targetLabBridge ? targetLabBridge.gtDiagnosticsLogTail : ""
                                color: "#6F7E8E"
                                font.pixelSize: 10
                                font.family: "Menlo"
                                wrapMode: Text.Wrap
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
            }
        }
    }

    component BigCard: Rectangle {
        id: card
        property string title: ""
        property string value: ""
        property string subtitle: ""
        property color accent: "#8FA4B8"
        default property alias content: contentCol.data
        radius: 10
        color: Qt.rgba(1,1,1,0.035)
        border.color: Qt.rgba(accent.r, accent.g, accent.b, 0.32)
        border.width: 1
        implicitHeight: contentCol.implicitHeight + 32
        clip: true
        ColumnLayout {
            id: contentCol
            anchors.fill: parent
            anchors.margins: 16
            spacing: 10
            Text { text: card.title; color: card.accent; font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 2 }
            Text { Layout.fillWidth: true; text: card.value; color: "#E6ECF3"; font.pixelSize: 24; font.family: "Menlo"; font.bold: true; elide: Text.ElideRight }
            Text { Layout.fillWidth: true; text: card.subtitle; color: "#8FA4B8"; font.pixelSize: 11; font.family: "Menlo"; elide: Text.ElideRight }
        }
    }

    component ScenePill: Rectangle {
        property string scene: ""
        property string main: ""
        property string note: ""
        property color accent: "#8FA4B8"
        Layout.fillWidth: true
        height: 34
        radius: 7
        color: Qt.rgba(accent.r, accent.g, accent.b, 0.08)
        border.color: Qt.rgba(accent.r, accent.g, accent.b, 0.24)
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            Text { Layout.preferredWidth: 94; text: scene; color: accent; font.pixelSize: 10; font.family: "Menlo"; font.bold: true; elide: Text.ElideRight }
            Text { Layout.fillWidth: true; text: main; color: "#D5DEE8"; font.pixelSize: 10; font.family: "Menlo"; elide: Text.ElideRight }
            Text { text: note; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; elide: Text.ElideRight }
        }
    }

    component CheckPill: Rectangle {
        property string scene: ""
        property int recall: 0
        property int falseLock: 0
        property int fps: 0
        property string status: ""
        property string tone: "idle"
        Layout.fillWidth: true
        height: 38
        radius: 7
        color: root.toneFill(tone)
        border.color: root.toneColor(tone)
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            spacing: 10
            Text { Layout.preferredWidth: 82; text: scene; color: root.toneColor(tone); font.pixelSize: 10; font.family: "Menlo"; font.bold: true; elide: Text.ElideRight }
            Text { text: "видит " + recall + "%"; color: "#D5DEE8"; font.pixelSize: 10; font.family: "Menlo" }
            Text { text: "мимо " + falseLock + "%"; color: falseLock > 25 ? "#E8B547" : "#8FA4B8"; font.pixelSize: 10; font.family: "Menlo" }
            Text { text: "FPS " + fps; color: "#8FA4B8"; font.pixelSize: 10; font.family: "Menlo" }
            Item { Layout.fillWidth: true }
            Text { text: status; color: root.toneColor(tone); font.pixelSize: 9; font.family: "Menlo"; elide: Text.ElideRight }
        }
    }

    component TruthCard: Rectangle {
        property string title: ""
        property string body: ""
        property color accent: "#8FA4B8"
        Layout.fillWidth: true
        height: 78
        radius: 9
        color: Qt.rgba(accent.r, accent.g, accent.b, 0.06)
        border.color: Qt.rgba(accent.r, accent.g, accent.b, 0.20)
        Column {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 6
            Text { width: parent.width; text: title; color: accent; font.pixelSize: 12; font.family: "Menlo"; font.bold: true; elide: Text.ElideRight }
            Text { width: parent.width; text: body; color: "#8FA4B8"; font.pixelSize: 10; font.family: "Menlo"; wrapMode: Text.Wrap }
        }
    }

    component StepNav: Rectangle {
        id: nav
        property string number: ""
        property string title: ""
        property string detail: ""
        property bool active: false
        signal clicked()
        Layout.fillWidth: true
        height: 54
        radius: 8
        color: active ? Qt.rgba(0.561,0.643,0.722,0.12) : (navMa.containsMouse ? Qt.rgba(1,1,1,0.045) : "transparent")
        border.color: active ? Qt.rgba(0.561,0.643,0.722,0.40) : Qt.rgba(1,1,1,0.10)
        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10
            Rectangle {
                width: 26; height: 26; radius: 13
                color: active ? "#E8B547" : Qt.rgba(1,1,1,0.05)
                Text { anchors.centerIn: parent; text: number; color: active ? "#080D12" : "#8FA4B8"; font.pixelSize: 11; font.family: "Menlo"; font.bold: true }
            }
            Column {
                Layout.fillWidth: true
                spacing: 3
                Text { width: parent.width; text: title; color: active ? "#E6ECF3" : "#A9B5C2"; font.pixelSize: 11; font.family: "Menlo"; elide: Text.ElideRight }
                Text { width: parent.width; text: detail; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; elide: Text.ElideRight }
            }
        }
        MouseArea { id: navMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: nav.clicked() }
    }

    component SideButton: Rectangle {
        id: btn
        property string label: ""
        property string detail: ""
        property color accent: "#8FA4B8"
        property bool active: false
        signal clicked()
        Layout.fillWidth: true
        height: 44
        radius: 8
        color: active ? Qt.rgba(accent.r, accent.g, accent.b, 0.12) : (sideMa.containsMouse ? Qt.rgba(1,1,1,0.045) : "transparent")
        border.color: active ? Qt.rgba(accent.r, accent.g, accent.b, 0.38) : Qt.rgba(1,1,1,0.09)
        Column {
            anchors.fill: parent
            anchors.leftMargin: 11
            anchors.rightMargin: 11
            anchors.topMargin: 8
            spacing: 3
            Text { width: parent.width; text: label; color: accent; font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1.1; elide: Text.ElideRight }
            Text { width: parent.width; text: detail; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; elide: Text.ElideRight }
        }
        MouseArea { id: sideMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: btn.clicked() }
    }

    component ActionButton: Rectangle {
        id: action
        property string label: ""
        property color accent: "#8FA4B8"
        signal clicked()
        Layout.preferredWidth: 210
        height: 38
        radius: 8
        opacity: enabled ? 1.0 : 0.42
        color: actionMa.containsMouse && enabled ? Qt.rgba(accent.r, accent.g, accent.b, 0.15) : Qt.rgba(accent.r, accent.g, accent.b, 0.075)
        border.color: Qt.rgba(accent.r, accent.g, accent.b, enabled ? 0.50 : 0.22)
        Text { anchors.centerIn: parent; text: label; color: accent; font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1.2; elide: Text.ElideRight }
        MouseArea {
            id: actionMa
            anchors.fill: parent
            enabled: action.enabled
            hoverEnabled: true
            cursorShape: action.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: action.clicked()
        }
    }

    component HeaderButton: Rectangle {
        id: headerBtn
        property string label: ""
        property color accent: "#8FA4B8"
        signal clicked()
        height: 32
        radius: 7
        color: headerMa.containsMouse ? Qt.rgba(accent.r, accent.g, accent.b, 0.12) : "transparent"
        border.color: Qt.rgba(accent.r, accent.g, accent.b, 0.35)
        Text { anchors.centerIn: parent; text: label; color: accent; font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1 }
        MouseArea { id: headerMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: headerBtn.clicked() }
    }
}
