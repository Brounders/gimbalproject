from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


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

        self.overlay_layer = QWidget(self)
        self.overlay_layer.setObjectName('VideoOverlayLayer')
        self.overlay_layer.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.overlay_layout = QVBoxLayout(self.overlay_layer)
        self.overlay_layout.setContentsMargins(16, 16, 16, 16)
        self.overlay_layout.setSpacing(0)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)
        top_row.addStretch(1)
        self.overlay_anchor = QFrame()
        self.overlay_anchor.setObjectName('VideoOverlayAnchor')
        self.overlay_anchor_layout = QVBoxLayout(self.overlay_anchor)
        self.overlay_anchor_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_anchor_layout.setSpacing(0)
        top_row.addWidget(self.overlay_anchor, 0, Qt.AlignTop | Qt.AlignRight)
        self.overlay_layout.addLayout(top_row)
        self.overlay_layout.addStretch(1)

    def set_overlay_widget(self, widget: QWidget) -> None:
        while self.overlay_anchor_layout.count():
            item = self.overlay_anchor_layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.setParent(None)
        widget.setParent(self.overlay_anchor)
        self.overlay_anchor_layout.addWidget(widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay_layer.setGeometry(self.surface.geometry())
