"""
app/ui/theme.py — Canonical source of truth for the application stylesheet.

All UI theme constants live here. Import APP_STYLESHEET in main_gui.py:
    from app.ui.theme import APP_STYLESHEET
"""

APP_STYLESHEET = """
QMainWindow {
    background: #23272B;
    color: #E6EBEF;
}
QWidget {
    color: #E6EBEF;
    font-size: 13px;
    font-family: "Segoe UI", "Noto Sans", "Inter", sans-serif;
}
QWidget#CentralRoot {
    background: #23272B;
}
QMenuBar {
    background: #2B3136;
    color: #AAB4BE;
    border-bottom: 1px solid #3E474F;
}
QMenuBar::item:selected {
    background: #31383E;
}

QFrame#HeaderBar {
    background: #2B3136;
    border: 1px solid #3E474F;
    border-radius: 10px;
}
QLabel#WindowTitle {
    font-size: 17px;
    font-weight: 600;
    color: #E6EBEF;
}
QLabel#HeaderMeta {
    color: #AAB4BE;
    font-size: 13px;
}
QLabel#HeaderStatus {
    border: 1px solid #3E474F;
    border-radius: 8px;
    padding: 5px 10px;
    background: #31383E;
    color: #E6EBEF;
    font-weight: 600;
}
QLabel#HeaderStatus[state="idle"] { background: #31383E; }
QLabel#HeaderStatus[state="running"] { background: #3F5A4C; }
QLabel#HeaderStatus[state="lock"] { background: #5B7183; }
QLabel#HeaderStatus[state="lost"] { background: #9A7B3F; }
QLabel#HeaderStatus[state="stopping"] { background: #5D4F3A; }
QLabel#HeaderStatus[state="evaluating"] { background: #5B7183; }
QLabel#HeaderStatus[state="error"] { background: #7A4141; }

QLabel#RecordIndicator {
    border: 1px solid #3E474F;
    border-radius: 8px;
    padding: 5px 10px;
    background: #31383E;
    color: #AAB4BE;
}
QLabel#RecordIndicator[recording="true"] {
    background: #A24A4A;
    color: #E6EBEF;
    border-color: #A24A4A;
}

QFrame#LeftControlRail {
    background: #2B3136;
    border: 1px solid #3E474F;
    border-radius: 10px;
}
QLabel#RailSectionTitle {
    color: #AAB4BE;
    font-size: 12px;
    font-weight: 600;
}
QLabel#BottomConsoleText {
    color: #AAB4BE;
    font-family: "Consolas", "JetBrains Mono", monospace;
}
QFrame#BottomConsole {
    background: #2B3136;
    border: 1px solid #3E474F;
    border-radius: 8px;
}

QGroupBox {
    border: 1px solid #3E474F;
    border-radius: 10px;
    margin-top: 10px;
    padding-top: 12px;
    background: #2B3136;
    color: #E6EBEF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #AAB4BE;
    font-weight: 600;
    font-size: 12px;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
    background: #31383E;
    color: #E6EBEF;
    border: 1px solid #3E474F;
    border-radius: 8px;
    padding: 6px 8px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {
    border-color: #5B7183;
}

QPushButton {
    background: #31383E;
    color: #E6EBEF;
    border: 1px solid #3E474F;
    border-radius: 8px;
    padding: 7px 11px;
    font-weight: 600;
}
QPushButton:hover { background: #3A4248; }
QPushButton:disabled {
    background: #2A2F34;
    color: #7C8792;
    border-color: #384047;
}
QPushButton[variant="primary"] {
    background: #35654C;
    border-color: #35654C;
}
QPushButton[variant="primary"]:hover {
    background: #3D7358;
}
QPushButton[variant="destructive"] {
    background: #7A4141;
    border-color: #7A4141;
}
QPushButton[variant="destructive"]:hover {
    background: #8B4A4A;
}
QPushButton[variant="ghost"] {
    background: transparent;
    border-color: #3E474F;
    color: #AAB4BE;
}
QPushButton[variant="ghost"]:hover {
    background: #31383E;
    color: #E6EBEF;
}

QCheckBox {
    spacing: 7px;
    color: #E6EBEF;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #3E474F;
    border-radius: 4px;
    background: #31383E;
}
QCheckBox::indicator:checked {
    background: #5B7183;
    border-color: #5B7183;
}

QFrame#VideoStage {
    background: #2B3136;
    border: 1px solid #3E474F;
    border-radius: 10px;
    padding: 8px;
}

QLabel#VideoSurface {
    background: #1F2428;
    color: #AAB4BE;
    border: 1px solid #3E474F;
    border-radius: 10px;
    font-size: 14px;
}

QFrame#InspectorCard {
    background: #31383E;
    border: 1px solid #3E474F;
    border-radius: 8px;
}
QLabel#InspectorTitle {
    color: #AAB4BE;
    font-size: 12px;
    font-weight: 600;
}
QLabel#InspectorValue {
    color: #E6EBEF;
    font-size: 13px;
}

QFrame#TargetInfoCard {
    background: rgba(35, 39, 43, 210);
    border: 1px solid rgba(62, 71, 79, 180);
    border-radius: 8px;
}
QLabel#TargetCardRow {
    color: #E6EBEF;
    font-size: 12px;
}
QLabel#TargetCardState {
    color: #E6EBEF;
    font-size: 12px;
    font-weight: 700;
}
QLabel#TargetCardState[state="lock"] { color: #7FBFAA; }
QLabel#TargetCardState[state="lost"] { color: #CFA85A; }
QLabel#TargetCardState[state="idle"] { color: #AAB4BE; }

QPushButton[active="true"] {
    background: #3F5A4C;
    border-color: #4A7A62;
    color: #E6EBEF;
}
QPushButton[active="true"]:hover {
    background: #4A6B5A;
}
"""
