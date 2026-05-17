import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: dlg
    width: 420
    height: _step === 0 ? 310 : 280
    radius: 14
    color: Qt.rgba(0.05, 0.09, 0.15, 0.96)
    border.color: Qt.rgba(1,1,1,0.16); border.width: 1
    clip: true

    Behavior on height { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

    signal sourceSelected(string sourceType, string sourceValue, int cameraIndex)
    signal cancelled()

    // Internal state
    property int    _step:         0      // 0=select, 1=configure
    property string _type:         ""     // "ВИДЕО"|"ПОТОК"|"КАМЕРА"
    property string _filePath:     "test_videos/cli_smoke_test.mp4"
    property string _rtspUrl:      "rtsp://192.168.1.100/stream"
    property int    _camIdx:       0

    onVisibleChanged: {
        if (visible && settingsBridge) {
            var savedPath = settingsBridge.value("last_video_path")
            if (savedPath !== "") dlg._filePath = savedPath
        }
    }

    function reset() { _step = 0; _type = ""; _camIdx = 0 }

    // ── Step 0: Source type selection ────────────────────────────────
    Item {
        anchors.fill: parent
        opacity: dlg._step === 0 ? 1 : 0
        visible: opacity > 0.01
        Behavior on opacity { NumberAnimation { duration: 160 } }

        // Title
        Text {
            anchors.top: parent.top; anchors.topMargin: 20
            anchors.left: parent.left; anchors.leftMargin: 24
            text: "ВЫБОР ИСТОЧНИКА"
            color: Qt.rgba(1,1,1,0.55); font.pixelSize: 10; font.family: "Menlo"
            font.letterSpacing: 3; font.weight: Font.DemiBold
        }

        Rectangle {
            anchors.top: parent.top; anchors.topMargin: 48
            anchors.left: parent.left; anchors.right: parent.right
            height: 1; color: Qt.rgba(1,1,1,0.07)
        }

        Column {
            anchors.top: parent.top; anchors.topMargin: 56
            anchors.left: parent.left; anchors.right: parent.right
            anchors.leftMargin: 16; anchors.rightMargin: 16
            spacing: 8

            Repeater {
                model: [
                    { label: "ВИДЕО",  desc: "Видеофайл с диска (MP4, AVI...)",  src: "ВИДЕО",  icon: "▶" },
                    { label: "ПОТОК",  desc: "RTSP / HTTP видеопоток из сети",    src: "ПОТОК",  icon: "⟳" },
                    { label: "КАМЕРА", desc: "Встроенная или USB-камера",         src: "КАМЕРА", icon: "◉" },
                ]
                Rectangle {
                    required property var modelData
                    width: parent.width; height: 58; radius: 9
                    color: oMa.pressed       ? Qt.rgba(0.561, 0.643, 0.722, 0.20)
                         : oMa.containsMouse ? Qt.rgba(0.561, 0.643, 0.722, 0.10) : Qt.rgba(1,1,1,0.04)
                    border.color: oMa.containsMouse ? Qt.rgba(0.561,0.643,0.722,0.50) : Qt.rgba(1,1,1,0.10)
                    border.width: 1

                    Text {
                        anchors.left: parent.left; anchors.leftMargin: 16
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.icon; color: oMa.containsMouse ? "#8FA4B8" : "#4A5E6E"
                        font.pixelSize: 20
                    }
                    Column {
                        anchors.left: parent.left; anchors.leftMargin: 48
                        anchors.verticalCenter: parent.verticalCenter; spacing: 4
                        Text { text: modelData.label; color: "#E6ECF3"; font.pixelSize: 12; font.family: "Menlo"; font.weight: Font.Normal }
                        Text { text: modelData.desc; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo" }
                    }
                    Text {
                        anchors.right: parent.right; anchors.rightMargin: 16
                        anchors.verticalCenter: parent.verticalCenter
                        text: "›"; font.pixelSize: 22
                        color: oMa.containsMouse ? "#8FA4B8" : "#2A3A4A"
                    }
                    MouseArea {
                        id: oMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: { dlg._type = modelData.src; dlg._step = 1 }
                    }
                }
            }

            // Cancel
            Rectangle {
                width: parent.width; height: 32; radius: 7
                color: cMa.containsMouse ? Qt.rgba(0.886,0.420,0.420,0.12) : "transparent"
                border.color: Qt.rgba(0.886,0.420,0.420,0.28); border.width: 1
                Text { anchors.centerIn: parent; text: "ОТМЕНА"; color: "#E26B6B"
                       font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.5 }
                MouseArea { id: cMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: { dlg.reset(); dlg.cancelled() } }
            }
        }
    }

    // ── Step 1: Configuration ────────────────────────────────────────
    Item {
        anchors.fill: parent
        opacity: dlg._step === 1 ? 1 : 0
        visible: opacity > 0.01
        Behavior on opacity { NumberAnimation { duration: 160 } }

        // Back row
        Row {
            id: backRow
            anchors.top: parent.top; anchors.topMargin: 16
            anchors.left: parent.left; anchors.leftMargin: 16
            spacing: 8

            Rectangle {
                width: 26; height: 26; radius: 6
                color: backMa.containsMouse ? Qt.rgba(1,1,1,0.08) : "transparent"
                border.color: Qt.rgba(1,1,1,0.10); border.width: 1
                Text { anchors.centerIn: parent; text: "←"; color: "#8FA4B8"; font.pixelSize: 12; font.family: "Menlo" }
                MouseArea { id: backMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: dlg._step = 0 }
            }
            Text { text: dlg._type; color: "#8FA4B8"; font.pixelSize: 11; font.family: "Menlo"
                   font.letterSpacing: 2; font.weight: Font.DemiBold; anchors.verticalCenter: parent.verticalCenter }
        }

        Rectangle {
            anchors.top: backRow.bottom; anchors.topMargin: 14
            anchors.left: parent.left; anchors.right: parent.right
            height: 1; color: Qt.rgba(1,1,1,0.07)
        }

        // ── ВИДЕО config ─────────────────────────────────────────────
        Column {
            visible: dlg._type === "ВИДЕО"
            anchors.top: backRow.bottom; anchors.topMargin: 26
            anchors.left: parent.left; anchors.right: parent.right
            anchors.leftMargin: 20; anchors.rightMargin: 20
            spacing: 10

            Text { text: "ПУТЬ К ФАЙЛУ"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.5 }

            Rectangle {
                width: parent.width; height: 36; radius: 8
                color: Qt.rgba(1,1,1,0.05); border.color: Qt.rgba(1,1,1,0.12); border.width: 1

                TextInput {
                    id: filePathInput
                    anchors.left: parent.left; anchors.leftMargin: 12
                    anchors.right: browseBtn.left; anchors.rightMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    text: dlg._filePath; color: "#A9B5C2"
                    font.pixelSize: 10; font.family: "Menlo"
                    clip: true
                    onTextChanged: dlg._filePath = text
                }
                Rectangle {
                    id: browseBtn
                    anchors.right: parent.right; anchors.rightMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    width: 56; height: 26; radius: 6
                    color: brMa.containsMouse ? Qt.rgba(0.561,0.643,0.722,0.18) : Qt.rgba(1,1,1,0.06)
                    border.color: Qt.rgba(1,1,1,0.12); border.width: 1
                    Text { anchors.centerIn: parent; text: "Обзор"; color: "#8FA4B8"; font.pixelSize: 9; font.family: "Menlo" }
                    MouseArea {
                        id: brMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var picked = bridge ? bridge.browseVideoFile() : ""
                            if (picked !== "") {
                                filePathInput.text = picked
                                dlg._filePath = picked
                                if (settingsBridge) settingsBridge.setValue("last_video_path", picked)
                            }
                        }
                    }
                }
            }

            Text { text: "MP4 · AVI · MOV · MKV"; color: "#2A3A4A"; font.pixelSize: 8; font.family: "Menlo" }

            Rectangle {
                width: parent.width; height: 36; radius: 8
                color: vidMa.containsMouse ? Qt.rgba(0.322,0.824,0.451,0.20) : Qt.rgba(0.322,0.824,0.451,0.10)
                border.color: Qt.rgba(0.322,0.824,0.451,0.50); border.width: 1
                Text { anchors.centerIn: parent; text: "▶  ЗАПУСТИТЬ"; color: "#52D273"
                       font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1.5; font.weight: Font.DemiBold }
                MouseArea { id: vidMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                var p = filePathInput.text
                                if (settingsBridge) settingsBridge.setValue("last_video_path", p)
                                dlg.reset()
                                dlg.sourceSelected("video", p, 0)
                            } }
            }
        }

        // ── ПОТОК config ─────────────────────────────────────────────
        Column {
            visible: dlg._type === "ПОТОК"
            anchors.top: backRow.bottom; anchors.topMargin: 26
            anchors.left: parent.left; anchors.right: parent.right
            anchors.leftMargin: 20; anchors.rightMargin: 20
            spacing: 10

            Text { text: "URL ПОТОКА"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.5 }

            Rectangle {
                width: parent.width; height: 36; radius: 8
                color: Qt.rgba(1,1,1,0.05); border.color: Qt.rgba(1,1,1,0.12); border.width: 1
                TextInput {
                    id: urlInput
                    anchors.left: parent.left; anchors.leftMargin: 12
                    anchors.right: parent.right; anchors.rightMargin: 12
                    anchors.verticalCenter: parent.verticalCenter
                    text: dlg._rtspUrl; color: "#A9B5C2"
                    font.pixelSize: 10; font.family: "Menlo"
                    clip: true
                    onTextChanged: dlg._rtspUrl = text
                }
            }

            Row {
                spacing: 6
                Repeater {
                    model: ["rtsp://", "http://", "udp://"]
                    Rectangle {
                        required property string modelData
                        required property int index
                        width: protoLbl.implicitWidth + 14; height: 22; radius: 5
                        color: Qt.rgba(1,1,1,0.04); border.color: Qt.rgba(1,1,1,0.10); border.width: 1
                        Text { id: protoLbl; anchors.centerIn: parent; text: modelData; color: "#4A5E6E"
                               font.pixelSize: 9; font.family: "Menlo" }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    onClicked: { urlInput.text = modelData } }
                    }
                }
            }

            Rectangle {
                width: parent.width; height: 36; radius: 8
                color: strMa.containsMouse ? Qt.rgba(0.561,0.643,0.722,0.22) : Qt.rgba(0.561,0.643,0.722,0.12)
                border.color: Qt.rgba(0.561,0.643,0.722,0.55); border.width: 1
                Text { anchors.centerIn: parent; text: "⟳  ПОДКЛЮЧИТЬ"; color: "#8FA4B8"
                       font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1.5; font.weight: Font.DemiBold }
                MouseArea { id: strMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: { var u = urlInput.text; dlg.reset(); dlg.sourceSelected("stream", u, 0) } }
            }
        }

        // ── КАМЕРА config ─────────────────────────────────────────────
        Column {
            visible: dlg._type === "КАМЕРА"
            anchors.top: backRow.bottom; anchors.topMargin: 22
            anchors.left: parent.left; anchors.right: parent.right
            anchors.leftMargin: 20; anchors.rightMargin: 20
            spacing: 8

            Text { text: "ВЫБОР УСТРОЙСТВА"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.5 }

            Repeater {
                model: ["FaceTime HD (встроенная)", "OBS Virtual Camera", "USB Camera ELP-960P"]
                Rectangle {
                    required property string modelData
                    required property int index
                    width: parent.width; height: 34; radius: 7
                    color: dlg._camIdx === index
                           ? Qt.rgba(0.322,0.824,0.451,0.10)
                           : camMa.containsMouse ? Qt.rgba(1,1,1,0.05) : "transparent"
                    border.color: dlg._camIdx === index ? Qt.rgba(0.322,0.824,0.451,0.40) : Qt.rgba(1,1,1,0.08)
                    border.width: 1

                    Row {
                        anchors.left: parent.left; anchors.leftMargin: 12
                        anchors.verticalCenter: parent.verticalCenter; spacing: 10
                        Rectangle {
                            width: 8; height: 8; radius: 4
                            anchors.verticalCenter: parent.verticalCenter
                            color: dlg._camIdx === index ? "#52D273" : "transparent"
                            border.color: dlg._camIdx === index ? "#52D273" : "#3A5060"; border.width: 1.5
                        }
                        Text { text: modelData; color: dlg._camIdx === index ? "#E6ECF3" : "#8FA4B8"
                               font.pixelSize: 10; font.family: "Menlo"; anchors.verticalCenter: parent.verticalCenter }
                    }
                    MouseArea { id: camMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: dlg._camIdx = index }
                }
            }

            Rectangle {
                width: parent.width; height: 34; radius: 8
                color: camStartMa.containsMouse ? Qt.rgba(0.322,0.824,0.451,0.20) : Qt.rgba(0.322,0.824,0.451,0.10)
                border.color: Qt.rgba(0.322,0.824,0.451,0.50); border.width: 1
                Text { anchors.centerIn: parent; text: "◉  ЗАПУСТИТЬ"; color: "#52D273"
                       font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1.5; font.weight: Font.DemiBold }
                MouseArea { id: camStartMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: { var idx = dlg._camIdx; dlg.reset(); dlg.sourceSelected("camera", "", idx) } }
            }
        }
    }
}
