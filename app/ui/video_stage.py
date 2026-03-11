from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class VideoStage(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName('VideoStage')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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
        layout.addWidget(self.surface)

        self._overlays_top_right: list[QWidget] = []

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
