"""app/app_settings.py — QSettings persistence helpers extracted from MainWindow (T8f)."""
import json


def save_app_settings(window) -> None:
    window.settings.setValue('window/geometry', window.saveGeometry())
    window.settings.setValue('ui/scenario', window.scenario_combo.currentData())
    window.settings.setValue('ui/workspace', window._current_workspace_key())
    window.settings.setValue('ui/source_type', window.source_type_combo.currentData())
    window.settings.setValue('ui/camera_index', window.camera_index_spin.value())
    window.settings.setValue('ui/source_path', window.source_path_edit.text())
    window.settings.setValue('ui/record_output', window.record_check.isChecked())
    window.settings.setValue('ui/output_path', window.output_edit.text())
    window.settings.setValue('ui/profile_json', json.dumps(window._collect_profile(), ensure_ascii=False))
    window.settings.sync()


def load_app_settings(window) -> None:
    geometry = window.settings.value('window/geometry')
    if geometry is not None:
        window.restoreGeometry(geometry)

    profile_json = window.settings.value('ui/profile_json', '')
    if profile_json:
        try:
            profile = json.loads(str(profile_json))
            window._set_controls_from_profile(profile)
        except Exception:
            pass

    window._updating_controls = True
    try:
        source_type = window.settings.value('ui/source_type', window.source_type_combo.currentData())
        idx = window.source_type_combo.findData(source_type)
        if idx >= 0:
            window.source_type_combo.setCurrentIndex(idx)

        window.camera_index_spin.setValue(int(window.settings.value('ui/camera_index', window.camera_index_spin.value())))
        window.source_path_edit.setText(str(window.settings.value('ui/source_path', window.source_path_edit.text())))
        window.record_check.setChecked(str(window.settings.value('ui/record_output', 'true')).lower() == 'true')
        window.output_edit.setText(str(window.settings.value('ui/output_path', window.output_edit.text())))

        scenario = window.settings.value('ui/scenario', None)
        if scenario is not None:
            sidx = window.scenario_combo.findData(scenario)
            if sidx >= 0:
                window.scenario_combo.setCurrentIndex(sidx)
    finally:
        window._updating_controls = False
        window._refresh_record_controls()
        window._on_source_type_changed()
        window._refresh_workspace_overviews()
        window._refresh_sidebar_meta()
        window._refresh_header_state()
        workspace_key = str(window.settings.value('ui/workspace', 'operator'))
        if workspace_key not in window.workspace_indexes:
            workspace_key = 'operator'
        window._on_workspace_selected(workspace_key)
        window.inspector_module.setVisible(False)
