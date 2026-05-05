import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication, QPushButton

from app.main_gui import MainWindow


def _window():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    return app, window


def test_operator_shell_uses_real_action_buttons():
    _app, window = _window()
    try:
        for name in (
            'start_btn',
            'stop_btn',
            'next_target_btn',
            'operator_confirm_btn',
            'operator_release_btn',
            '_rail_source_btn',
            '_rail_record_btn',
            'bottom_drawer_toggle_btn',
        ):
            assert isinstance(getattr(window, name), QPushButton)
    finally:
        window.close()


def test_operator_shell_drawers_toggle_without_losing_controls():
    _app, window = _window()
    try:
        assert window.left_rail_container.width() == 72
        assert not window.left_drawer.isVisible()

        window._toggle_left_drawer()
        assert window.left_rail_container.width() == 318
        assert window.left_drawer.isVisible()
        assert window.source_type_combo.isVisible()
        assert window.record_check.isVisible()

        assert not window.bottom_drawer.body.isVisible()
        window._toggle_bottom_drawer()
        _app.processEvents()
        assert window.bottom_drawer.body.isVisible()
        assert hasattr(window, 'panel_monitoring_summary')
    finally:
        window.close()


def test_record_rail_button_toggles_existing_record_checkbox():
    _app, window = _window()
    try:
        initial = window.record_check.isChecked()
        window._toggle_record_enabled()
        assert window.record_check.isChecked() is (not initial)
        window._toggle_record_enabled()
        assert window.record_check.isChecked() is initial
    finally:
        window.close()
