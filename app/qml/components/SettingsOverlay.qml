import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: Qt.rgba(0, 0, 0, 0.72)

    signal closed()

    MouseArea { anchors.fill: parent; onClicked: root.closed() }

    Rectangle {
        id: settingsBox
        anchors.centerIn: parent
        width: Math.min(820, parent.width - 80)
        height: Math.min(600, parent.height - 80)
        color: "#0C1219"; radius: 12
        border.color: Qt.rgba(1,1,1,0.14); border.width: 1; clip: true

        property string _tab: "СИСТЕМА"

        MouseArea { anchors.fill: parent }

        RowLayout {
            anchors.fill: parent; spacing: 0

            // ── Sidebar ──────────────────────────────────────────────────────
            Rectangle {
                Layout.preferredWidth: 190; Layout.fillHeight: true
                color: "#080D12"; clip: true

                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 12; spacing: 4

                    Rectangle { Layout.fillWidth: true; height: 50; color: "transparent"
                        Text { anchors.verticalCenter: parent.verticalCenter
                               text: "НАСТРОЙКИ"; color: "#3A5060"
                               font.pixelSize: 9; font.family: "Menlo"
                               font.letterSpacing: 2.5; font.weight: Font.DemiBold }
                    }

                    Repeater {
                        model: [
                            {lbl:"СИСТЕМА",  desc:"Основные"},
                            {lbl:"ТРЕКЕР",   desc:"Детектор"},
                            {lbl:"КАМЕРА",   desc:"Изображение"},
                            {lbl:"КАРТА",    desc:"Геопозиция"},
                            {lbl:"СЕТЬ",     desc:"Подключение"},
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true; height: 48; radius: 7
                            property bool sel: settingsBox._tab === modelData.lbl
                            color: sel ? Qt.rgba(0.561,0.643,0.722,0.12)
                                       : sbMa.containsMouse ? Qt.rgba(1,1,1,0.04) : "transparent"
                            border.color: sel ? Qt.rgba(0.561,0.643,0.722,0.30) : "transparent"; border.width: 1
                            MouseArea { id: sbMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: settingsBox._tab = modelData.lbl }
                            Column {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left; anchors.leftMargin: 12
                                spacing: 3
                                Text { text: modelData.lbl; font.pixelSize: 11; font.family: "Menlo"
                                       font.weight: Font.Normal
                                       color: parent.parent.sel ? "#E6ECF3" : "#6F7E8E" }
                                Text { text: modelData.desc; font.pixelSize: 9; font.family: "Menlo"; color: "#3A5060" }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }

                    Rectangle {
                        Layout.fillWidth: true; height: 36; radius: 6; color: "transparent"
                        border.color: Qt.rgba(0.886,0.420,0.420,0.28); border.width: 1
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.closed() }
                        Text { anchors.centerIn: parent; text: "ЗАКРЫТЬ"; color: "#7A3A3A"
                               font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1 }
                    }
                    Item { height: 4 }
                }
            }

            Rectangle { width: 1; Layout.fillHeight: true; color: "#1C2A38" }

            // ── Content ──────────────────────────────────────────────────────
            Item {
                Layout.fillWidth: true; Layout.fillHeight: true

                // ── СИСТЕМА ──────────────────────────────────────────────────
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 24; anchors.topMargin: 20; spacing: 0
                    visible: settingsBox._tab === "СИСТЕМА"

                    Text { text: "СИСТЕМА"; color: "#5A7080"; font.pixelSize: 9; font.family: "Menlo"
                           font.letterSpacing: 2.5; Layout.bottomMargin: 18 }

                    Repeater {
                        model: [
                            {lbl:"Язык интерфейса",      val:"Русский"},
                            {lbl:"Тема оформления",       val:"Тёмная"},
                            {lbl:"Звуковые уведомления",  val:"Вкл"},
                            {lbl:"Автозапись при старте", val:"Выкл"},
                            {lbl:"Автосохранение логов",  val:"Вкл"},
                            {lbl:"Интервал лога (сек)",   val:"5"},
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true; height: 46; color: "transparent"
                            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#131E2A" }
                            RowLayout {
                                anchors.fill: parent
                                Text { text: modelData.lbl; color: "#6F7E8E"; font.pixelSize: 11; font.family: "Menlo" }
                                Item { Layout.fillWidth: true }
                                Rectangle {
                                    width: valLbl.implicitWidth + 20; height: 26; radius: 5
                                    color: Qt.rgba(1,1,1,0.05); border.color: Qt.rgba(1,1,1,0.09); border.width: 1
                                    Text { id: valLbl; anchors.centerIn: parent; text: modelData.val; color: "#A9B5C2"
                                           font.pixelSize: 11; font.family: "Menlo" }
                                }
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }

                // ── ТРЕКЕР ───────────────────────────────────────────────────
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 24; anchors.topMargin: 20; spacing: 10
                    visible: settingsBox._tab === "ТРЕКЕР"

                    Text { text: "ТРЕКЕР"; color: "#5A7080"; font.pixelSize: 9; font.family: "Menlo"
                           font.letterSpacing: 2.5; Layout.bottomMargin: 8 }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 10
                        rowSpacing: 8

                        SettingInput { label: "YOLO confidence"; keyName: "tracker_conf_thresh"; valueText: settingsBridge ? settingsBridge.value("tracker_conf_thresh") : "0.30" }
                        SettingInput { label: "Small target confidence"; keyName: "tracker_small_target_conf"; valueText: settingsBridge ? settingsBridge.value("tracker_small_target_conf") : "0.15" }
                        SettingInput { label: "YOLO image size"; keyName: "tracker_img_size"; valueText: settingsBridge ? settingsBridge.value("tracker_img_size") : "640" }
                        SettingInput { label: "Small target image size"; keyName: "tracker_small_target_img_size"; valueText: settingsBridge ? settingsBridge.value("tracker_small_target_img_size") : "960" }
                        SettingInput { label: "Night detector 1/0"; keyName: "tracker_night_enabled"; valueText: settingsBridge ? settingsBridge.value("tracker_night_enabled") : "1" }
                        SettingInput { label: "Night confirm frames"; keyName: "tracker_night_confirm"; valueText: settingsBridge ? settingsBridge.value("tracker_night_confirm") : "3" }
                        SettingInput { label: "Lock tracker 1/0"; keyName: "tracker_lock_tracker_enabled"; valueText: settingsBridge ? settingsBridge.value("tracker_lock_tracker_enabled") : "1" }
                        SettingInput { label: "Lock confirm frames"; keyName: "tracker_lock_confirm_frames"; valueText: settingsBridge ? settingsBridge.value("tracker_lock_confirm_frames") : "5" }
                        SettingInput { label: "Lost state frames"; keyName: "tracker_track_state_lost_frames"; valueText: settingsBridge ? settingsBridge.value("tracker_track_state_lost_frames") : "8" }
                        SettingInput { label: "YOLO lost max"; keyName: "tracker_yolo_lost_max"; valueText: settingsBridge ? settingsBridge.value("tracker_yolo_lost_max") : "12" }
                        SettingInput { label: "ROI assist 1/0"; keyName: "tracker_roi_assist_enabled"; valueText: settingsBridge ? settingsBridge.value("tracker_roi_assist_enabled") : "1" }
                        SettingInput { label: "ROI confidence"; keyName: "tracker_roi_conf_thresh"; valueText: settingsBridge ? settingsBridge.value("tracker_roi_conf_thresh") : "0.12" }
                        SettingInput { label: "ROI max candidates"; keyName: "tracker_roi_max_candidates"; valueText: settingsBridge ? settingsBridge.value("tracker_roi_max_candidates") : "3" }
                        SettingInput { label: "DTS annotation log 1/0"; keyName: "tracker_operator_annotation_enabled"; valueText: settingsBridge ? settingsBridge.value("tracker_operator_annotation_enabled") : "0" }
                    }

                    Rectangle {
                        Layout.fillWidth: true; height: 54; radius: 7
                        color: Qt.rgba(0.910,0.714,0.279,0.06)
                        border.color: Qt.rgba(0.910,0.714,0.279,0.18); border.width: 1
                        Text {
                            anchors.fill: parent; anchors.margins: 10
                            text: "Параметры трекера применяются при следующем запуске трекинга. Размеры image size автоматически округляются к шагу YOLO 32."
                            color: "#A58B4A"; font.pixelSize: 10; font.family: "Menlo"; wrapMode: Text.Wrap
                        }
                    }

                    Item { Layout.fillHeight: true }
                }

                // ── КАМЕРА ───────────────────────────────────────────────────
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 24; anchors.topMargin: 20; spacing: 0
                    visible: settingsBox._tab === "КАМЕРА"

                    Text { text: "КАМЕРА"; color: "#5A7080"; font.pixelSize: 9; font.family: "Menlo"
                           font.letterSpacing: 2.5; Layout.bottomMargin: 18 }

                    Repeater {
                        model: [
                            {lbl:"Режим по умолчанию",   val:"ДЕНЬ"},
                            {lbl:"Зум по умолчанию",     val:"×1.0"},
                            {lbl:"Стабилизация",          val:"Вкл"},
                            {lbl:"Целевой FPS",           val:"30"},
                            {lbl:"Экспозиция авто",       val:"Вкл"},
                            {lbl:"Усиление (gain)",       val:"AUTO"},
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true; height: 46; color: "transparent"
                            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#131E2A" }
                            RowLayout {
                                anchors.fill: parent
                                Text { text: modelData.lbl; color: "#6F7E8E"; font.pixelSize: 11; font.family: "Menlo" }
                                Item { Layout.fillWidth: true }
                                Rectangle {
                                    width: valLbl2.implicitWidth + 20; height: 26; radius: 5
                                    color: Qt.rgba(1,1,1,0.05); border.color: Qt.rgba(1,1,1,0.09); border.width: 1
                                    Text { id: valLbl2; anchors.centerIn: parent; text: modelData.val; color: "#A9B5C2"
                                           font.pixelSize: 11; font.family: "Menlo" }
                                }
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }

                // ── КАРТА ───────────────────────────────────────────────────
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 24; anchors.topMargin: 20; spacing: 10
                    visible: settingsBox._tab === "КАРТА"

                    Text { text: "КАРТА"; color: "#5A7080"; font.pixelSize: 9; font.family: "Menlo"
                           font.letterSpacing: 2.5; Layout.bottomMargin: 8 }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 10
                        rowSpacing: 8

                        SettingInput { label: "Широта устройства"; keyName: "device_lat"; valueText: settingsBridge ? settingsBridge.deviceLat.toFixed(6) : "0" }
                        SettingInput { label: "Долгота устройства"; keyName: "device_lon"; valueText: settingsBridge ? settingsBridge.deviceLon.toFixed(6) : "0" }
                        SettingInput { label: "Высота над морем, м"; keyName: "device_alt_m"; valueText: settingsBridge ? settingsBridge.deviceAltM.toFixed(1) : "0" }
                        SettingInput { label: "Пеленг базы, ° true"; keyName: "heading_deg"; valueText: settingsBridge ? settingsBridge.headingDeg.toFixed(1) : "0" }
                        SettingInput { label: "Поправка yaw, °"; keyName: "gimbal_yaw_offset_deg"; valueText: settingsBridge ? settingsBridge.gimbalYawOffsetDeg.toFixed(1) : "0" }
                        SettingInput { label: "Pitch камеры, °"; keyName: "camera_pitch_deg"; valueText: settingsBridge ? settingsBridge.cameraPitchDeg.toFixed(1) : "0" }
                        SettingInput { label: "FOV горизонт, °"; keyName: "camera_fov_h_deg"; valueText: settingsBridge ? settingsBridge.cameraFovHDeg.toFixed(1) : "62" }
                        SettingInput { label: "FOV вертикаль, °"; keyName: "camera_fov_v_deg"; valueText: settingsBridge ? settingsBridge.cameraFovVDeg.toFixed(1) : "38" }
                        SettingInput { label: "Дальность цели, м"; keyName: "manual_range_m"; valueText: settingsBridge ? settingsBridge.manualRangeM.toFixed(0) : "500" }
                        SettingInput { label: "История трека, сек"; keyName: "trail_length_sec"; valueText: settingsBridge ? settingsBridge.trailLengthSec.toFixed(0) : "60" }
                        SettingInput { label: "Прогноз, сек"; keyName: "prediction_horizon_sec"; valueText: settingsBridge ? settingsBridge.predictionHorizonSec.toFixed(0) : "12" }
                        SettingInput { label: "Зум карты"; keyName: "map_zoom"; valueText: settingsBridge ? settingsBridge.mapZoom.toFixed(2) : "1.00" }
                        SettingInput { label: "Поворот карты, °"; keyName: "map_rotation_deg"; valueText: settingsBridge ? settingsBridge.mapRotationDeg.toFixed(1) : "0" }
                    }

                    Rectangle {
                        Layout.fillWidth: true; height: 54; radius: 7
                        color: Qt.rgba(0.910,0.714,0.279,0.06)
                        border.color: Qt.rgba(0.910,0.714,0.279,0.18); border.width: 1
                        Text {
                            anchors.fill: parent; anchors.margins: 10
                            text: "Сейчас карта строит цель по ручной дальности. Точная геопозиция цели потребует дальномер, уверенную оценку distance или отдельную модель расчёта дистанции."
                            color: "#A58B4A"; font.pixelSize: 10; font.family: "Menlo"; wrapMode: Text.Wrap
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Item { Layout.fillWidth: true }
                        Rectangle {
                            width: 142; height: 32; radius: 6
                            color: resetMapMa.containsMouse ? Qt.rgba(0.886,0.420,0.420,0.12) : "transparent"
                            border.color: Qt.rgba(0.886,0.420,0.420,0.30); border.width: 1
                            MouseArea { id: resetMapMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: if (settingsBridge) settingsBridge.resetMapDefaults() }
                            Text { anchors.centerIn: parent; text: "СБРОСИТЬ"; color: "#E26B6B"; font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1 }
                        }
                    }

                    Text { text: settingsBridge ? settingsBridge.lastMessage : ""; color: "#3A5060"; font.pixelSize: 10; font.family: "Menlo" }
                    Item { Layout.fillHeight: true }
                }

                // ── СЕТЬ ─────────────────────────────────────────────────────
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 24; anchors.topMargin: 20; spacing: 0
                    visible: settingsBox._tab === "СЕТЬ"

                    Text { text: "СЕТЬ"; color: "#5A7080"; font.pixelSize: 9; font.family: "Menlo"
                           font.letterSpacing: 2.5; Layout.bottomMargin: 18 }

                    Repeater {
                        model: [
                            {lbl:"IP адрес гимбала",         val:"192.168.1.100"},
                            {lbl:"Порт управления",          val:"5555"},
                            {lbl:"URL видеопотока",          val:"rtsp://192.168.1.100/stream"},
                            {lbl:"Протокол",                 val:"RTSP"},
                            {lbl:"Таймаут соединения (с)",   val:"5"},
                            {lbl:"Переподключение авто",     val:"Вкл"},
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true; height: 46; color: "transparent"
                            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#131E2A" }
                            RowLayout {
                                anchors.fill: parent
                                Text { text: modelData.lbl; color: "#6F7E8E"; font.pixelSize: 11; font.family: "Menlo" }
                                Item { Layout.fillWidth: true }
                                Rectangle {
                                    width: valLbl3.implicitWidth + 20; height: 26; radius: 5
                                    color: Qt.rgba(1,1,1,0.05); border.color: Qt.rgba(1,1,1,0.09); border.width: 1
                                    Text { id: valLbl3; anchors.centerIn: parent; text: modelData.val; color: "#A9B5C2"
                                           font.pixelSize: 11; font.family: "Menlo" }
                                }
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }
            }
        }
    }

    component SettingInput: Rectangle {
        id: fieldRoot
        required property string label
        required property string keyName
        property string valueText: ""
        Layout.fillWidth: true
        height: 48
        radius: 7
        color: Qt.rgba(1,1,1,0.035)
        border.color: Qt.rgba(1,1,1,0.09)
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 8
            spacing: 8
            Text {
                Layout.fillWidth: true
                text: fieldRoot.label
                color: "#6F7E8E"
                font.pixelSize: 10
                font.family: "Menlo"
                elide: Text.ElideRight
            }
            Rectangle {
                width: 116
                height: 28
                radius: 5
                color: Qt.rgba(0,0,0,0.18)
                border.color: input.activeFocus ? Qt.rgba(0.561,0.643,0.722,0.45) : Qt.rgba(1,1,1,0.10)
                border.width: 1
                TextInput {
                    id: input
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    verticalAlignment: TextInput.AlignVCenter
                    text: fieldRoot.valueText
                    color: "#A9B5C2"
                    selectionColor: "#26384A"
                    selectedTextColor: "#E6ECF3"
                    font.pixelSize: 10
                    font.family: "Menlo"
                    clip: true
                    onEditingFinished: if (settingsBridge) settingsBridge.setValue(fieldRoot.keyName, text)
                }
            }
        }
    }
}
