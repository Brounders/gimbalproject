"""
app/ui/theme.py — Glass console theme (iOS-style dark panels over video feed).

Color system derived from the Gimbal Design reference (gimbal design/style.css).
oklch tokens converted to sRGB hex for Qt QSS compatibility.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget

# ── Color tokens (oklch → sRGB approximations) ───────────────────────────────
BG0     = '#1D1F26'   # oklch(26% 0.01 250) — deepest background
BG1     = '#23252E'   # oklch(30% 0.011 250)
BG2     = '#292C36'   # oklch(34% 0.012 250)

FG0     = '#F3F4F7'   # oklch(98% 0.004 250) — near white
FG1     = '#E1E3E9'   # oklch(90% 0.006 250) — main text
FG2     = '#B4B9C5'   # oklch(74% 0.008 250) — secondary
FG3     = '#898FA1'   # oklch(60% 0.010 250) — muted

ACC     = '#7BC0DE'   # oklch(80% 0.13 210)  — blue accent
ACC_DIM = 'rgba(123,192,222,0.18)'
ACC_MID = 'rgba(123,192,222,0.28)'
ACC_LINE= 'rgba(123,192,222,0.55)'

OK      = '#5CCB78'   # oklch(82% 0.14 145) — green
WARN    = '#CDB038'   # oklch(84% 0.14 78)  — amber
BAD     = '#E06555'   # oklch(72% 0.18 25)  — red

GLASS   = 'rgba(255,255,255,0.07)'
GLASS2  = 'rgba(255,255,255,0.11)'
GLASS_BD= 'rgba(255,255,255,0.10)'
GLASS_HL= 'rgba(255,255,255,0.18)'
DARK25  = 'rgba(0,0,0,0.25)'
DARK40  = 'rgba(0,0,0,0.40)'

MONO    = '"JetBrains Mono", "Cascadia Code", "Fira Code", "Menlo", monospace'
SANS    = '"Inter", "Segoe UI", "Noto Sans", system-ui, sans-serif'

APP_STYLESHEET = f"""
/* ── Base ──────────────────────────────────────────────────────────────────── */
QMainWindow {{
    background: {BG0};
}}
QWidget {{
    color: {FG1};
    font-size: 13px;
    font-family: {SANS};
    background: transparent;
}}
QWidget#CentralRoot {{
    background: {BG0};
}}
QMenuBar {{
    background: {BG1};
    color: {FG2};
    border-bottom: 1px solid {GLASS_BD};
}}
QMenuBar::item:selected {{
    background: {BG2};
    border-radius: 6px;
}}
QMenu {{
    background: {BG2};
    border: 1px solid {GLASS_BD};
    border-radius: 10px;
    padding: 4px;
    color: {FG1};
}}
QMenu::item {{
    padding: 6px 20px 6px 12px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background: {GLASS};
}}
QScrollBar:vertical {{
    width: 4px;
    background: transparent;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {GLASS_BD};
    border-radius: 2px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

/* ── Top pill ──────────────────────────────────────────────────────────────── */
QFrame#TopBar {{
    background: {GLASS2};
    border: 1px solid {GLASS_HL};
    border-radius: 999px;
    min-height: 46px;
    max-height: 46px;
}}
QLabel#BrandName {{
    font-size: 11px;
    font-weight: 700;
    color: {FG0};
}}
QLabel#BrandSub {{
    font-size: 11px;
    color: {FG3};
}}
QLabel#TopBarClock {{
    font-family: {MONO};
    font-size: 12px;
    color: {FG0};
}}
QLabel#TopBarSep {{
    background: {GLASS_BD};
    min-width: 1px;
    max-width: 1px;
    min-height: 14px;
    max-height: 14px;
}}
QFrame#ModeSelector {{
    background: {DARK25};
    border-radius: 999px;
}}
QPushButton#ModeBtn {{
    background: transparent;
    border: none;
    border-radius: 999px;
    color: {FG2};
    font-family: {MONO};
    font-size: 11px;
    padding: 5px 14px;
    min-height: 28px;
}}
QPushButton#ModeBtn:hover {{
    background: rgba(255,255,255,0.08);
    color: {FG0};
}}
QPushButton#ModeBtn[active="true"] {{
    background: rgba(255,255,255,0.14);
    color: {ACC};
    border: 1px solid {GLASS_HL};
}}
QLabel#HeaderStatus {{
    font-family: {MONO};
    font-size: 10px;
    color: {FG0};
    border-radius: 999px;
    padding: 4px 10px;
    background: rgba(0,0,0,0.3);
}}
QLabel#HeaderStatus[state="idle"]       {{ background: rgba(0,0,0,0.30); color: {FG3}; }}
QLabel#HeaderStatus[state="running"]    {{ background: rgba(92,203,120,0.20); color: {OK}; }}
QLabel#HeaderStatus[state="lock"]       {{ background: {ACC_DIM}; color: {ACC}; }}
QLabel#HeaderStatus[state="lost"]       {{ background: rgba(205,176,56,0.20); color: {WARN}; }}
QLabel#HeaderStatus[state="stopping"]   {{ background: rgba(0,0,0,0.30); color: {FG3}; }}
QLabel#HeaderStatus[state="evaluating"] {{ background: {ACC_DIM}; color: {ACC}; }}
QLabel#HeaderStatus[state="error"]      {{ background: rgba(224,101,85,0.20); color: {BAD}; }}
QLabel#RecordIndicator {{
    font-family: {MONO};
    font-size: 10px;
    border-radius: 999px;
    padding: 4px 10px;
    background: rgba(0,0,0,0.30);
    color: {FG3};
    border: 1px solid {GLASS_BD};
}}
QLabel#RecordIndicator[recording="true"] {{
    background: rgba(224,101,85,0.18);
    color: {BAD};
    border-color: rgba(224,101,85,0.40);
}}

