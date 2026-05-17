from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "app" / "qml" / "components" / "TargetLabOverlay.qml"


def test_target_lab_dashboard_cards_are_vertical_and_dynamic_height():
    text = QML.read_text(encoding="utf-8")

    assert 'title: "МАТЕРИАЛ"' in text
    assert 'title: "ПРОВЕРКА ТРЕКЕРА"' in text
    assert "implicitHeight: contentCol.implicitHeight + 32" in text
    assert "Layout.preferredHeight: 210" not in text


def test_target_lab_check_wording_does_not_blame_gt_annotations():
    text = QML.read_text(encoding="utf-8")

    assert '"мимо " + falseLock + "%"' in text
    assert '"ложные " + falseLock + "%"' not in text
