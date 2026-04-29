"""app/source_controller.py — Source type helpers extracted from MainWindow."""
from typing import Any


def split_source(source: Any) -> tuple[str, int, str]:
    if isinstance(source, int):
        return 'camera', int(source), ''
    text = str(source).strip()
    if text.isdigit():
        return 'camera', int(text), ''
    lowered = text.lower()
    if lowered.startswith(('rtsp://', 'http://', 'https://', 'udp://', 'tcp://')):
        return 'stream', 0, text
    return 'video', 0, text


def source_from_controls(window) -> Any:
    source_type = window.source_type_combo.currentData()
    if source_type == 'camera':
        return int(window.camera_index_spin.value())
    return window.source_path_edit.text().strip()


def on_source_type_changed(window) -> None:
    if window._updating_controls:
        return
    source_type = window.source_type_combo.currentData()
    is_camera = source_type == 'camera'
    controls_enabled = window._job_state == 'idle'
    window.camera_index_spin.setEnabled(is_camera and controls_enabled)
    window.camera_index_spin.setVisible(is_camera)
    show_path = source_type in {'video', 'stream'}
    window.source_path_label.setVisible(show_path)
    window.source_path_edit.setVisible(show_path)
    window.source_browse_btn.setVisible(show_path)
    window.source_path_edit.setEnabled(show_path and controls_enabled)
    window.source_browse_btn.setEnabled(show_path and controls_enabled)
    if is_camera:
        window.source_path_edit.setPlaceholderText('Для камеры путь не нужен')
        window.source_browse_btn.setText('Выбрать...')
    elif source_type == 'video':
        window.source_path_label.setText('Видео файл')
        window.source_path_edit.setPlaceholderText('/путь/к/видео.mp4')
        window.source_browse_btn.setText('Выбрать...')
    else:
        window.source_path_label.setText('URL потока')
        window.source_path_edit.setPlaceholderText('rtsp://...')
        window.source_browse_btn.setText('Подключить...')
    window._refresh_header_state()
    window._refresh_workspace_overviews()