/* ── Left rail ─────────────────────────────────────────────────────────────── */
QFrame#LeftControlRail {{
    background: transparent;
}}
QLabel#RailSectionTitle {{
    font-size: 10px;
    font-weight: 600;
    color: {FG3};
}}
QPushButton#QuickModeBtn {{
    background: {DARK25};
    border: 1px solid {GLASS_BD};
    border-radius: 10px;
    color: {FG2};
    font-family: {MONO};
    font-size: 11px;
    padding: 7px 4px;
    min-height: 32px;
}}
QPushButton#QuickModeBtn:hover {{
    background: rgba(255,255,255,0.08);
    color: {FG0};
}}
QPushButton#QuickModeBtn[active="true"] {{
    background: {ACC_DIM};
    color: {ACC};
    border-color: {ACC_LINE};
}}

/* ── Source / form inputs ──────────────────────────────────────────────────── */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {{
    background: {DARK25};
    border: 1px solid {GLASS_BD};
    border-radius: 10px;
    color: {FG1};
    padding: 6px 10px;
    selection-background-color: {ACC_DIM};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QPlainTextEdit:focus {{
    border-color: {ACC_LINE};
}}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox::down-arrow {{ width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{
    background: {BG2};
    border: 1px solid {GLASS_BD};
    border-radius: 10px;
    color: {FG1};
    selection-background-color: {ACC_DIM};
    outline: none;
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    width: 18px;
    border: none;
    background: transparent;
}}
QCheckBox {{
    color: {FG1};
    spacing: 8px;
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {GLASS_BD};
    border-radius: 5px;
    background: rgba(0,0,0,0.20);
}}
QCheckBox::indicator:checked {{
    background: {ACC_DIM};
    border-color: {ACC_LINE};
}}

/* ── Video stage ───────────────────────────────────────────────────────────── */
QFrame#VideoStage {{
    background: #0A0D12;
    border: 1px solid {GLASS_BD};
    border-radius: 24px;
}}
QLabel#VideoSurface {{
    background: #0A0D12;
    border-radius: 20px;
}}

