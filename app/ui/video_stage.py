from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QRubberBand, QSizePolicy, QVBoxLayout

from app.ui.video_mapping import map_widget_bbox_to_frame, map_widget_point_to_frame


class VideoStage(QFrame):
    operator_target_requested = Signal(int, int)
    operator_bbox_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.setObjectName('VideoStage')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._frame_size: tuple[int, int] | None = None
        self._drag_origin: QPoint | None = None
        self._rubber_band: QRubberBand | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.surface = QLabel(
            'Операторская сцена пока не активна\n\n'
            '1) Выбери источник\n'
            '2) Примени сценарий\n'
            '3) Нажми Старт'
        )
        self.surface.setObjectName('VideoSurface')
        self.surface.setAlignment(Qt.AlignCenter)
        self.surface.setMinimumSize(860, 600)
        self.surface.setWordWrap(True)
        self.surface.installEventFilter(self)
        self.surface.setCursor(Qt.ArrowCursor)
        layout.addWidget(self.surface)

        self._overlays_top_right: list[QWidget] = []

    def set_frame_size(self, width: int, height: int) -> None:
        self._frame_size = (int(width), int(height)) if width > 0 and height > 0 else None
        self.surface.setCursor(Qt.CrossCursor if self._frame_size is not None else Qt.ArrowCursor)

    def clear_frame_size(self) -> None:
        self._frame_size = None
        self.surface.setCursor(Qt.ArrowCursor)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.surface and self._frame_size is not None:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() != Qt.LeftButton:
                    return False
                self._drag_origin = event.position().toPoint()
                if self._rubber_band is None:
                    self._rubber_band = QRubberBand(QRubberBand.Rectangle, self.surface)
                self._rubber_band.setGeometry(QRect(self._drag_origin, self._drag_origin))
                self._rubber_band.show()
                return True
            if event.type() == QEvent.MouseMove and self._drag_origin is not None:
                if self._rubber_band is not None:
                    self._rubber_band.setGeometry(QRect(self._drag_origin, event.position().toPoint()).normalized())
                return True
            if event.type() == QEvent.MouseButtonRelease and self._drag_origin is not None:
                if event.button() != Qt.LeftButton:
                    return False
                origin = self._drag_origin
                end = event.position().toPoint()
                self._drag_origin = None
                if self._rubber_band is not None:
                    self._rubber_band.hide()
                rect = QRect(origin, end).normalized()
                if rect.width() >= 8 and rect.height() >= 8:
                    mapped_bbox = map_widget_bbox_to_frame(
                        widget_size=(self.surface.width(), self.surface.height()),
                        frame_size=self._frame_size,
                        bbox=(rect.left(), rect.top(), rect.right(), rect.bottom()),
                    )
                    if mapped_bbox is not None:
                        self.operator_bbox_requested.emit(mapped_bbox)
                    return True
                pos = end
                mapped = map_widget_point_to_frame(
                    widget_size=(self.surface.width(), self.surface.height()),
                    frame_size=self._frame_size,
                    point=(int(pos.x()), int(pos.y())),
                )
                if mapped is None:
                    return False
                self.operator_target_requested.emit(mapped[0], mapped[1])
                return True
        if watched is self.surface and event.type() == QEvent.MouseButtonPress:
            if event.button() != Qt.LeftButton:
                return False
        return super().eventFilter(watched, event)

    def add_overlay_top_right(self, widget: 'QWidget') -> None:
        widget.setParent(self)
        self._overlays_top_right.append(widget)
        self._reposition_overlays()
        widget.show()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_overlays()

    def _reposition_overlays(self) -> None:
        margin = 8
        y = margin
        for w in self._overlays_top_right:
            w.adjustSize()
            x = self.width() - w.width() - margin
            w.move(x, y)
