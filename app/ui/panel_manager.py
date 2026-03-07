from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .state_machine import UIState


@dataclass
class PanelState:
    key: str
    title: str
    pinned: bool = False
    opened: bool = True
    collapsed: bool = False


class PanelCard(QFrame):
    def __init__(self, title: str, content: QWidget, *, on_change: Optional[Callable[[], None]] = None):
        super().__init__()
        self.setObjectName('PanelCard')
        self.setFrameShape(QFrame.NoFrame)
        self._on_change = on_change

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(12, 12, 12, 12)
        self._root.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName('PanelCardTitle')
        header.addWidget(self.title_label, 1)

        self.pin_btn = QToolButton()
        self.pin_btn.setObjectName('PanelCardTool')
        self.pin_btn.setText('📌')
        self.pin_btn.setCheckable(True)
        self.pin_btn.setToolTip('Закрепить панель')
        self.pin_btn.toggled.connect(self._emit_change)
        header.addWidget(self.pin_btn)

        self.collapse_btn = QToolButton()
        self.collapse_btn.setObjectName('PanelCardTool')
        self.collapse_btn.setText('▾')
        self.collapse_btn.setCheckable(True)
        self.collapse_btn.setToolTip('Свернуть/развернуть')
        self.collapse_btn.toggled.connect(self._toggle_collapsed)
        header.addWidget(self.collapse_btn)

        self._root.addLayout(header)

        self.content = content
        self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._root.addWidget(self.content)

    def _toggle_collapsed(self, collapsed: bool) -> None:
        self.content.setVisible(not collapsed)
        self.collapse_btn.setText('▸' if collapsed else '▾')
        self._emit_change()

    def _emit_change(self) -> None:
        if self._on_change is not None:
            self._on_change()

    @property
    def pinned(self) -> bool:
        return self.pin_btn.isChecked()

    @property
    def collapsed(self) -> bool:
        return self.collapse_btn.isChecked()


class PanelManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('PanelManager')

        self._cards: dict[str, PanelCard] = {}
        self._states: dict[str, PanelState] = {}
        self._context_checkers: dict[str, Callable[[UIState], bool]] = {}
        self._toggle_buttons: dict[str, QPushButton] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        title = QLabel('Панели')
        title.setObjectName('SectionHeader')
        root.addWidget(title)

        self.toolbar_widget = QWidget()
        self.toolbar_widget.setObjectName('PanelToolbar')
        self.toolbar = QGridLayout(self.toolbar_widget)
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        self.toolbar.setHorizontalSpacing(8)
        self.toolbar.setVerticalSpacing(8)
        root.addWidget(self.toolbar_widget)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(self.scroll, 1)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(8)
        self.body_layout.addStretch(1)
        self.scroll.setWidget(self.body)

    def register_panel(
        self,
        key: str,
        title: str,
        content: QWidget,
        *,
        context_checker: Optional[Callable[[UIState], bool]] = None,
        opened: bool = True,
        pinned: bool = False,
    ) -> None:
        if key in self._cards:
            return

        card = PanelCard(title, content, on_change=self._sync_states)
        card.setVisible(opened)
        card.pin_btn.setChecked(pinned)

        self._cards[key] = card
        self._states[key] = PanelState(key=key, title=title, opened=opened, pinned=pinned)
        self._context_checkers[key] = context_checker or (lambda _state: True)

        toggle = QPushButton(title)
        toggle.setObjectName('PanelToggle')
        toggle.setCheckable(True)
        toggle.setChecked(opened)
        toggle.setMinimumHeight(34)
        toggle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        toggle.toggled.connect(lambda checked, panel_key=key: self.set_open(panel_key, checked))
        self._toggle_buttons[key] = toggle

        idx = len(self._toggle_buttons) - 1
        row, col = divmod(idx, 2)
        self.toolbar.addWidget(toggle, row, col)

        self.body_layout.insertWidget(max(0, self.body_layout.count() - 1), card)

    def set_open(self, key: str, opened: bool) -> None:
        card = self._cards.get(key)
        if card is None:
            return
        card.setVisible(opened)
        btn = self._toggle_buttons.get(key)
        if btn is not None and btn.isChecked() != opened:
            btn.blockSignals(True)
            btn.setChecked(opened)
            btn.blockSignals(False)
        self._sync_states()

    def set_pinned(self, key: str, pinned: bool) -> None:
        card = self._cards.get(key)
        if card is None:
            return
        card.pin_btn.setChecked(pinned)
        self._sync_states()

    def set_collapsed(self, key: str, collapsed: bool) -> None:
        card = self._cards.get(key)
        if card is None:
            return
        card.collapse_btn.setChecked(collapsed)
        self._sync_states()

    def set_context_state(self, state: UIState) -> None:
        for key, card in self._cards.items():
            checker = self._context_checkers.get(key, lambda _state: True)
            allowed = checker(state)
            if card.pinned:
                card.setVisible(True)
            else:
                card.setVisible(allowed and self._states.get(key, PanelState(key, key)).opened)
        self._sync_states()

    def open_panel(self, key: str) -> None:
        self.set_open(key, True)

    def panel_states(self) -> dict[str, PanelState]:
        self._sync_states()
        return dict(self._states)

    def restore_states(self, states: dict[str, dict]) -> None:
        for key, data in states.items():
            if key not in self._cards:
                continue
            self.set_open(key, bool(data.get('opened', True)))
            self.set_pinned(key, bool(data.get('pinned', False)))
            self.set_collapsed(key, bool(data.get('collapsed', False)))
        self._sync_states()

    def panel_titles(self) -> list[tuple[str, str]]:
        return [(key, state.title) for key, state in self._states.items()]

    def _sync_states(self) -> None:
        for key, card in self._cards.items():
            state = self._states[key]
            state.opened = card.isVisible()
            state.pinned = card.pinned
            state.collapsed = card.collapsed
