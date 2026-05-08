import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: "#0C1219"
    focus: visible

    signal closed()

    onVisibleChanged: if (visible && dtsBridge) dtsBridge.reload()

    Timer {
        interval: 1800
        running: root.visible
        repeat: true
        onTriggered: if (dtsBridge) dtsBridge.reload()
    }

    function statusColor(s) {
        var v = (s || "").toUpperCase()
        if (v === "ACCEPTED") return "#52D273"
        if (v === "REJECTED") return "#E26B6B"
        if (v === "STAGED") return "#E8B547"
        return "#8FA4B8"
    }

    function qualityRows() {
        if (!dtsBridge) return []
        try { return JSON.parse(dtsBridge.selectedQualityRows) }
        catch (e) { return [] }
    }

    function setFilter(filter) {
        if (dtsBridge) dtsBridge.setFilter(filter)
    }

    function selected() {
        return dtsBridge && dtsBridge.selectedRecordId !== ""
    }

    Keys.onEscapePressed: root.closed()

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            height: 48
            color: "transparent"
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#1C2A38" }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 12
                spacing: 10

                Text {
                    text: "DTS · TRAINING DESK"
                    color: "#E6ECF3"
                    font.pixelSize: 13
                    font.family: "Menlo"
                    font.letterSpacing: 2
                }

                Text {
                    text: dtsBridge ? dtsBridge.totalCount + " записей" : "0 записей"
                    color: "#4A5E6E"
                    font.pixelSize: 10
                    font.family: "Menlo"
                }

                Item { Layout.fillWidth: true }

                Repeater {
                    model: [
                        {label:"ОЧЕРЕДЬ",  filter:"new"},
                        {label:"ACCEPTED", filter:"accepted"},
                        {label:"FAIL",     filter:"accepted_fail"},
                        {label:"REJECTED", filter:"rejected"},
                        {label:"ALL",      filter:"all"},
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        width: chipLbl.implicitWidth + 18
                        height: 24
                        radius: 6
                        property bool active: dtsBridge && dtsBridge.currentFilter === modelData.filter.toUpperCase()
                        color: active ? Qt.rgba(0.561, 0.643, 0.722, 0.14) : "transparent"
                        border.color: active ? Qt.rgba(0.561, 0.643, 0.722, 0.45) : Qt.rgba(1,1,1,0.10)
                        border.width: 1
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.setFilter(modelData.filter)
                        }
                        Text {
                            id: chipLbl
                            anchors.centerIn: parent
                            text: modelData.label + " " + (dtsBridge ? dtsBridge.countStatus(modelData.filter) : 0)
                            color: parent.active ? "#E6ECF3" : "#6F7E8E"
                            font.pixelSize: 10
                            font.family: "Menlo"
                            font.letterSpacing: 1
                        }
                    }
                }

                Rectangle {
                    width: 34
                    height: 28
                    radius: 6
                    color: reloadArea.containsMouse ? Qt.rgba(0.561,0.643,0.722,0.14) : "transparent"
                    border.color: Qt.rgba(0.561,0.643,0.722,0.30)
                    border.width: 1
                    MouseArea {
                        id: reloadArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: if (dtsBridge) dtsBridge.reload()
                    }
                    Text { anchors.centerIn: parent; text: "⟳"; color: "#8FA4B8"; font.pixelSize: 13; font.family: "Menlo" }
                }

                Rectangle {
                    width: 72
                    height: 28
                    radius: 6
                    color: closeArea.containsMouse ? Qt.rgba(0.886,0.420,0.420,0.12) : "transparent"
                    border.color: Qt.rgba(0.886,0.420,0.420,0.35)
                    border.width: 1
                    MouseArea {
                        id: closeArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.closed()
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "ЗАКРЫТЬ"
                        color: "#E26B6B"
                        font.pixelSize: 10
                        font.family: "Menlo"
                        font.letterSpacing: 1
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.preferredWidth: 320
                Layout.fillHeight: true
                color: "#0A1018"

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true
                        height: 44
                        color: "#080D12"
                        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#1C2A38" }
                        TextInput {
                            id: searchInput
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            verticalAlignment: TextInput.AlignVCenter
                            color: "#A9B5C2"
                            selectionColor: "#26384A"
                            selectedTextColor: "#E6ECF3"
                            font.pixelSize: 11
                            font.family: "Menlo"
                            clip: true
                            onTextChanged: if (dtsBridge) dtsBridge.setSearch(text)
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                visible: searchInput.text.length === 0
                                text: "ПОИСК: ID, КАДР, ФАЙЛ..."
                                color: "#35495A"
                                font.pixelSize: 10
                                font.family: "Menlo"
                                font.letterSpacing: 1
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 32
                        color: "#080D12"
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 10
                            spacing: 0
                            Text { Layout.preferredWidth: 86; text: "ID"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.8 }
                            Text { Layout.preferredWidth: 56; text: "КАДР"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.8 }
                            Text { Layout.fillWidth: true; text: "СТАТУС"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.8 }
                        }
                    }

                    ListView {
                        id: annList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: dtsRecordsModel
                        delegate: Rectangle {
                            required property int index
                            required property string recordId
                            required property string shortId
                            required property int frame
                            required property string status
                            required property string clip
                            required property string bbox
                            width: annList.width
                            height: 38
                            color: dtsBridge && index === dtsBridge.selectedIndex ? Qt.rgba(0.561,0.643,0.722,0.09) : "transparent"
                            Rectangle { visible: dtsBridge && index === dtsBridge.selectedIndex; width: 3; height: parent.height; color: "#8FA4B8" }
                            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Qt.rgba(1,1,1,0.04) }
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: if (dtsBridge) dtsBridge.selectIndex(index)
                            }
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 10
                                spacing: 0
                                Text { Layout.preferredWidth: 86; text: shortId; color: "#A9B5C2"; font.pixelSize: 10; font.family: "Menlo" }
                                Text { Layout.preferredWidth: 56; text: frame; color: "#6F7E8E"; font.pixelSize: 10; font.family: "Menlo" }
                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 18
                                    radius: 4
                                    color: "transparent"
                                    border.color: root.statusColor(status)
                                    border.width: 1
                                    Text { anchors.centerIn: parent; text: status; color: root.statusColor(status); font.pixelSize: 8; font.family: "Menlo" }
                                }
                            }
                        }
                    }
                }
            }

            Rectangle { width: 1; Layout.fillHeight: true; color: "#1C2A38" }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#080D12"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "#050810"
                        radius: 8
                        clip: true
                        border.color: "#1C2A38"
                        border.width: 1

                        Image {
                            anchors.fill: parent
                            anchors.margins: 1
                            source: dtsBridge ? dtsBridge.previewSource : ""
                            fillMode: Image.PreserveAspectFit
                            cache: false
                            asynchronous: false
                            visible: root.selected()
                        }

                        Text {
                            anchors.centerIn: parent
                            visible: !root.selected()
                            text: "НЕТ DTS ЗАПИСЕЙ"
                            color: Qt.rgba(0.561,0.643,0.722,0.16)
                            font.pixelSize: 20
                            font.family: "Menlo"
                            font.letterSpacing: 5
                        }

                        Rectangle {
                            anchors.top: parent.top
                            anchors.right: parent.right
                            anchors.margins: 10
                            width: previewChipRow.implicitWidth + 14
                            height: 24
                            radius: 4
                            color: Qt.rgba(0,0,0,0.62)
                            border.color: Qt.rgba(1,1,1,0.12)
                            border.width: 1
                            visible: root.selected()
                            Row {
                                id: previewChipRow
                                anchors.centerIn: parent
                                spacing: 8
                                Text { text: dtsBridge ? dtsBridge.selectedClip : "—"; color: "#8FA4B8"; font.pixelSize: 10; font.family: "Menlo" }
                                Rectangle { width: 1; height: 12; color: Qt.rgba(1,1,1,0.15); anchors.verticalCenter: parent.verticalCenter }
                                Text { text: "F " + (dtsBridge ? dtsBridge.selectedFrame : "—"); color: "#A9B5C2"; font.pixelSize: 10; font.family: "Menlo" }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: [
                                {label:"ПРИНЯТЬ",   color:"#52D273", status:"accepted"},
                                {label:"ОТКЛОНИТЬ", color:"#E26B6B", status:"rejected"},
                            ]
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                height: 36
                                radius: 6
                                color: actionMa.containsMouse ? Qt.rgba(1,1,1,0.035) : "transparent"
                                border.color: modelData.color
                                border.width: 1
                                opacity: root.selected() ? 0.86 : 0.30
                                MouseArea {
                                    id: actionMa
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: root.selected() ? Qt.PointingHandCursor : Qt.ArrowCursor
                                    onClicked: if (root.selected() && dtsBridge) dtsBridge.setSelectedStatus(modelData.status)
                                }
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.label
                                    color: modelData.color
                                    font.pixelSize: 10
                                    font.family: "Menlo"
                                    font.letterSpacing: 1.5
                                }
                            }
                        }

                    }
                }
            }

            Rectangle { width: 1; Layout.fillHeight: true; color: "#1C2A38" }

            Rectangle {
                Layout.preferredWidth: 340
                Layout.fillHeight: true
                color: "#0A1018"
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 10

                    Text { text: "RECORD"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 2 }
                    Text { text: dtsBridge ? dtsBridge.selectedShortId : "—"; color: "#E6ECF3"; font.pixelSize: 18; font.family: "Menlo" }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 28
                        radius: 5
                        color: Qt.rgba(0,0,0,0.22)
                        border.color: root.statusColor(dtsBridge ? dtsBridge.selectedStatus : "")
                        border.width: 1
                        Text {
                            anchors.centerIn: parent
                            text: "СТАТУС · " + (dtsBridge ? dtsBridge.selectedStatus : "—")
                            color: root.statusColor(dtsBridge ? dtsBridge.selectedStatus : "")
                            font.pixelSize: 10
                            font.family: "Menlo"
                            font.letterSpacing: 1
                        }
                    }

                    Text { text: "QUALITY · " + (dtsBridge ? dtsBridge.selectedQuality : "—"); color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.5 }

                    ListView {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 170
                        clip: true
                        model: root.qualityRows()
                        delegate: RowLayout {
                            required property var modelData
                            width: parent ? parent.width : 320
                            height: 22
                            spacing: 8
                            Text {
                                Layout.preferredWidth: 18
                                text: modelData.state === "ok" ? "●" : modelData.state === "warn" ? "●" : modelData.state === "fail" ? "●" : "○"
                                color: modelData.state === "ok" ? "#52D273" : modelData.state === "warn" ? "#E8B547" : modelData.state === "fail" ? "#E26B6B" : "#4A5E6E"
                                font.pixelSize: 10
                                font.family: "Menlo"
                            }
                            Text { Layout.preferredWidth: 98; text: modelData.name; color: "#8FA4B8"; font.pixelSize: 10; font.family: "Menlo"; elide: Text.ElideRight }
                            Text {
                                Layout.fillWidth: true
                                text: (modelData.value || "—") + (modelData.note ? " · " + modelData.note : "")
                                color: "#4A5E6E"
                                font.pixelSize: 10
                                font.family: "Menlo"
                                elide: Text.ElideRight
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.minimumHeight: 160
                        implicitHeight: candidateCol.implicitHeight + 20
                        radius: 7
                        color: Qt.rgba(0.322,0.824,0.451,0.045)
                        border.color: Qt.rgba(0.322,0.824,0.451,0.20)
                        border.width: 1
                        ColumnLayout {
                            id: candidateCol
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            Text {
                                text: "КАНДИДАТ"
                                color: "#52D273"
                                font.pixelSize: 10
                                font.family: "Menlo"
                                font.letterSpacing: 2
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text { text: "КАДРОВ"; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.5 }
                                Text { text: dtsBridge ? dtsBridge.candidateFrameCount : 0; color: "#E6ECF3"; font.pixelSize: 22; font.family: "Menlo" }
                                Item { Layout.fillWidth: true }
                            }

                            Text {
                                Layout.fillWidth: true
                                text: dtsBridge ? dtsBridge.candidateSummary : "accepted 0"
                                color: "#8FA4B8"
                                font.pixelSize: 9
                                font.family: "Menlo"
                                wrapMode: Text.Wrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.fillWidth: true
                                text: dtsBridge && dtsBridge.candidatePackDir !== "" ? "PACK · " + dtsBridge.candidatePackDir + " · ok " + dtsBridge.candidatePackOkCount : "PACK · не собран"
                                color: dtsBridge && dtsBridge.candidatePackOkCount > 0 ? "#52D273" : "#4A5E6E"
                                font.pixelSize: 8
                                font.family: "Menlo"
                                elide: Text.ElideRight
                            }

                            // -- compare status block (Task 1) --
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                visible: (dtsBridge && dtsBridge.compareStatus !== "NOT_RUN") || (dtsBridge && dtsBridge.compareRunning)

                                // status badge + N/M counts
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 6

                                    Rectangle {
                                        width: statusBadgeTxt.implicitWidth + 10
                                        height: 16
                                        radius: 3
                                        color: {
                                            var s = dtsBridge ? dtsBridge.compareStatus : ""
                                            if (s === "PASS") return Qt.rgba(0.322,0.824,0.451,0.18)
                                            if (s === "RUNNING") return Qt.rgba(0.910,0.710,0.280,0.18)
                                            if (s === "RETUNE") return Qt.rgba(0.910,0.710,0.280,0.18)
                                            return Qt.rgba(0.886,0.420,0.420,0.18)
                                        }
                                        Text {
                                            id: statusBadgeTxt
                                            anchors.centerIn: parent
                                            text: dtsBridge ? dtsBridge.compareStatus : "—"
                                            color: {
                                                var s = dtsBridge ? dtsBridge.compareStatus : ""
                                                if (s === "PASS") return "#52D273"
                                                if (s === "RUNNING") return "#E8B547"
                                                if (s === "RETUNE") return "#E8B547"
                                                return "#E26B6B"
                                            }
                                            font.pixelSize: 9; font.family: "Menlo"; font.letterSpacing: 1.2
                                        }
                                    }

                                    Text {
                                        text: "base " + (dtsBridge ? dtsBridge.compareBaselinePassN : 0) + "/" + (dtsBridge ? dtsBridge.compareBaselineTotalN : 0)
                                        color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo"
                                    }
                                    Text {
                                        text: "cand " + (dtsBridge ? dtsBridge.compareCandidatePassN : 0) + "/" + (dtsBridge ? dtsBridge.compareCandidateTotalN : 0)
                                        color: "#8FA4B8"; font.pixelSize: 9; font.family: "Menlo"
                                    }
                                    Item { Layout.fillWidth: true }
                                }

                                // per-context rows
                                Repeater {
                                    model: {
                                        if (!dtsBridge) return []
                                        try { return JSON.parse(dtsBridge.compareContextsJson) }
                                        catch(e) { return [] }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 4
                                        Text {
                                            text: (modelData.name || "?").toUpperCase()
                                            color: modelData.passed ? "#52D273" : "#E26B6B"
                                            font.pixelSize: 8; font.family: "Menlo"; font.letterSpacing: 1
                                            Layout.preferredWidth: 26
                                        }
                                        Text {
                                            text: "pres " + (modelData.presence !== undefined ? modelData.presence.toFixed(2) : "—")
                                            color: "#8FA4B8"; font.pixelSize: 8; font.family: "Menlo"
                                        }
                                        Text {
                                            visible: modelData.delta_presence !== undefined
                                            text: (modelData.delta_presence >= 0 ? "+" : "") + (modelData.delta_presence !== undefined ? modelData.delta_presence.toFixed(2) : "")
                                            color: modelData.delta_presence >= 0 ? "#52D273" : "#E26B6B"
                                            font.pixelSize: 8; font.family: "Menlo"
                                        }
                                        Text {
                                            text: "fl " + (modelData.false_lock !== undefined ? modelData.false_lock.toFixed(2) : "—")
                                            color: "#8FA4B8"; font.pixelSize: 8; font.family: "Menlo"
                                        }
                                        Text {
                                            text: "id " + (modelData.id_changes !== undefined ? modelData.id_changes.toFixed(1) : "—")
                                            color: "#8FA4B8"; font.pixelSize: 8; font.family: "Menlo"
                                        }
                                    }
                                }

                                // result dir
                                Text {
                                    Layout.fillWidth: true
                                    visible: dtsBridge && dtsBridge.compareResultDir !== ""
                                    text: dtsBridge ? dtsBridge.compareResultDir : ""
                                    color: "#2A3E50"
                                    font.pixelSize: 7; font.family: "Menlo"
                                    elide: Text.ElideLeft
                                }
                            }

                            // -- segmented progress bar (Task 2, replaces indeterminate) --
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                visible: dtsBridge && dtsBridge.compareRunning

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text {
                                        text: dtsBridge && dtsBridge.compareTotal > 0
                                            ? "шаг " + dtsBridge.compareStep + "/" + dtsBridge.compareTotal
                                            : "..."
                                        color: "#E8B547"; font.pixelSize: 8; font.family: "Menlo"
                                    }
                                    Text {
                                        text: dtsBridge && dtsBridge.compareContextLabel !== "" ? "· " + dtsBridge.compareContextLabel : ""
                                        color: "#4A5E6E"; font.pixelSize: 8; font.family: "Menlo"
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 5
                                    radius: 3
                                    color: Qt.rgba(0.561,0.643,0.722,0.10)
                                    Rectangle {
                                        width: {
                                            if (!dtsBridge || dtsBridge.compareTotal <= 0) return 0
                                            return parent.width * dtsBridge.compareStep / dtsBridge.compareTotal
                                        }
                                        height: parent.height
                                        radius: 3
                                        color: "#E8B547"
                                        opacity: 0.9
                                        Behavior on width { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                                    }
                                }
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                rowSpacing: 8
                                columnSpacing: 8

                                Rectangle {
                                    Layout.fillWidth: true; height: 34; radius: 6
                                    color: assembleMa.containsMouse ? Qt.rgba(0.322,0.824,0.451,0.13) : Qt.rgba(0.322,0.824,0.451,0.06)
                                    border.color: Qt.rgba(0.322,0.824,0.451,0.34); border.width: 1
                                    MouseArea { id: assembleMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: if (dtsBridge) dtsBridge.assembleCandidate() }
                                    Text { anchors.centerIn: parent; text: "СОБРАТЬ"; color: "#52D273"; font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1.2 }
                                }

                                Rectangle {
                                    Layout.fillWidth: true; height: 34; radius: 6
                                    color: trainMa.containsMouse ? Qt.rgba(0.561,0.643,0.722,0.12) : Qt.rgba(0.561,0.643,0.722,0.06)
                                    border.color: Qt.rgba(0.561,0.643,0.722,0.30); border.width: 1
                                    MouseArea { id: trainMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: if (dtsBridge) dtsBridge.trainCandidate() }
                                    Text { anchors.centerIn: parent; text: "ОБУЧИТЬ"; color: "#8FA4B8"; font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1.2 }
                                }

                                Rectangle {
                                    Layout.fillWidth: true; height: 34; radius: 6
                                    enabled: !(dtsBridge && dtsBridge.compareRunning)
                                    opacity: enabled ? 1.0 : 0.55
                                    color: compareMa.containsMouse && enabled ? Qt.rgba(0.561,0.643,0.722,0.12) : Qt.rgba(0.561,0.643,0.722,0.06)
                                    border.color: Qt.rgba(0.561,0.643,0.722,0.30); border.width: 1
                                    MouseArea { id: compareMa; anchors.fill: parent; hoverEnabled: true; cursorShape: parent.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: if (dtsBridge && parent.enabled) dtsBridge.compareCandidate() }
                                    Text { anchors.centerIn: parent; text: dtsBridge && dtsBridge.compareRunning ? "ИДЕТ..." : "СРАВНИТЬ"; color: "#8FA4B8"; font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1.2 }
                                }

                                Rectangle {
                                    Layout.fillWidth: true; height: 34; radius: 6
                                    color: acceptMa.containsMouse ? Qt.rgba(0.886,0.420,0.420,0.11) : Qt.rgba(0.886,0.420,0.420,0.045)
                                    border.color: Qt.rgba(0.886,0.420,0.420,0.28); border.width: 1
                                    MouseArea { id: acceptMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: if (dtsBridge) dtsBridge.acceptCandidate() }
                                    Text { anchors.centerIn: parent; text: "ПРИНЯТЬ"; color: "#E26B6B"; font.pixelSize: 10; font.family: "Menlo"; font.letterSpacing: 1.2 }
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }

                    Text {
                        Layout.fillWidth: true
                        text: dtsBridge ? dtsBridge.lastMessage : "—"
                        color: "#4A5E6E"
                        font.pixelSize: 10
                        font.family: "Menlo"
                        wrapMode: Text.Wrap
                        maximumLineCount: 4
                        elide: Text.ElideRight
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: "#0A1018"
            Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: "#1C2A38" }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 20
                Repeater {
                    model: [
                        {s:"new",      label:"NEW",      c:"#8FA4B8"},
                        {s:"accepted", label:"ACCEPTED", c:"#52D273"},
                        {s:"rejected", label:"REJECTED", c:"#E26B6B"},
                    ]
                    delegate: RowLayout {
                        required property var modelData
                        spacing: 6
                        Text { text: modelData.label; color: "#4A5E6E"; font.pixelSize: 9; font.family: "Menlo" }
                        Text { text: dtsBridge ? dtsBridge.countStatus(modelData.s) : 0; color: modelData.c; font.pixelSize: 11; font.family: "Menlo" }
                    }
                }
                Item { Layout.fillWidth: true }
                Text { text: dtsBridge ? dtsBridge.duplicateSummary : "0 records"; color: "#4A5E6E"; font.pixelSize: 10; font.family: "Menlo" }
                Text { text: "ВСЕГО: " + (dtsBridge ? dtsBridge.totalCount : 0); color: "#4A5E6E"; font.pixelSize: 10; font.family: "Menlo" }
            }
        }
    }
}
