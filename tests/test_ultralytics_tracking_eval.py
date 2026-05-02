from pathlib import Path

from python_scripts.run_ultralytics_tracking_eval import _comparison_row, _resolve_tracker_arg, _select_native_track


class _Scalar:
    def __init__(self, value):
        self._value = value

    def item(self):
        return self._value


class _Vector:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return self._values


class _Box:
    def __init__(self, *, track_id, cls_id, conf, bbox):
        self.id = _Scalar(track_id) if track_id is not None else None
        self.cls = _Scalar(cls_id)
        self.conf = _Scalar(conf)
        self.xyxy = [_Vector(bbox)]


def test_select_native_track_prefers_preferred_class_then_confidence():
    selected = _select_native_track(
        [
            _Box(track_id=7, cls_id=1, conf=0.99, bbox=[1, 2, 3, 4]),
            _Box(track_id=3, cls_id=0, conf=0.40, bbox=[5, 6, 7, 8]),
            _Box(track_id=9, cls_id=0, conf=0.30, bbox=[9, 10, 11, 12]),
        ],
        prefer_class_id=0,
    )

    assert selected == {"track_id": 3, "bbox": (5, 6, 7, 8), "cls_id": 0, "conf": 0.40}


def test_select_native_track_ignores_untracked_boxes():
    selected = _select_native_track(
        [
            _Box(track_id=None, cls_id=0, conf=0.99, bbox=[1, 2, 3, 4]),
            _Box(track_id=4, cls_id=1, conf=0.50, bbox=[5, 6, 7, 8]),
        ],
        prefer_class_id=0,
    )

    assert selected["track_id"] == 4


def test_comparison_row_adds_project_deltas():
    project = {
        "total_frames": 100,
        "lock_frames": 40,
        "active_presence_rate": 0.50,
        "active_id_changes_per_min": 2.0,
        "false_lock_rate": 0.10,
        "avg_fps": 20.0,
    }
    native = {
        "total_frames": 100,
        "tracker": "bytetrack",
        "active_presence_rate": 0.70,
        "active_id_changes_per_min": 3.5,
        "false_lock_rate": 0.15,
        "avg_fps": 25.0,
    }

    row = _comparison_row("clip.mp4", "night", project, native)

    assert row["project_lock_rate"] == 0.4
    assert row["presence_delta"] == 0.2
    assert row["idchg_pm_delta"] == 1.5
    assert row["false_lock_delta"] == 0.05
    assert row["fps_delta"] == 5.0


def test_resolve_tracker_arg_uses_named_tracker_yaml_when_no_custom_config():
    assert _resolve_tracker_arg("botsort", Path("")) == "botsort.yaml"


def test_resolve_tracker_arg_prefers_custom_config_path():
    assert _resolve_tracker_arg("botsort", Path("configs/trackers/botsort_reid.yaml")) == "configs/trackers/botsort_reid.yaml"
