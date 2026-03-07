from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QPlainTextEdit, QVBoxLayout


class CommandConsole(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName('CommandConsolePanel')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName('AppTitle')
        layout.addWidget(self.title_label)

        self.context_label = QLabel('Готово к запуску')
        self.context_label.setObjectName('Subtle')
        self.context_label.setWordWrap(True)
        layout.addWidget(self.context_label)

        self.status_label = QLabel('$ waiting for source')
        self.status_label.setObjectName('CommandStatus')
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName('CommandConsole')
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(52)
        self.log_view.document().setMaximumBlockCount(24)
        layout.addWidget(self.log_view)
