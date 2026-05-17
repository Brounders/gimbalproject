import QtQuick 2.15

Rectangle {
    id: videoRoot
    color: "#060A0D"
    implicitWidth: 400

    property string trackingState: "SEARCH"
    property string targetLifecycle: "SEARCH"
    property bool   isRunning:     false
    property int    targetId:      1
    property real   confidence:    0.0
    property string currentMode:   "ДЕНЬ"
    property int    fps:           0
    property int    frameId:       0
    property bool   markBBoxFlash: false
    property int    frameWidth:    0
    property int    frameHeight:   0
    property string activeBboxJson: "[]"
    property string displayTargetsJson: "[]"

    signal targetClicked(int frameX, int frameY)

    // Internal animation state
    property real _t:  0.0
    property real _tx: 0.5   // target X [0..1]
    property real _ty: 0.5   // target Y [0..1]
    property real _clickFxX: -100
    property real _clickFxY: -100
    property bool _clickFxVisible: false

    onActiveBboxJsonChanged: overlay.requestPaint()
    onDisplayTargetsJsonChanged: overlay.requestPaint()
    onFrameWidthChanged: overlay.requestPaint()
    onFrameHeightChanged: overlay.requestPaint()
    onFrameIdChanged: overlay.requestPaint()
    onIsRunningChanged: overlay.requestPaint()
    onMarkBBoxFlashChanged: overlay.requestPaint()
    onTargetLifecycleChanged: overlay.requestPaint()

    Timer {
        id: clickFxTimer
        interval: 520
        onTriggered: {
            videoRoot._clickFxVisible = false
            overlay.requestPaint()
        }
    }

    function _frameScale() {
        if (frameWidth <= 0 || frameHeight <= 0) return 1.0
        return Math.max(width / frameWidth, height / frameHeight)
    }

    function _frameOffsetX() {
        if (frameWidth <= 0 || frameHeight <= 0) return 0
        return (width - frameWidth * _frameScale()) / 2
    }

    function _frameOffsetY() {
        if (frameWidth <= 0 || frameHeight <= 0) return 0
        return (height - frameHeight * _frameScale()) / 2
    }

    function frameToViewX(x) {
        return _frameOffsetX() + x * _frameScale()
    }

    function frameToViewY(y) {
        return _frameOffsetY() + y * _frameScale()
    }

    function viewToFrameX(x) {
        if (frameWidth <= 0) return 0
        return Math.max(0, Math.min(frameWidth - 1, Math.round((x - _frameOffsetX()) / _frameScale())))
    }

    function viewToFrameY(y) {
        if (frameHeight <= 0) return 0
        return Math.max(0, Math.min(frameHeight - 1, Math.round((y - _frameOffsetY()) / _frameScale())))
    }

    function parseJsonArray(text) {
        try {
            var parsed = JSON.parse(text)
            return Array.isArray(parsed) ? parsed : []
        } catch (e) {
            return []
        }
    }

    Image {
        id: liveFrame
        anchors.fill: parent
        visible: videoRoot.isRunning && videoRoot.frameId > 0
        source: visible ? ("image://frames/current?" + videoRoot.frameId) : ""
        fillMode: Image.PreserveAspectCrop
        cache: false
        asynchronous: true
    }

    Canvas {
        id: overlay
        anchors.fill: parent
        z: 20
        visible: videoRoot.isRunning && videoRoot.frameId > 0

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            if (!videoRoot.isRunning || videoRoot.frameWidth <= 0 || videoRoot.frameHeight <= 0) return

            var targets = videoRoot.parseJsonArray(videoRoot.displayTargetsJson)
            var drawnActive = false
            for (var i = 0; i < targets.length; i++) {
                var target = targets[i]
                if (!target.bbox || target.bbox.length < 4) continue
                if (target.active) drawnActive = true
                drawTarget(ctx, target.bbox, target.active, target.id, target.conf, i)
            }

            if (!drawnActive) {
                var active = videoRoot.parseJsonArray(videoRoot.activeBboxJson)
                if (active.length >= 4) drawTarget(ctx, active, true, videoRoot.targetId, videoRoot.confidence, 0)
            }
            drawClickFeedback(ctx)
        }

        function drawClickFeedback(ctx) {
            if (!videoRoot._clickFxVisible) return
            var x = videoRoot._clickFxX
            var y = videoRoot._clickFxY
            ctx.save()
            ctx.strokeStyle = "rgba(82,210,115,0.95)"
            ctx.lineWidth = 1.4
            ctx.beginPath(); ctx.arc(x, y, 14, 0, Math.PI * 2); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(x - 24, y); ctx.lineTo(x - 8, y); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(x + 8, y); ctx.lineTo(x + 24, y); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(x, y - 24); ctx.lineTo(x, y - 8); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(x, y + 8); ctx.lineTo(x, y + 24); ctx.stroke()
            ctx.fillStyle = videoRoot.targetLifecycle === "VERIFYING" ? "rgba(232,181,71,0.95)" : "rgba(82,210,115,0.95)"
            ctx.font = "bold 10px monospace"
            ctx.fillText(videoRoot.targetLifecycle === "VERIFYING" ? "VERIFYING" : "SELECT", x + 18, y - 16)
            ctx.restore()
        }

        function drawTarget(ctx, bbox, active, targetId, conf, index) {
            var x1 = videoRoot.frameToViewX(bbox[0])
            var y1 = videoRoot.frameToViewY(bbox[1])
            var x2 = videoRoot.frameToViewX(bbox[2])
            var y2 = videoRoot.frameToViewY(bbox[3])
            var w = Math.max(16, x2 - x1)
            var h = Math.max(16, y2 - y1)
            var color = active ? "#52D273" : "#E8B547"
            var alpha = active ? 0.95 : 0.64
            var corner = active ? 18 : 12
            ctx.save()
            ctx.strokeStyle = active ? "rgba(82,210,115," + alpha + ")" : "rgba(232,181,71," + alpha + ")"
            ctx.lineWidth = active ? (videoRoot.markBBoxFlash ? 3.0 : 2.0) : 1.3
            ctx.setLineDash(active ? [] : [7, 5])
            ctx.lineCap = "square"

            ctx.beginPath(); ctx.moveTo(x1, y1 + corner); ctx.lineTo(x1, y1); ctx.lineTo(x1 + corner, y1); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(x1 + w - corner, y1); ctx.lineTo(x1 + w, y1); ctx.lineTo(x1 + w, y1 + corner); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(x1, y1 + h - corner); ctx.lineTo(x1, y1 + h); ctx.lineTo(x1 + corner, y1 + h); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(x1 + w - corner, y1 + h); ctx.lineTo(x1 + w, y1 + h); ctx.lineTo(x1 + w, y1 + h - corner); ctx.stroke()
            ctx.setLineDash([])

            var label = active ? "АКТИВНАЯ T-" : "КАНДИДАТ T-"
            label += (targetId < 10 ? "0" : "") + targetId
            if (!active) label += "  " + Math.round((conf || 0) * 100) + "%"
            ctx.font = active ? "bold 11px monospace" : "10px monospace"
            var labelW = ctx.measureText(label).width + 14
            var labelH = 18
            var lx = Math.max(8, Math.min(width - labelW - 8, x1))
            var ly = Math.max(8, y1 - labelH - 5)
            ctx.fillStyle = active ? "rgba(5,12,20,0.78)" : "rgba(5,12,20,0.58)"
            ctx.fillRect(lx, ly, labelW, labelH)
            ctx.fillStyle = color
            ctx.fillRect(lx, ly, 3, labelH)
            ctx.fillStyle = active ? "rgba(82,210,115,1.0)" : "rgba(232,181,71,0.95)"
            ctx.fillText(label, lx + 7, ly + 13)

            if (active) {
                var cx = x1 + w / 2
                var cy = y1 + h / 2
                ctx.strokeStyle = "rgba(82,210,115,0.56)"
                ctx.lineWidth = 1.0
                ctx.beginPath(); ctx.moveTo(cx - 12, cy); ctx.lineTo(cx - 4, cy); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(cx + 4, cy); ctx.lineTo(cx + 12, cy); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(cx, cy - 12); ctx.lineTo(cx, cy - 4); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(cx, cy + 4); ctx.lineTo(cx, cy + 12); ctx.stroke()
            }
            ctx.restore()
        }
    }

    MouseArea {
        anchors.fill: parent
        z: 100
        enabled: videoRoot.isRunning
        hoverEnabled: true
        cursorShape: videoRoot.isRunning ? Qt.CrossCursor : Qt.ArrowCursor
        acceptedButtons: Qt.LeftButton
        onClicked: function(mouse) {
            videoRoot._clickFxX = mouse.x
            videoRoot._clickFxY = mouse.y
            videoRoot._clickFxVisible = true
            clickFxTimer.restart()
            overlay.requestPaint()
            videoRoot.targetClicked(videoRoot.viewToFrameX(mouse.x), videoRoot.viewToFrameY(mouse.y))
        }
    }

    // Animated canvas
    Canvas {
        id: cvs
        anchors.fill: parent
        visible: !(videoRoot.isRunning && videoRoot.frameId > 0)

        Timer {
            interval: 33
            running: true
            repeat: true
            onTriggered: {
                videoRoot._t  += 0.018
                videoRoot._tx = 0.5 + Math.sin(videoRoot._t * 0.38) * 0.28
                videoRoot._ty = 0.5 + Math.cos(videoRoot._t * 0.27) * 0.22
                cvs.requestPaint()
            }
        }

        onPaint: {
            var ctx = getContext("2d")
            var W = width, H = height
            var t  = videoRoot._t
            var tx = videoRoot._tx * W
            var ty = videoRoot._ty * H
            var running = videoRoot.isRunning
            var state   = videoRoot.trackingState
            var mode    = videoRoot.currentMode

            // Mode tint channels [R,G,B]
            var mc = mode === "ИК"   ? [200, 100,  50]
                   : mode === "НОЧЬ" ? [ 50, 190, 110]
                   : [90, 150, 210]

            // State color channels
            var sc = state === "LOCK"  ? [82,  210, 115]
                   : state === "TRACK" ? [143, 164, 184]
                   : state === "LOST"  ? [226, 107, 107]
                   : [232, 181, 71]

            // ── Clear ─────────────────────────────────────────────
            ctx.fillStyle = "#060A0D"
            ctx.fillRect(0, 0, W, H)

            // ── Background gradient (mode tint) ───────────────────
            var bgGrad = ctx.createRadialGradient(W*0.55, H*0.4, 0, W*0.55, H*0.4, W*0.6)
            bgGrad.addColorStop(0, "rgba(" + mc[0]+","+mc[1]+","+mc[2]+",0.06)")
            bgGrad.addColorStop(1, "rgba(0,0,0,0)")
            ctx.fillStyle = bgGrad
            ctx.fillRect(0, 0, W, H)

            // ── Terrain blobs (slow camera drift) ─────────────────
            var camX = Math.sin(t * 0.04) * 0.08
            var camY = Math.cos(t * 0.033) * 0.06
            var blobs = [
                {bx:0.18, by:0.28, br:0.07},
                {bx:0.65, by:0.72, br:0.06},
                {bx:0.80, by:0.18, br:0.09},
                {bx:0.40, by:0.82, br:0.05},
                {bx:0.72, by:0.45, br:0.07},
                {bx:0.30, by:0.55, br:0.04},
            ]
            for (var i = 0; i < blobs.length; i++) {
                var bx = (blobs[i].bx + camX) * W
                var by = (blobs[i].by + camY) * H
                var br = blobs[i].br * Math.min(W, H)
                var bGrad = ctx.createRadialGradient(bx, by, 0, bx, by, br)
                bGrad.addColorStop(0, "rgba(" + mc[0]+","+mc[1]+","+mc[2]+",0.07)")
                bGrad.addColorStop(1, "rgba(0,0,0,0)")
                ctx.fillStyle = bGrad
                ctx.beginPath()
                ctx.arc(bx, by, br, 0, Math.PI*2)
                ctx.fill()
            }

            // ── Tactical grid ─────────────────────────────────────
            ctx.strokeStyle = "rgba(" + mc[0]+","+mc[1]+","+mc[2]+",0.045)"
            ctx.lineWidth = 0.5
            var gs = 60
            for (var gx = 0; gx < W; gx += gs) {
                ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, H); ctx.stroke()
            }
            for (var gy = 0; gy < H; gy += gs) {
                ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(W, gy); ctx.stroke()
            }

            // ── Scan line ─────────────────────────────────────────
            var scanY = ((t * 22) % (H + 40)) - 20
            var scanGrad = ctx.createLinearGradient(0, scanY, 0, scanY + 28)
            scanGrad.addColorStop(0, "rgba(" + mc[0]+","+mc[1]+","+mc[2]+",0)")
            scanGrad.addColorStop(0.6, "rgba(" + mc[0]+","+mc[1]+","+mc[2]+",0.07)")
            scanGrad.addColorStop(1, "rgba(" + mc[0]+","+mc[1]+","+mc[2]+",0)")
            ctx.fillStyle = scanGrad
            ctx.fillRect(0, scanY, W, 28)

            // ── Target (only when running) ────────────────────────
            if (running) {
                var col = "rgba(" + sc[0]+","+sc[1]+","+sc[2]+","

                // Glow halo (larger, more visible)
                var halo = ctx.createRadialGradient(tx, ty, 0, tx, ty, 110)
                halo.addColorStop(0, col + "0.18)")
                halo.addColorStop(0.4, col + "0.08)")
                halo.addColorStop(1, col + "0)")
                ctx.fillStyle = halo
                ctx.beginPath(); ctx.arc(tx, ty, 110, 0, Math.PI*2); ctx.fill()

                // BBox (wider, more like reference)
                var bw = 54, bh = 26
                var pad = 18
                var bbx = tx - bw/2 - pad
                var bby = ty - bh/2 - pad
                var bbw = bw + pad*2
                var bbh = bh + pad*2
                var cl  = 14

                // Target body (filled rect, no roundRect for compatibility)
                ctx.fillStyle = col + "0.35)"
                ctx.fillRect(tx - bw/2, ty - bh/2, bw, bh)

                // BBox corners (thicker)
                var alpha = videoRoot.markBBoxFlash ? 1.0 : 0.92
                ctx.strokeStyle = col + alpha + ")"
                ctx.lineWidth = videoRoot.markBBoxFlash ? 3.0 : 2.0
                ctx.lineCap = "square"
                // TL
                ctx.beginPath(); ctx.moveTo(bbx, bby+cl); ctx.lineTo(bbx, bby); ctx.lineTo(bbx+cl, bby); ctx.stroke()
                // TR
                ctx.beginPath(); ctx.moveTo(bbx+bbw-cl, bby); ctx.lineTo(bbx+bbw, bby); ctx.lineTo(bbx+bbw, bby+cl); ctx.stroke()
                // BL
                ctx.beginPath(); ctx.moveTo(bbx, bby+bbh-cl); ctx.lineTo(bbx, bby+bbh); ctx.lineTo(bbx+cl, bby+bbh); ctx.stroke()
                // BR
                ctx.beginPath(); ctx.moveTo(bbx+bbw-cl, bby+bbh); ctx.lineTo(bbx+bbw, bby+bbh); ctx.lineTo(bbx+bbw, bby+bbh-cl); ctx.stroke()

                // Target marker above bbox
                var idStr    = "T-" + (videoRoot.targetId < 10 ? "0" : "") + videoRoot.targetId
                var labelStr = idStr
                ctx.font = "bold 11px monospace"
                var lw = ctx.measureText(labelStr).width + 16
                var lx = bbx, ly = bby - 22
                // Dark pill background
                ctx.fillStyle = "rgba(5,12,20,0.75)"
                ctx.fillRect(lx, ly, lw, 18)
                // Colored left edge
                ctx.fillStyle = col + "0.85)"
                ctx.fillRect(lx, ly, 3, 18)
                // Text
                ctx.fillStyle = col + "1.0)"
                ctx.fillText(labelStr, lx + 7, ly + 13)

                // Mini crosshair at target center
                var iArm = 9, iGap = 3
                ctx.strokeStyle = col + "0.65)"
                ctx.lineWidth = 1.0
                ctx.lineCap = "round"
                ctx.beginPath(); ctx.moveTo(tx-iArm-iGap, ty); ctx.lineTo(tx-iGap, ty); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(tx+iGap, ty);      ctx.lineTo(tx+iArm+iGap, ty); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(tx, ty-iArm-iGap); ctx.lineTo(tx, ty-iGap); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(tx, ty+iGap);      ctx.lineTo(tx, ty+iArm+iGap); ctx.stroke()
            }

            // ── Crosshair (always) ────────────────────────────────
            var cx = W / 2, cy = H / 2
            var arm = 13, gap = 5
            ctx.strokeStyle = "rgba(143,164,184,0.28)"
            ctx.lineWidth = 1.0
            ctx.beginPath(); ctx.moveTo(cx-arm-gap, cy); ctx.lineTo(cx-gap, cy); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(cx+gap, cy);     ctx.lineTo(cx+arm+gap, cy); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(cx, cy-arm-gap); ctx.lineTo(cx, cy-gap); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(cx, cy+gap);     ctx.lineTo(cx, cy+arm+gap); ctx.stroke()
            ctx.fillStyle = "rgba(143,164,184,0.38)"
            ctx.beginPath(); ctx.arc(cx, cy, 1.5, 0, Math.PI*2); ctx.fill()
        }
    }

    // No-signal overlay
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        visible: !videoRoot.isRunning

        Column {
            anchors.centerIn: parent
            spacing: 10
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "НЕТ СИГНАЛА"
                color: Qt.rgba(0.561, 0.643, 0.722, 0.18)
                font.pixelSize: 22
                font.family: "Menlo"
                font.letterSpacing: 8
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Нажмите СТАРТ для запуска"
                color: Qt.rgba(0.561, 0.643, 0.722, 0.1)
                font.pixelSize: 11
                font.family: "Menlo"
                font.letterSpacing: 2
            }
        }
    }
}