/* ── Right panel cards ─────────────────────────────────────────────────────── */
QFrame#ActiveTargetCard {{
    background: {GLASS};
    border: 1px solid {GLASS_BD};
    border-radius: 18px;
}}
QLabel#LiveBadge {{
    background: {ACC_DIM};
    color: {ACC};
    border-radius: 999px;
    padding: 3px 10px;
    font-family: {MONO};
    font-size: 10px;
}}
QLabel#ActiveTargetId {{
    font-family: {MONO};
    font-size: 11px;
    color: {FG2};
}}
QLabel#ActiveTargetName {{
    font-size: 26px;
    font-weight: 500;
    color: {FG0};
}}
QLabel#ActiveTargetSub {{
    font-size: 12px;
    color: {FG2};
}}
QLabel#MetricKey {{
    font-size: 10px;
    font-weight: 600;
    color: {FG3};
}}
QLabel#MetricVal {{
    font-size: 18px;
    font-weight: 500;
    color: {FG0};
}}
QFrame#ConfBarTrack {{
    background: rgba(255,255,255,0.10);
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}}
QFrame#ConfBarFill {{
    background: {ACC};
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}}

/* Status chips */
QLabel#ChipOk     {{ background: rgba(92,203,120,0.18);  color: {OK};   border-radius: 999px; padding: 2px 8px; font-size: 10px; font-family: {MONO}; }}
QLabel#ChipWarn   {{ background: rgba(205,176,56,0.18);  color: {WARN}; border-radius: 999px; padding: 2px 8px; font-size: 10px; font-family: {MONO}; }}
QLabel#ChipAccent {{ background: {ACC_DIM};               color: {ACC};  border-radius: 999px; padding: 2px 8px; font-size: 10px; font-family: {MONO}; }}
QLabel#ChipBad    {{ background: rgba(224,101,85,0.18);  color: {BAD};  border-radius: 999px; padding: 2px 8px; font-size: 10px; font-family: {MONO}; }}

/* Runtime stats card */
QFrame#RuntimeCard {{
    background: {GLASS};
    border: 1px solid {GLASS_BD};
    border-radius: 16px;
}}
QLabel#RuntimeTitle {{
    font-size: 10px;
    font-weight: 600;
    color: {FG3};
}}
QLabel#RuntimeVal {{
    font-family: {MONO};
    font-size: 28px;
    font-weight: 400;
    color: {FG0};
}}
QLabel#RuntimeUnit {{
    font-size: 12px;
    color: {FG3};
}}

/* ── Inspector / diagnostics ───────────────────────────────────────────────── */
QGroupBox {{
    background: {GLASS};
    border: 1px solid {GLASS_BD};
    border-radius: 16px;
    padding: 16px 12px 10px;
    margin-top: 8px;
    font-size: 10px;
    font-weight: 600;
    color: {FG3};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 4px;
    padding: 0 4px;
    color: {FG2};
    background: transparent;
}}
QFrame#InspectorCard {{
    background: rgba(0,0,0,0.18);
    border: 1px solid {GLASS_BD};
    border-radius: 12px;
}}
QLabel#InspectorTitle {{
    font-size: 10px;
    font-weight: 600;
    color: {FG3};
}}
QLabel#InspectorValue {{
    font-family: {MONO};
    font-size: 11px;
    color: {FG1};
}}
QFrame#TargetInfoCard {{
    background: rgba(10,13,18,0.72);
    border: 1px solid {GLASS_BD};
    border-radius: 14px;
}}
QLabel#TargetCardRow {{
    font-family: {MONO};
    font-size: 11px;
    color: {FG1};
}}
QLabel#TargetCardState {{
    font-family: {MONO};
    font-size: 12px;
    font-weight: 600;
    color: {FG1};
}}
QLabel#TargetCardState[state="lock"] {{ color: {OK}; }}
QLabel#TargetCardState[state="lost"] {{ color: {WARN}; }}
QLabel#TargetCardState[state="idle"] {{ color: {FG3}; }}

