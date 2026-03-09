from __future__ import annotations

from app.ui.state_machine import UIState


UI_STATE_VIEW: dict[UIState, dict[str, str]] = {
    UIState.IDLE: {'badge': 'IDLE', 'state': 'idle', 'label': 'Ожидание'},
    UIState.CHECKING: {'badge': 'CHECK', 'state': 'checking', 'label': 'Остановка'},
    UIState.RUNNING: {'badge': 'RUN', 'state': 'running', 'label': 'Сканирование'},
    UIState.LOCK: {'badge': 'LOCK', 'state': 'lock', 'label': 'Сопровождение'},
    UIState.LOST: {'badge': 'LOST', 'state': 'lost', 'label': 'Повторный захват'},
    UIState.EVALUATION: {'badge': 'EVAL', 'state': 'evaluating', 'label': 'Оценка'},
    UIState.ERROR: {'badge': 'ERROR', 'state': 'error', 'label': 'Ошибка'},
}


TOKENS_V2: dict[str, str] = {
    'bg': '#23272B',
    'bg_secondary': '#2B3136',
    'panel': '#2B3136',
    'panel_raised': '#31383E',
    'panel_soft': '#3E474F',
    'surface': '#1F2428',
    'border': '#3E474F',
    'border_soft': '#4A535C',
    'text_primary': '#E6EBEF',
    'text_secondary': '#AAB4BE',
    'text_muted': '#8E98A2',
    'accent': '#5F6B76',
    'accent_soft': '#48525C',
    'success': '#3F6A52',
    'danger': '#6E3A3A',
    'warn': '#7A6A46',
    'rec': '#8A4040',
    'radius_sm': '8',
    'radius_md': '10',
    'radius_lg': '12',
}


