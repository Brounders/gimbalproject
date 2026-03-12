"""
app/ui/cards.py — Factory functions for reusable display cards.

Extracted from app/main_gui.py (TASK-20260312-056).
All functions are pure widget factories: they create and return Qt widgets with no side effects.
"""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout


def build_inspector_card(title: str) -> tuple[QFrame, QLabel]:
    """Create an InspectorCard frame with a title and a value label.

    Returns (card, value_label).
    """
    card = QFrame()
    card.setObjectName('InspectorCard')
    layout = QVBoxLayout(card)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(4)
    header = QLabel(title)
    header.setObjectName('InspectorTitle')
    layout.addWidget(header)
    value = QLabel('-')
    value.setObjectName('InspectorValue')
    value.setWordWrap(True)
    layout.addWidget(value)
    return card, value


def build_target_info_card() -> tuple[QFrame, QLabel, QLabel, QLabel, QLabel, QLabel]:
    """Create the TargetInfoCard overlay frame.

    Returns (card, id_label, conf_label, fps_label, time_label, state_label).
    """
    card = QFrame()
    card.setObjectName('TargetInfoCard')
    card.setMinimumWidth(170)
    grid = QGridLayout(card)
    grid.setContentsMargins(10, 8, 10, 8)
    grid.setSpacing(3)

    def _row(label_text: str) -> tuple[QLabel, QLabel]:
        lbl = QLabel(label_text)
        lbl.setObjectName('TargetCardRow')
        val = QLabel('—')
        val.setObjectName('TargetCardRow')
        return lbl, val

    lbl_id, tc_id = _row('Цель')
    lbl_conf, tc_conf = _row('Уверенность')
    lbl_fps, tc_fps = _row('FPS')
    lbl_time, tc_time = _row('На цели')

    tc_state = QLabel('IDLE')
    tc_state.setObjectName('TargetCardState')
    tc_state.setProperty('state', 'idle')

    for row_i, (lbl, val) in enumerate([
        (lbl_id, tc_id), (lbl_conf, tc_conf), (lbl_fps, tc_fps), (lbl_time, tc_time)
    ]):
        grid.addWidget(lbl, row_i, 0)
        grid.addWidget(val, row_i, 1)
    grid.addWidget(tc_state, 4, 0, 1, 2)
    return card, tc_id, tc_conf, tc_fps, tc_time, tc_state
