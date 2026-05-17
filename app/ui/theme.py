"""
app/ui/theme.py — Glass console theme (iOS-style dark panels over video feed).

Color system derived from the Gimbal Design reference (gimbal design/style.css).
oklch tokens converted to sRGB hex for Qt QSS compatibility.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget

# ── Color tokens — operator station palette ──────────────────────────────────
# Calibrated against Gimbal Operator HTML reference (steel-blue / glass HUD).
BG0     = '#1F3247'   # deep navy-steel — reference body gradient bottom
BG1     = '#243547'   # workspace base
BG2     = '#2A4361'   # panel surface — reference gradient top

FG0     = '#F2F7FB'   # near white — primary text (reference --t-1)
FG1     = '#E6ECF3'   # main text body (reference DTS --t-1)
FG2     = '#B7C7D6'   # secondary text (reference --t-2)
FG3     = '#8497A8'   # muted captions / keys (reference --t-3)

# Accent palette — reference tokens. Used for state only, not decoration.
ACC     = '#8FA4B8'   # cool steel cyan (reference --acc-cyan)
ACC_DIM = 'rgba(143,164,184,0.16)'
ACC_MID = 'rgba(143,164,184,0.26)'
ACC_LINE= 'rgba(143,164,184,0.50)'

OK      = '#5FD884'   # lock / accepted / tracking (reference --acc-green)
OK_DIM  = 'rgba(95,216,132,0.14)'
OK_LINE = 'rgba(95,216,132,0.45)'

WARN    = '#F2B84B'   # staged / warn / amber (reference --acc-warn)
WARN_DIM= 'rgba(242,184,75,0.14)'
WARN_LINE='rgba(242,184,75,0.45)'

BAD     = '#E05252'   # error / rec / rejected (reference --acc-err)
BAD_DIM = 'rgba(224,82,82,0.14)'
BAD_LINE= 'rgba(224,82,82,0.45)'

# Glass / surface tones over the steel-blue base.
GLASS   = 'rgba(255,255,255,0.06)'   # subtle panel fill
GLASS2  = 'rgba(255,255,255,0.10)'   # raised panel
GLASS3  = 'rgba(255,255,255,0.14)'   # strongest surface (active state)
GLASS_BD= 'rgba(255,255,255,0.12)'   # standard border
GLASS_HL= 'rgba(255,255,255,0.22)'   # strong border (focus, active)
DARK25  = 'rgba(0,0,0,0.22)'         # input fields
DARK40  = 'rgba(0,0,0,0.36)'

MONO    = '"JetBrains Mono", "Cascadia Code", "Fira Code", "Menlo", monospace'
SANS    = '"JetBrains Mono", "Inter", "Segoe UI", system-ui, monospace'

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
    background: qlineargradient(x1:0, y1:0, x2:0.4, y2:1,
        stop:0 #2A4361,
        stop:0.45 #243547,
        stop:1 #1F3247);
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

/* ── Top bar (floating glass pill — reference HUD style) ───────────────────── */
QFrame#TopBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255,255,255,0.14),
        stop:1 rgba(255,255,255,0.05));
    border: 1px solid {GLASS_HL};
    border-radius: 18px;
    min-height: 36px;
    max-height: 36px;
}}
QPushButton#TopBarMenuBtn {{
    background: {DARK25};
    border: 1px solid {GLASS_BD};
    border-radius: 10px;
    color: {FG1};
    min-width: 32px;
    max-width: 32px;
    min-height: 28px;
    max-height: 28px;
    padding: 0;
    font-size: 14px;
}}
QPushButton#TopBarMenuBtn:hover {{ background: {GLASS3}; }}
QFrame#TopBarBrandDot {{
    background: {OK_DIM};
    border: 1px solid {OK_LINE};
    border-radius: 8px;
    min-width: 16px;
    max-width: 16px;
    min-height: 16px;
    max-height: 16px;
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
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1px;
    color: {FG2};
    border-radius: 6px;
    padding: 3px 8px;
    background: rgba(159,177,195,0.10);
    border: 1px solid rgba(159,177,195,0.22);
}}
QLabel#HeaderStatus[state="idle"]       {{ background: rgba(159,177,195,0.10); color: {FG2}; border-color: rgba(159,177,195,0.22); }}
QLabel#HeaderStatus[state="running"]    {{ background: rgba(95,216,132,0.12); color: {OK}; border-color: rgba(95,216,132,0.40); }}
QLabel#HeaderStatus[state="lock"]       {{ background: rgba(95,216,132,0.12); color: {OK}; border-color: rgba(95,216,132,0.40); }}
QLabel#HeaderStatus[state="lost"]       {{ background: rgba(242,184,75,0.12); color: {WARN}; border-color: rgba(242,184,75,0.40); }}
QLabel#HeaderStatus[state="stopping"]   {{ background: rgba(159,177,195,0.10); color: {FG2}; border-color: rgba(159,177,195,0.22); }}
QLabel#HeaderStatus[state="evaluating"] {{ background: rgba(143,164,184,0.14); color: {ACC}; border-color: rgba(143,164,184,0.40); }}
QLabel#HeaderStatus[state="error"]      {{ background: rgba(224,82,82,0.14); color: {BAD}; border-color: rgba(224,82,82,0.40); }}
QLabel#RecordIndicator {{
    font-family: {MONO};
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1px;
    border-radius: 6px;
    padding: 3px 8px;
    background: rgba(0,0,0,0.20);
    color: {FG3};
    border: 1px solid {GLASS_BD};
}}
QLabel#RecordIndicator[recording="true"] {{
    background: rgba(224,82,82,0.14);
    color: {BAD};
    border-color: rgba(224,82,82,0.40);
}}

/* ── Left rail ─────────────────────────────────────────────────────────────── */
QFrame#LeftControlRail {{
    background: transparent;
}}
QFrame#GlassPanel {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255,255,255,0.10),
        stop:1 rgba(255,255,255,0.04));
    border: 1px solid {GLASS_BD};
    border-radius: 16px;
}}
QLabel#RailSectionTitle {{
    font-family: {MONO};
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1px;
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
    background: #0a121a;
    border: 1px solid {GLASS_BD};
    border-radius: 14px;
}}
QLabel#VideoSurface {{
    background: #0a121a;
    border-radius: 10px;
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
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255,255,255,0.12),
        stop:1 rgba(255,255,255,0.04));
    border: 1px solid {GLASS_HL};
    border-radius: 18px;
    min-height: 52px;
    max-height: 52px;
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

/* ── Reference-aligned operator widgets (2026-05-06 redesign) ──────────────── */

/* Compact icon+label stack button — used in the left control rail. */
QPushButton#RailIconBtn {{
    background: {GLASS};
    border: 1px solid {GLASS_BD};
    border-radius: 14px;
    color: {FG2};
    font-family: {MONO};
    font-size: 10px;
    padding: 8px 6px;
    min-width: 60px;
    max-width: 60px;
    min-height: 56px;
    max-height: 56px;
    text-align: center;
}}
QPushButton#RailIconBtn:hover {{
    background: {GLASS2};
    color: {FG0};
    border-color: {GLASS_HL};
}}
QPushButton#RailIconBtn:disabled {{
    color: {FG3};
    background: rgba(255,255,255,0.02);
}}
QPushButton#RailIconBtn[tone="rec"] {{
    background: {BAD_DIM};
    border-color: {BAD_LINE};
    color: {BAD};
}}
QPushButton#RailIconBtn[tone="rec"]:hover {{
    background: rgba(224,107,107,0.22);
}}
QPushButton#RailIconBtn[tone="lock"] {{
    background: {OK_DIM};
    border-color: {OK_LINE};
    color: {OK};
}}
QPushButton#RailIconBtn[tone="lock"]:hover {{
    background: rgba(95,217,126,0.24);
}}
QPushButton#RailIconBtn[active="true"] {{
    background: {ACC_DIM};
    border-color: {ACC_LINE};
    color: {ACC};
}}

/* Vertical zoom cluster card. */
QFrame#RailZoomCard {{
    background: {GLASS};
    border: 1px solid {GLASS_BD};
    border-radius: 14px;
    min-width: 60px;
    max-width: 60px;
}}
QLabel#RailZoomTitle {{
    font-family: {MONO};
    font-size: 9px;
    color: {FG3};
    qproperty-alignment: AlignCenter;
}}
QLabel#RailZoomVal {{
    font-family: {MONO};
    font-size: 12px;
    color: {FG0};
    qproperty-alignment: AlignCenter;
}}
QPushButton#RailZoomBtn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    color: {FG1};
    font-family: {MONO};
    font-size: 14px;
    min-width: 40px;
    max-width: 40px;
    min-height: 22px;
    max-height: 22px;
}}
QPushButton#RailZoomBtn:hover {{ background: {GLASS2}; color: {FG0}; }}

/* Reference target-card (right column): label/value rows + confidence bar. */
QFrame#RefTargetCard {{
    background: {GLASS};
    border: 1px solid {GLASS_BD};
    border-radius: 16px;
}}
QLabel#RefCardTitle {{
    font-family: {MONO};
    font-size: 11px;
    font-weight: 600;
    color: {FG2};
    letter-spacing: 1px;
}}
QLabel#RefCardClass {{
    font-family: {MONO};
    font-size: 10px;
    color: {FG3};
    letter-spacing: 1px;
}}
QLabel#RefRowKey {{
    font-family: {MONO};
    font-size: 10px;
    color: {FG3};
    letter-spacing: 1px;
}}
QLabel#RefRowVal {{
    font-family: {MONO};
    font-size: 12px;
    color: {FG0};
    qproperty-alignment: AlignRight;
}}
QLabel#RefRowValStrong {{
    font-family: {MONO};
    font-size: 14px;
    font-weight: 600;
    color: {FG0};
    qproperty-alignment: AlignRight;
}}
QLabel#RefConfPct {{
    font-family: {MONO};
    font-size: 28px;
    font-weight: 500;
    color: {OK};
    qproperty-alignment: AlignRight;
}}
QFrame#RefConfTrack {{
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}}
QFrame#RefConfFill {{
    background: {OK};
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}}

/* Telemetry grid cell. */
QFrame#TeleCell {{
    background: {DARK25};
    border: 1px solid {GLASS_BD};
    border-radius: 12px;
}}
QLabel#TeleKey {{
    font-family: {MONO};
    font-size: 9px;
    color: {FG3};
    letter-spacing: 1px;
}}
QLabel#TeleVal {{
    font-family: {MONO};
    font-size: 16px;
    color: {FG0};
}}
QLabel#TeleUnit {{
    font-family: {MONO};
    font-size: 10px;
    color: {FG3};
}}
QFrame#TeleBar {{
    background: rgba(255,255,255,0.06);
    border-radius: 2px;
    min-height: 3px;
    max-height: 3px;
}}
QFrame#TeleBarFill {{
    background: {ACC};
    border-radius: 2px;
    min-height: 3px;
    max-height: 3px;
}}
QFrame#TeleBarFill[tone="ok"]   {{ background: {OK}; }}
QFrame#TeleBarFill[tone="warn"] {{ background: {WARN}; }}
QFrame#TeleBarFill[tone="bad"]  {{ background: {BAD}; }}

/* Status pills for the topbar (REC, TRACKING). */
QLabel#StatusPill {{
    font-family: {MONO};
    font-size: 10px;
    border-radius: 999px;
    padding: 4px 12px;
    background: {DARK25};
    color: {FG3};
    border: 1px solid {GLASS_BD};
    letter-spacing: 1px;
}}
QLabel#StatusPill[state="rec_on"] {{
    background: {BAD_DIM};
    color: {BAD};
    border-color: {BAD_LINE};
}}
QLabel#StatusPill[state="tracking"] {{
    background: {OK_DIM};
    color: {OK};
    border-color: {OK_LINE};
}}
QLabel#StatusPill[state="lost"] {{
    background: {WARN_DIM};
    color: {WARN};
    border-color: {WARN_LINE};
}}
QLabel#StatusPill[state="evaluating"] {{
    background: {ACC_DIM};
    color: {ACC};
    border-color: {ACC_LINE};
}}
QLabel#StatusPill[state="error"] {{
    background: rgba(224,107,107,0.22);
    color: {BAD};
    border-color: {BAD_LINE};
}}

/* Bottom info bar — coords/console/FPS strip at the bottom of the operator UI. */
QFrame#BottomInfoBar {{
    background: rgba(255,255,255,0.025);
    border: 1px solid {GLASS_BD};
    border-radius: 14px;
    min-height: 36px;
    max-height: 36px;
}}
QLabel#BottomInfoText {{
    font-family: {MONO};
    font-size: 10px;
    color: {FG3};
    letter-spacing: 1px;
}}
QLabel#BottomFpsText {{
    font-family: {MONO};
    font-size: 11px;
    color: {FG1};
}}

/* ── DTS — Training Desk redesign primitives ──────────────────────────────── */
QDialog#TrainingDeskDialog {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(28,38,50,0.97),
        stop:1 rgba(22,30,40,0.99));
    background-color: #1A222C;
}}
QFrame#DtsHeader {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 0px;
    min-height: 46px;
    max-height: 46px;
}}
QLabel#DtsTitle {{
    font-family: {MONO};
    font-size: 13px;
    font-weight: 700;
    color: {FG0};
    letter-spacing: 1px;
}}
QLabel#DtsSubtitle {{
    font-size: 11px;
    color: {FG3};
}}
QLabel#DtsCounterPill {{
    font-family: {MONO};
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 1px;
    color: {FG2};
    border-radius: 0px;
    padding: 2px 0px;
    background: transparent;
    border: none;
}}
QLabel#DtsCounterPill[tone="new"]      {{ color: #8FA4B8; }}
QLabel#DtsCounterPill[tone="accepted"] {{ color: #52D273; }}
QLabel#DtsCounterPill[tone="rejected"] {{ color: #E26B6B; }}
QLabel#DtsCounterPill[tone="staged"]   {{ color: #E8B547; }}

QFrame#DtsSidebar, QFrame#DtsCenter, QFrame#DtsRecordPanel {{
    background: transparent;
    border: none;
    border-radius: 0px;
}}
QFrame#DtsSidebar {{
    border-right: 1px solid rgba(255,255,255,0.08);
}}
QFrame#DtsCenter {{
    border-right: 1px solid rgba(255,255,255,0.08);
}}
QFrame#DtsFooter {{
    background: rgba(255,255,255,0.03);
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    border-radius: 0px;
    min-height: 44px;
    max-height: 44px;
}}

QPushButton#DtsFilterBtn {{
    background: transparent;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 6px;
    color: #A9B5C2;
    font-family: {MONO};
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 1px;
    padding: 5px 8px;
    text-align: left;
}}
QPushButton#DtsFilterBtn:hover {{
    color: #E6ECF3;
}}
QPushButton#DtsFilterBtn[active="true"] {{
    background: rgba(143,164,184,0.16);
    border-color: rgba(143,164,184,0.45);
    color: #E6ECF3;
}}

QTableWidget#DtsEventsTable {{
    background: transparent;
    border: none;
    color: #E6ECF3;
    font-family: {MONO};
    font-size: 11px;
    gridline-color: transparent;
    selection-background-color: rgba(143,164,184,0.12);
    selection-color: #E6ECF3;
}}
QTableWidget#DtsEventsTable::item {{
    padding: 9px 10px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}}
QTableWidget#DtsEventsTable::item:selected {{
    background: rgba(143,164,184,0.12);
    color: #E6ECF3;
    border-left: 3px solid #8FA4B8;
}}
QHeaderView::section {{
    background: transparent;
    color: #6F7E8E;
    border: none;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding: 7px 10px;
    font-family: {MONO};
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
}}

QLabel#DtsPreviewSurface {{
    background: #0c1218;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    color: #6F7E8E;
}}
QLabel#DtsCropSurface {{
    background: #0c1218;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    color: #6F7E8E;
}}
QLabel#DtsPanelLabel {{
    font-family: {MONO};
    font-size: 10px;
    color: {FG3};
    letter-spacing: 1px;
}}
QLabel#DtsRecordHeading {{
    font-family: {MONO};
    font-size: 18px;
    font-weight: 600;
    color: {FG0};
}}
QLabel#DtsRecordClass {{
    font-family: {MONO};
    font-size: 10px;
    color: {FG3};
    border-radius: 999px;
    padding: 3px 10px;
    background: {DARK25};
    border: 1px solid {GLASS_BD};
}}
QLabel#DtsRecordKey {{
    font-family: {MONO};
    font-size: 9px;
    color: {FG3};
    letter-spacing: 1px;
}}
QLabel#DtsRecordVal {{
    font-family: {MONO};
    font-size: 11px;
    color: {FG0};
}}
QLabel#DtsQualityRow {{
    font-family: {MONO};
    font-size: 11px;
    color: {FG1};
}}
QLabel#DtsQualityState[state="ok"]   {{ color: {OK}; }}
QLabel#DtsQualityState[state="warn"] {{ color: {WARN}; }}
QLabel#DtsQualityState[state="fail"] {{ color: {BAD}; }}
QLabel#DtsQualityState[state="na"]   {{ color: {FG3}; }}
QLabel#DtsQualityValue {{
    font-family: {MONO};
    font-size: 11px;
    color: {FG2};
}}

QPushButton#DtsAccept {{
    background: {OK_DIM};
    border: 1px solid {OK_LINE};
    border-radius: 12px;
    color: {OK};
    font-weight: 600;
    min-height: 36px;
    padding: 0 16px;
}}
QPushButton#DtsAccept:hover {{ background: rgba(95,217,126,0.26); }}
QPushButton#DtsReject {{
    background: transparent;
    border: 1px solid {BAD_LINE};
    border-radius: 12px;
    color: {BAD};
    min-height: 36px;
    padding: 0 16px;
}}
QPushButton#DtsReject:hover {{ background: {BAD_DIM}; }}
QPushButton#DtsStage {{
    background: {WARN_DIM};
    border: 1px solid {WARN_LINE};
    border-radius: 12px;
    color: {WARN};
    font-weight: 600;
    min-height: 38px;
    padding: 0 16px;
}}
QPushButton#DtsStage:hover {{ background: rgba(217,184,95,0.26); }}
QPushButton#DtsExport {{
    background: transparent;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 7px;
    color: #A9B5C2;
    font-family: {MONO};
    font-size: 10px;
    font-weight: 500;
    min-height: 28px;
    padding: 0 12px;
}}
QPushButton#DtsExport:hover {{ background: rgba(255,255,255,0.06); color: #E6ECF3; }}
QPushButton#DtsExport[primary="true"] {{
    background: rgba(82,210,115,0.14);
    border-color: rgba(82,210,115,0.40);
    color: #52D273;
}}
QPushButton#DtsExport[primary="true"]:hover {{ background: rgba(82,210,115,0.22); }}
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