def _build_v2_stylesheet(tokens: dict[str, str]) -> str:
    return f"""
QMainWindow {{
    background: {tokens['bg']};
    color: {tokens['text_primary']};
}}
QWidget {{
    color: {tokens['text_primary']};
    font-size: 13px;
    font-family: "Segoe UI", "Noto Sans", "Inter", sans-serif;
}}
QWidget#CentralRoot {{
    background: {tokens['bg']};
}}

QMenuBar {{
    background: {tokens['panel']};
    color: {tokens['text_secondary']};
    border-bottom: 1px solid {tokens['border']};
}}
QMenuBar::item {{
    spacing: 4px;
    padding: 4px 8px;
}}
QMenuBar::item:selected {{
    background: {tokens['panel_soft']};
    border-radius: {tokens['radius_sm']}px;
}}

QFrame#HeaderBar {{
    background: {tokens['panel']};
    border: 1px solid {tokens['border_soft']};
    border-radius: {tokens['radius_md']}px;
}}
QLabel#WindowTitle {{
    font-size: 17px;
    font-weight: 600;
    color: {tokens['text_primary']};
}}
QLabel#HeaderMeta {{
    color: {tokens['text_secondary']};
    font-size: 13px;
    font-weight: 500;
}}
QLabel#HeaderStatus {{
    border: 1px solid {tokens['border']};
    border-radius: {tokens['radius_sm']}px;
    padding: 5px 10px;
    background: {tokens['panel_soft']};
    color: {tokens['text_primary']};
    font-weight: 600;
    min-width: 68px;
    qproperty-alignment: AlignCenter;
}}
QLabel#HeaderStatus[state="idle"] {{ background: {tokens['panel_soft']}; }}
QLabel#HeaderStatus[state="checking"] {{ background: {tokens['warn']}; }}
QLabel#HeaderStatus[state="running"] {{ background: {tokens['success']}; }}
QLabel#HeaderStatus[state="lock"] {{ background: {tokens['success']}; }}
QLabel#HeaderStatus[state="lost"] {{ background: {tokens['warn']}; }}
QLabel#HeaderStatus[state="evaluating"] {{ background: {tokens['accent_soft']}; }}
QLabel#HeaderStatus[state="error"] {{ background: {tokens['danger']}; }}

QLabel#RecordIndicator {{
    border: 1px solid {tokens['border']};
    border-radius: {tokens['radius_sm']}px;
    padding: 5px 10px;
    background: {tokens['panel_soft']};
    color: {tokens['text_secondary']};
    min-width: 74px;
    qproperty-alignment: AlignCenter;
}}
QLabel#RecordIndicator[recording="true"] {{
    background: {tokens['rec']};
    color: {tokens['text_primary']};
    border-color: {tokens['rec']};
}}

QFrame#LeftControlRail {{
    background: {tokens['panel']};
    border: 1px solid {tokens['border']};
    border-radius: {tokens['radius_md']}px;
}}
QLabel#RailSectionTitle {{
    color: {tokens['text_secondary']};
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.2px;
}}

QFrame#PrimaryControlCard,
QFrame#SecondaryControlCard,
QFrame#TertiaryControlCard {{
    border-radius: {tokens['radius_md']}px;
    border: 1px solid {tokens['border']};
    padding: 0;
}}
QFrame#PrimaryControlCard {{
    background: {tokens['panel_raised']};
    border-color: {tokens['border_soft']};
}}
QFrame#SecondaryControlCard {{
    background: {tokens['panel']};
}}
QFrame#TertiaryControlCard {{
    background: {tokens['bg_secondary']};
}}

QFrame#BottomConsole {{
    background: {tokens['panel']};
    border: 1px solid {tokens['border']};
    border-radius: {tokens['radius_sm']}px;
}}
QLabel#BottomConsoleText {{
    color: {tokens['text_primary']};
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 12px;
}}

QGroupBox {{
    border: 1px solid {tokens['border']};
    border-radius: {tokens['radius_md']}px;
    margin-top: 8px;
    padding-top: 10px;
    background: {tokens['bg_secondary']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 6px;
    color: {tokens['text_secondary']};
    font-size: 11px;
    font-weight: 600;
}}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {{
    background: {tokens['panel_raised']};
    color: {tokens['text_primary']};
    border: 1px solid {tokens['border']};
    border-radius: {tokens['radius_sm']}px;
    padding: 6px 8px;
    min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {{
    border-color: {tokens['accent']};
}}

QPushButton {{
    background: {tokens['panel_raised']};
    color: {tokens['text_primary']};
    border: 1px solid {tokens['border']};
    border-radius: {tokens['radius_sm']}px;
    padding: 6px 12px;
    min-height: 30px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {tokens['panel_soft']};
    border-color: {tokens['border_soft']};
}}
QPushButton:pressed {{
    background: {tokens['bg_secondary']};
}}
QPushButton:disabled {{
    background: {tokens['bg_secondary']};
    color: {tokens['text_muted']};
    border-color: {tokens['border']};
}}
QPushButton[variant="primary"] {{
    background: {tokens['success']};
    border-color: {tokens['success']};
}}
QPushButton[variant="primary"]:hover {{
    background: #48755C;
}}
QPushButton[variant="destructive"] {{
    background: {tokens['danger']};
    border-color: {tokens['danger']};
}}
QPushButton[variant="destructive"]:hover {{
    background: #7C4545;
}}
QPushButton[variant="ghost"] {{
    background: transparent;
    color: {tokens['text_secondary']};
    border-color: {tokens['border']};
}}
QPushButton[variant="ghost"]:hover {{
    color: {tokens['text_primary']};
    background: {tokens['panel_soft']};
}}

QCheckBox {{
    spacing: 7px;
    color: {tokens['text_primary']};
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {tokens['border']};
    border-radius: 4px;
    background: {tokens['panel_raised']};
}}
QCheckBox::indicator:checked {{
    background: {tokens['accent']};
    border-color: {tokens['accent']};
}}

QFrame#VideoStage {{
    background: {tokens['panel']};
    border: 1px solid {tokens['border']};
    border-radius: {tokens['radius_md']}px;
    padding: 8px;
}}

QLabel#VideoSurface {{
    background: {tokens['surface']};
    color: {tokens['text_secondary']};
    border: 1px solid {tokens['border']};
    border-radius: {tokens['radius_md']}px;
    font-size: 14px;
    padding: 10px;
}}

QWidget#VideoOverlayLayer {{
    background: transparent;
}}

QFrame#TargetInfoCard {{
    background: rgba(35, 39, 43, 225);
    border: 1px solid {tokens['border_soft']};
    border-radius: {tokens['radius_sm']}px;
    min-width: 190px;
}}
QLabel#TargetInfoState {{
    border: 1px solid {tokens['border']};
    border-radius: 6px;
    padding: 2px 6px;
    font-size: 13px;
    font-weight: 700;
    min-width: 58px;
    qproperty-alignment: AlignCenter;
}}
QLabel#TargetInfoState[state="lock"] {{
    background: {tokens['success']};
    border-color: {tokens['success']};
    color: {tokens['text_primary']};
}}
QLabel#TargetInfoState[state="idle"] {{
    background: {tokens['panel_soft']};
    border-color: {tokens['border']};
    color: {tokens['text_primary']};
}}
QLabel#TargetInfoTitle {{
    color: {tokens['text_secondary']};
    font-size: 12px;
    font-weight: 500;
}}
QLabel#TargetInfoValue {{
    color: {tokens['text_primary']};
    font-size: 13px;
    font-weight: 600;
}}

QGroupBox#CompactDiagnostics {{
    background: {tokens['panel']};
    border-color: {tokens['border_soft']};
}}
QFrame#InspectorCompactCard {{
    background: {tokens['panel_raised']};
    border: 1px solid {tokens['border_soft']};
    border-radius: {tokens['radius_sm']}px;
    min-height: 64px;
}}
QLabel#InspectorValueMain {{
    color: {tokens['text_primary']};
    font-size: 12px;
    font-weight: 600;
}}
QLabel#InspectorValueSub {{
    color: {tokens['text_secondary']};
    font-size: 11px;
}}

QFrame#InspectorCard {{
    background: {tokens['panel_raised']};
    border: 1px solid {tokens['border']};
    border-radius: {tokens['radius_sm']}px;
}}
QFrame#InspectorCard[level="primary"] {{
    background: {tokens['panel_soft']};
    border-color: {tokens['border_soft']};
}}
QFrame#InspectorCard[level="secondary"] {{
    background: {tokens['panel_raised']};
}}
QFrame#InspectorCard[level="tertiary"] {{
    background: {tokens['bg_secondary']};
}}
QLabel#InspectorTitle {{
    color: {tokens['text_primary']};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.3px;
}}
QLabel#InspectorValue {{
    color: {tokens['text_primary']};
    font-size: 12px;
}}
"""


LEGACY_STYLESHEET = """
QMainWindow { background: #23272B; color: #E6EBEF; }
QWidget { color: #E6EBEF; font-size: 13px; font-family: "Segoe UI", "Noto Sans", sans-serif; }
QFrame#HeaderBar, QFrame#LeftControlRail, QFrame#VideoStage, QFrame#BottomConsole {
    background: #2B3136;
    border: 1px solid #3E474F;
    border-radius: 10px;
}
QPushButton { background: #31383E; border: 1px solid #3E474F; border-radius: 8px; padding: 7px 11px; }
QPushButton[variant="primary"] { background: #35654C; border-color: #35654C; }
QPushButton[variant="destructive"] { background: #7A4141; border-color: #7A4141; }
QLabel#VideoSurface {
    background: #1F2428;
    border: 1px solid #3E474F;
    border-radius: 10px;
}
"""


def build_app_stylesheet(ui_v2_enabled: bool = True) -> str:
    if not ui_v2_enabled:
        return LEGACY_STYLESHEET
    return _build_v2_stylesheet(TOKENS_V2)
