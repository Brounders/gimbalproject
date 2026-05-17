import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: Qt.rgba(0.06, 0.10, 0.18, 0.58)
    border.color: Qt.rgba(1,1,1,0.22); border.width: 1
    clip: true

    // ── Props from Main ────────────────────────────────────────────────
    property bool   isOpen:        false
    property int    fps:           0
    property string trackingState: "SEARCH"
    property string targetLifecycle: "OFFLINE"
    property string activeSource: "—"
    property int    targetId:      0
    property bool   isRunning:     false
    property real   confidence:    0.0
    property int    latencyMs:     0
    property real   falseLockRisk: 0.0
    property real   lockScore:     0.0
    property real   reliability:   0.0
    property int    idSwitches:    0
    property int    activeTargets: 0
    property bool   isRecording:   false
    property string lastAction:    "Система готова"
    property int    _battery:      68
    property real   _dist:         0.0
    property int    _course:       87
    property real   _alt:          0.0
    property real   _speed:        0.0
    property int    _signal:       0

    // GPS (mock drift from StatusStrip)
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

    property int _selectedTab: 0
    property string _lastLoggedAction: ""
    property string _lastLoggedLifecycle: ""

    // Height: handle 32px collapsed, content above
    height: isOpen ? 210 : 32
    Behavior on height { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }

    // Log model
    ListModel { id: logModel }

    function addLog(level, msg) {
        if (!msg || msg === "") return
        var now = new Date()
        var h = now.getHours(), m = now.getMinutes(), s = now.getSeconds()
        var ts = (h<10?"0":"")+h+":"+(m<10?"0":"")+m+":"+(s<10?"0":"")+s
        logModel.append({ ts: ts, msg: msg, level: level })
        if (logModel.count > 80) logModel.remove(0)
    }

    function stageLabel(stage) {
        var labels = {
            "OFFLINE": "OFFLINE",
            "SEARCH": "ПОИСК",
            "DETECTED": "ОБНАРУЖЕНО",
            "CANDIDATE": "КАНДИДАТ",
            "ACQUIRE": "ЗАХВАТ",
            "VERIFYING": "ПРОВЕРКА",
            "VERIFIED": "ПОДТВЕРЖДЕНО",
            "LOCKED": "LOCK",
            "TRACKING": "TRACK",
            "WEAK_TRACK": "СЛАБЫЙ ТРЕК",
            "REACQUIRE": "REACQUIRE",
            "LOST": "ПОТЕРЯ"
        }
        return labels[stage] || stage
    }

    function stageColor(stage) {
        if (stage === "LOCKED" || stage === "TRACKING" || stage === "VERIFIED") return "#52D273"
        if (stage === "REACQUIRE" || stage === "ACQUIRE" || stage === "VERIFYING" || stage === "WEAK_TRACK") return "#E8B547"
        if (stage === "LOST") return "#E26B6B"
        if (stage === "DETECTED" || stage === "CANDIDATE") return "#8FA4B8"
        return "#4A5E6E"
    }

    onLastActionChanged: {
        if (root.lastAction !== root._lastLoggedAction) {
            root._lastLoggedAction = root.lastAction
            root.addLog(root.lastAction.indexOf("Ошибка") >= 0 ? "err" : "info", root.lastAction)
        }
    }

    onTargetLifecycleChanged: {
        if (root.targetLifecycle !== root._lastLoggedLifecycle) {
            root._lastLoggedLifecycle = root.targetLifecycle
            root.addLog(root.targetLifecycle === "LOST" ? "err" : root.targetLifecycle === "REACQUIRE" ? "warn" : "ok",
                        "Этап цели: " + root.stageLabel(root.targetLifecycle))
        }
    }

    Component.onCompleted: {
        addLog("ok",   "Система инициализирована")
        addLog("info", "Пресет: ДЕНЬ")
        addLog("ok",   "Детектор готов")
        addLog("info", "Ожидание источника")
    }

    // ── Body (opens upward, sits above handle) ─────────────────────────
    Item {
        id: body
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: handle.top
        visible: root.height > 40
        clip: true

        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#151E28" }

        // Tab sidebar
        Item {
            id: tabBar
            anchors.top: parent.top; anchors.topMargin: 1
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            width: 140

            Column {
                anchors.top: parent.top; anchors.topMargin: 10
                width: parent.width; spacing: 0

                Repeater {
                    model: ["Диагностика", "Телеметрия", "Цели", "Журнал событий"]
                    Rectangle {
                        required property string modelData
                        required property int index
                        width: parent.width; height: 34; color: "transparent"

                        Rectangle {
                            visible: root._selectedTab === index
                            width: 2; height: parent.height; color: "#52D273"
                        }
                        Rectangle {
                            anchors.fill: parent
                            color: tMa.containsMouse && root._selectedTab !== index
                                   ? Qt.rgba(1,1,1,0.03) : "transparent"
                        }
                        Text {
                            anchors.left: parent.left; anchors.leftMargin: 16
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData
                            color: root._selectedTab === index ? "#A9B5C2" : "#4A5E6E"
                            font.pixelSize: 10; font.family: "Menlo"
                        }
                        MouseArea {
                            id: tMa; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root._selectedTab = index
                        }
                    }
                }
            }
        }

        Rectangle {
            anchors.left: tabBar.right; anchors.top: parent.top; anchors.topMargin: 1
            anchors.bottom: parent.bottom; width: 1; color: "#151E28"
        }

        // Content area
        Item {
            anchors.left: tabBar.right; anchors.leftMargin: 1
            anchors.top: parent.top; anchors.topMargin: 1
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            clip: true

            // Tab 0: Диагностика
            GridLayout {
                visible: root._selectedTab === 0
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 10 }
                columns: 4; columnSpacing: 6; rowSpacing: 6

                DiagCard { label: "FPS";        value: root.fps > 0 ? root.fps + "" : "—" }
                DiagCard { label: "ЗАДЕРЖКА";   value: root.latencyMs > 0 ? root.latencyMs + " мс" : "—" }
                DiagCard {
                    label: "FALSE LOCK"
                    value: root.isRunning ? Math.round(root.falseLockRisk * 100) + "%" : "—"
                    valueColor: root.falseLockRisk > 0.20 ? "#E26B6B"
                              : root.falseLockRisk > 0.10 ? "#E8B547" : "#52D273"
                }
                DiagCard { label: "ID SW";      value: root.idSwitches + "" }
                DiagCard {
                    label: "ЭТАП ЦЕЛИ"
                    value: root.isRunning ? root.stageLabel(root.targetLifecycle) : "OFFLINE"
                    valueColor: root.stageColor(root.targetLifecycle)
                }
                DiagCard { label: "ЦЕЛИ";       value: root.activeTargets + "" }
                DiagCard {
                    label: "УВЕРЕН."
                    value: root.isRunning ? Math.round(root.confidence * 100) + "%" : "—"
                    valueColor: root.confidence > 0.80 ? "#52D273"
                              : root.confidence > 0.55 ? "#E8B547" : "#E26B6B"
                }
                DiagCard { label: "СИСТЕМА";    value: "OK"; valueColor: "#52D273" }
            }

            // Tab 1: Телеметрия
            GridLayout {
                visible: root._selectedTab === 1
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 10 }
                columns: 4; columnSpacing: 6; rowSpacing: 6

                DiagCard { label: "ДИСТ.";    value: root.isRunning ? root._dist.toFixed(1) + " м" : "—" }
                DiagCard { label: "КУРС";     value: root.isRunning ? String(root._course).padStart(3,"0") + "°" : "—" }
                DiagCard { label: "ВЫСОТА";   value: root.isRunning ? root._alt.toFixed(1) + " м" : "—" }
                DiagCard { label: "СКОРОСТЬ"; value: root.isRunning ? root._speed.toFixed(1) + " м/с" : "—" }
                DiagCard {
                    label: "БАТАРЕЯ"; value: root._battery + "%"
                    valueColor: root._battery > 40 ? "#52D273" : root._battery > 20 ? "#E8B547" : "#E26B6B"
                }
                DiagCard {
                    label: "СИГНАЛ"; value: root.isRunning ? root._signal + "%" : "—"
                    valueColor: root._signal > 60 ? "#8FA4B8" : "#E8B547"
                }
                DiagCard { label: "ДРОНЫ";    value: root.isRunning ? "1" : "0" }
                DiagCard { label: "ПОТЕРЯНО"; value: "0" }
            }

            // Tab 2: Цели
            GridLayout {
                visible: root._selectedTab === 2
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 10 }
                columns: 4; columnSpacing: 6; rowSpacing: 6

                DiagCard { label: "АКТИВНАЯ"; value: root.isRunning ? "T-" + (root.targetId < 10 ? "0" : "") + root.targetId : "—"; valueColor: root.isRunning ? "#A9B5C2" : "#4A5E6E" }
                DiagCard { label: "ЭТАП"; value: root.isRunning ? root.stageLabel(root.targetLifecycle) : "OFFLINE"; valueColor: root.stageColor(root.targetLifecycle) }
                DiagCard { label: "SOURCE"; value: root.isRunning ? root.activeSource : "—" }
                DiagCard { label: "КАНДИДАТЫ"; value: root.activeTargets + "" }
                DiagCard { label: "LOCK"; value: root.isRunning ? root.lockScore.toFixed(2) : "—" }
                DiagCard { label: "НАДЁЖН."; value: root.isRunning ? root.reliability.toFixed(2) : "—" }
                DiagCard { label: "CONF"; value: root.isRunning ? Math.round(root.confidence * 100) + "%" : "—" }
                DiagCard { label: "ID SW"; value: root.idSwitches + "" }
            }

            // Tab 3: Журнал событий
            ListView {
                visible: root._selectedTab === 3
                anchors { fill: parent; margins: 8 }
                clip: true
                model: logModel
                verticalLayoutDirection: ListView.BottomToTop

                delegate: Row {
                    required property string ts
                    required property string msg
                    required property string level
                    width: parent ? parent.width : 0
                    height: 20; spacing: 8
                    Text { text: ts; color: "#3A5060"; font.pixelSize: 9; font.family: "Menlo"; width: 62 }
                    Text {
                        text: msg
                        color: level === "ok"   ? "#52D273"
                             : level === "warn" ? "#E8B547"
                             : level === "err"  ? "#E26B6B" : "#8FA4B8"
                        font.pixelSize: 9; font.family: "Menlo"
                    }
                }
            }
        }
    }

    // ── Handle (always visible, at the BOTTOM) ─────────────────────────
    Rectangle {
        id: handle
        anchors.bottom: parent.bottom
        anchors.left:   parent.left
        anchors.right:  parent.right
        height: 32
        color: "transparent"

        Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: "#151E28" }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 14; anchors.rightMargin: 14
            spacing: 0

            // GPS
            Text {
                text: root._lat.toFixed(3) + "° N   " + root._lon.toFixed(3) + "° E"
                color: "#3A5060"; font.pixelSize: 9; font.family: "Menlo"
                font.letterSpacing: 0.5
            }

            // Sep
            Rectangle { width: 1; height: 12; color: "#1C2A38"; Layout.leftMargin: 10; Layout.rightMargin: 10 }

            // Signal
            Text {
                text: "SIG " + root._sig + " dBm"
                color: root._sig > -70 ? "#52D273" : root._sig > -80 ? "#E8B547" : "#E26B6B"
                font.pixelSize: 9; font.family: "Menlo"
            }

            // Sep
            Rectangle { width: 1; height: 12; color: "#1C2A38"; Layout.leftMargin: 10; Layout.rightMargin: 10 }

            // REC
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
                    color: root.isRecording ? "#E26B6B" : "#2A3A4A"
                    font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            // Sep
            Rectangle { width: 1; height: 12; color: "#1C2A38"; Layout.leftMargin: 10; Layout.rightMargin: 10 }

            // Last action
            Text {
                text: root.lastAction; color: "#3A5060"
                font.pixelSize: 9; font.family: "Menlo"
                elide: Text.ElideRight; Layout.fillWidth: true
            }

            // Chevron center-ish (between lastAction and FPS)
            Text {
                text: root.isOpen ? "▼" : "▲"
                color: "#4A5E6E"; font.pixelSize: 8; font.family: "Menlo"
                Layout.leftMargin: 8; Layout.rightMargin: 8
            }

            // Sep
            Rectangle { width: 1; height: 12; color: "#1C2A38"; Layout.leftMargin: 4; Layout.rightMargin: 10 }

            // FPS
            Text {
                text: root.fps > 0 ? "FPS " + root.fps : "FPS —"
                color: root.fps > 20 ? "#3A5060" : root.fps > 0 ? "#E8B547" : "#2A3A4A"
                font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 0.5
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.isOpen = !root.isOpen
        }
    }

    // ── DiagCard inline component ─────────────────────────────────────
    component DiagCard: Rectangle {
        id: dc
        property string label:      ""
        property string value:      "—"
        property color  valueColor: "#E6ECF3"

        height: 44; radius: 5
        color: "#0A1018"
        border.color: Qt.rgba(1,1,1,0.06); border.width: 1
        Layout.fillWidth: true

        Column {
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 7; topMargin: 6 }
            spacing: 2
            Text { text: dc.label; color: "#4A5E6E"; font.pixelSize: 7; font.family: "Menlo"; font.letterSpacing: 1 }
            Text { text: dc.value; color: dc.valueColor; font.pixelSize: 12; font.family: "Menlo"; font.weight: Font.DemiBold }
        }
    }
}
