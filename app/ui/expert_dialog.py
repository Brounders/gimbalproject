"""app/ui/expert_dialog.py — Expert settings dialog builder (T8d)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from uav_tracker.modes import RUNTIME_MODES
from uav_tracker.profile_io import available_presets


def build_expert_dialog(window) -> None:
    window.expert_dialog = QDialog(window)
    window.expert_dialog.setWindowTitle('Экспертные настройки')
    window.expert_dialog.resize(860, 620)
    window.expert_dialog.finished.connect(window._on_expert_dialog_closed)

    root = QVBoxLayout(window.expert_dialog)
    root.setContentsMargins(10, 10, 10, 10)
    root.setSpacing(8)

    scroller = QScrollArea()
    scroller.setWidgetResizable(True)
    root.addWidget(scroller, 1)

    content = QWidget()
    scroller.setWidget(content)
    layout = QGridLayout(content)
    layout.setHorizontalSpacing(8)
    layout.setVerticalSpacing(8)

    window.scenario_combo = QComboBox()
    window._fill_scenarios()
    window.preset_combo = QComboBox()
    window.preset_combo.addItems(available_presets() + ['custom'])
    window.apply_preset_btn = QPushButton('Применить preset')
    window.profile_load_btn = QPushButton('Загрузить профиль')
    window.profile_save_btn = QPushButton('Сохранить профиль')

    window.model_edit = QLineEdit('runs/detect/runs/drone_bird_probe_fast/weights/best.pt')
    window.model_browse_btn = QPushButton('Модель...')

    window.mode_combo = QComboBox()
    window.mode_combo.addItems(list(RUNTIME_MODES))
    window.device_combo = QComboBox()
    window.device_combo.addItems(['mps', 'cpu', 'hailo'])

    window.imgsz_spin = QSpinBox()
    window.imgsz_spin.setRange(160, 2048)
    window.imgsz_spin.setSingleStep(32)
    window.imgsz_spin.setValue(640)
    window.conf_spin = QDoubleSpinBox()
    window.conf_spin.setRange(0.01, 0.99)
    window.conf_spin.setSingleStep(0.01)
    window.conf_spin.setDecimals(2)
    window.conf_spin.setValue(0.30)
    window.rescan_spin = QSpinBox()
    window.rescan_spin.setRange(1, 60)
    window.rescan_spin.setValue(6)

    window.small_target_check = QCheckBox('Малые цели')
    window.adaptive_scan_check = QCheckBox('Adaptive scan')
    window.adaptive_scan_check.setChecked(True)
    window.lock_tracker_check = QCheckBox('Lock tracker')
    window.lock_tracker_check.setChecked(True)
    window.night_check = QCheckBox('Night detector')
    window.night_check.setChecked(True)
    window.roi_check = QCheckBox('ROI assist')
    window.roi_check.setChecked(True)
    window.show_gt_check = QCheckBox('Показывать GT')
    window.show_gt_check.setChecked(True)
    window.timing_check = QCheckBox('Показывать timing')
    window.timing_check.setChecked(True)
    window.show_trails_check = QCheckBox('Показывать траектории')
    window.show_trails_check.setChecked(True)

    row = 0
    layout.addWidget(QLabel('Сценарий'), row, 0)
    layout.addWidget(window.scenario_combo, row, 1, 1, 3)
    row += 1

    layout.addWidget(QLabel('Профиль'), row, 0)
    layout.addWidget(window.preset_combo, row, 1)
    layout.addWidget(window.apply_preset_btn, row, 2)
    layout.addWidget(window.profile_load_btn, row, 3)
    layout.addWidget(window.profile_save_btn, row, 4)
    row += 1

    layout.addWidget(QLabel('Модель'), row, 0)
    layout.addWidget(window.model_edit, row, 1, 1, 3)
    layout.addWidget(window.model_browse_btn, row, 4)
    row += 1

    layout.addWidget(QLabel('Mode'), row, 0)
    layout.addWidget(window.mode_combo, row, 1)
    layout.addWidget(QLabel('Device'), row, 2)
    layout.addWidget(window.device_combo, row, 3)
    row += 1

    layout.addWidget(QLabel('imgsz'), row, 0)
    layout.addWidget(window.imgsz_spin, row, 1)
    layout.addWidget(QLabel('conf'), row, 2)
    layout.addWidget(window.conf_spin, row, 3)
    layout.addWidget(QLabel('rescan'), row, 4)
    layout.addWidget(window.rescan_spin, row, 5)
    row += 1

    layout.addWidget(window.small_target_check, row, 0)
    layout.addWidget(window.adaptive_scan_check, row, 1)
    layout.addWidget(window.lock_tracker_check, row, 2)
    layout.addWidget(window.night_check, row, 3)
    layout.addWidget(window.roi_check, row, 4)
    row += 1

    layout.addWidget(window.show_gt_check, row, 0)
    layout.addWidget(window.timing_check, row, 1)
    layout.addWidget(window.show_trails_check, row, 2)

    close_btn = QPushButton('Закрыть')
    close_btn.clicked.connect(window._hide_expert_dialog)
    root.addWidget(close_btn, 0, Qt.AlignRight)
