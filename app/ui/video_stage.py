from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

from app.ui.video_mapping import map_widget_point_to_frame


class VideoStage(QFrame):
    operator_target_requested = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.setObjectName('VideoStage')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._frame_size: tuple[int, int] | None = None

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
        if watched is self.surface and event.type() == QEvent.MouseButtonPress:
            if event.button() != Qt.LeftButton or self._frame_size is None:
                return False
            pos = event.position()
            mapped = map_widget_point_to_frame(
                widget_size=(self.surface.width(), self.surface.height()),
                frame_size=self._frame_size,
                point=(int(pos.x()), int(pos.y())),
            )
            if mapped is None:
                return False
            self.operator_target_requested.emit(mapped[0], mapped[1])
            return True
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
