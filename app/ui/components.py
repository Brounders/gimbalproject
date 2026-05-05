from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.theme import refresh_widget_style


class IconButton(QPushButton):
    """Compact operator action button with a stable QSS object name."""

    def __init__(self, label: str, tooltip: str = '', parent: QWidget | None = None):
        super().__init__(label, parent)
        self.setObjectName('RailIconBtn')
        self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(48, 42)
        self.setMaximumSize(48, 42)

    def set_active(self, active: bool) -> None:
        self.setProperty('active', 'true' if active else 'false')
        refresh_widget_style(self)


class StatusBadge(QLabel):
    """Small state badge used by the operator shell."""

    def __init__(self, text: str = 'IDLE', state: str = 'idle', parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName('HeaderStatus')
        self.set_state(text, state)

    def set_state(self, text: str, state: str) -> None:
        self.setText(text)
        self.setProperty('state', state)
        refresh_widget_style(self)


class MetricTile(QFrame):
    """Small key/value telemetry tile."""

    def __init__(self, key: str, value: str = '—', parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName('MetricTile')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(3)
        self.key_label = QLabel(key)
        self.key_label.setObjectName('MetricKey')
        self.value_label = QLabel(value)
        self.value_label.setObjectName('MetricVal')
        layout.addWidget(self.key_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class BottomDrawer(QFrame):
    """Collapsible bottom diagnostics surface."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName('BottomDrawer')
        self._expanded = False

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.header = QFrame()
        self.header.setObjectName('BottomDrawerHeader')
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(12, 0, 12, 0)
        self.header_layout.setSpacing(6)
        self.root_layout.addWidget(self.header)

        self.body = QFrame()
        self.body.setObjectName('BottomDrawerBody')
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(10, 0, 10, 10)
        self.body_layout.setSpacing(8)
        self.root_layout.addWidget(self.body)
        self.body.setVisible(False)
        self.setMaximumHeight(50)

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = bool(expanded)
        self.body.setVisible(self._expanded)
        self.setMaximumHeight(310 if self._expanded else 50)
        self.setProperty('expanded', self._expanded)
        refresh_widget_style(self)

    def toggle(self) -> None:
        self.set_expanded(not self._expanded)