/* ── Dock ──────────────────────────────────────────────────────────────────── */
QFrame#Dock {{
    background: {GLASS2};
    border: 1px solid {GLASS_HL};
    border-radius: 999px;
    min-height: 60px;
    max-height: 60px;
}}
QPushButton#DockBtn {{
    background: transparent;
    border: none;
    border-radius: 999px;
    color: {FG1};
    font-size: 13px;
    min-height: 44px;
    padding: 0 16px;
}}
QPushButton#DockBtn:hover {{
    background: rgba(255,255,255,0.08);
    color: {FG0};
}}
QPushButton#DockBtn:disabled {{
    color: {FG3};
}}
QPushButton#DockIconBtn {{
    background: transparent;
    border: none;
    border-radius: 999px;
    color: {FG1};
    font-size: 16px;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
}}
QPushButton#DockIconBtn:hover {{
    background: rgba(255,255,255,0.08);
}}
QPushButton#DockIconBtn:disabled {{
    color: {FG3};
}}
QPushButton#DockPrimary {{
    background: {ACC_DIM};
    border: 1px solid {ACC_LINE};
    border-radius: 999px;
    color: {ACC};
    font-size: 13px;
    font-weight: 600;
    min-height: 44px;
    padding: 0 20px;
}}
QPushButton#DockPrimary:hover {{
    background: {ACC_MID};
}}
QPushButton#DockPrimary:disabled {{
    background: rgba(123,192,222,0.07);
    border-color: rgba(123,192,222,0.15);
    color: rgba(123,192,222,0.35);
}}
QPushButton#DockDestructive {{
    background: transparent;
    border: none;
    border-radius: 999px;
    color: {BAD};
    font-size: 13px;
    min-height: 44px;
    padding: 0 16px;
}}
QPushButton#DockDestructive:hover {{
    background: rgba(224,101,85,0.12);
}}
QPushButton#DockDestructive:disabled {{
    color: rgba(224,101,85,0.30);
}}
QFrame#DockSep {{
    background: {GLASS_BD};
    min-width: 1px;
    max-width: 1px;
    min-height: 22px;
    max-height: 22px;
}}
QLabel#BottomConsoleText {{
    font-family: {MONO};
    font-size: 11px;
    color: {FG3};
    padding: 0 8px;
}}

/* ── Generic buttons (legacy / expert dialog) ──────────────────────────────── */
QPushButton {{
    background: {DARK25};
    border: 1px solid {GLASS_BD};
    border-radius: 10px;
    color: {FG1};
    padding: 6px 14px;
    font-size: 13px;
    min-height: 30px;
}}
QPushButton:hover {{
    background: rgba(255,255,255,0.06);
    border-color: {GLASS_HL};
}}
QPushButton:disabled {{
    color: {FG3};
    border-color: rgba(255,255,255,0.05);
}}
QPushButton[variant="primary"] {{
    background: {ACC_DIM};
    border: 1px solid {ACC_LINE};
    color: {ACC};
    font-weight: 600;
}}
QPushButton[variant="primary"]:hover {{
    background: {ACC_MID};
}}
QPushButton[variant="primary"]:disabled {{
    background: rgba(123,192,222,0.07);
    border-color: rgba(123,192,222,0.15);
    color: rgba(123,192,222,0.35);
}}
QPushButton[variant="destructive"] {{
    background: rgba(224,101,85,0.14);
    border-color: rgba(224,101,85,0.35);
    color: {BAD};
}}
QPushButton[variant="destructive"]:hover {{
    background: rgba(224,101,85,0.22);
}}
QPushButton[variant="ghost"] {{
    background: transparent;
    border: none;
    color: {FG2};
}}
QPushButton[variant="ghost"]:hover {{
    background: rgba(255,255,255,0.06);
    color: {FG0};
}}
QPushButton[active="true"] {{
    background: {ACC_DIM};
    border-color: {ACC_LINE};
    color: {ACC};
}}
QPushButton[active="true"]:hover {{
    background: {ACC_MID};
}}
"""

# Display labels for scenario keys
SCENARIO_LABELS: dict[str, str] = {
    'day':        'День',
    'night':      'Ночь',
    'ir':         'IR',
    'auto':       'Авто',
    'drone':      'Дрон',
    'bird':       'Птица',
    'custom':     'Пользов.',
    'evaluation': 'Оценка',
    'default':    'По умолч.',
}


def refresh_widget_style(widget: QWidget) -> None:
    """Force Qt to re-evaluate dynamic property-based QSS rules."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
