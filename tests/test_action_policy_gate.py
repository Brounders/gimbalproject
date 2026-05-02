from argparse import Namespace

from python_scripts.run_action_policy_gate import (
    compact_report,
    load_pack,
    pair_row,
    row_failures,
    scene_preset,
)


def _thresholds(**overrides):
    values = {
        "max_presence_drop": 0.01,
        "max_false_lock_increase": 0.01,
        "max_noise_presence_increase": 0.01,
        "max_noise_false_lock_increase": 0.01,
        "max_iou_drop": 0.02,
        "max_hit01_drop": 2,
        "max_fps_drop": 5.0,
        "max_drop_rate": 0.02,
    }
    values.update(overrides)
    return Namespace(**values)


def _report(**overrides):
    values = {
        "total_frames": 100,
        "gt_frames": 100,
        "active_presence_rate": 0.80,
        "false_lock_rate": 0.05,
        "active_id_changes_per_min": 1.5,
        "avg_gt_iou": 0.60,
        "hits_iou_01": 80,
        "hits_iou_05": 70,
        "avg_fps": 30.0,
        "behavior_drop_count": 0,
    }
    values.update(overrides)
    return values


def test_load_pack_ignores_comments_and_defaults_scene(tmp_path):
    pack = tmp_path / "pack.csv"
    pack.write_text(
        "\n".join([
            "# source,scene",
            "test_videos/day.mp4,day",
            "",
            "test_videos/unknown.mp4",
        ]),
        encoding="utf-8",
    )

    rows = load_pack(pack)

    assert rows == [
        {"source": "test_videos/day.mp4", "scene": "day"},
        {"source": "test_videos/unknown.mp4", "scene": "unknown"},
    ]


def test_scene_preset_uses_ir_mapping_and_override():
    assert scene_preset("ir") == "antiuav_thermal"
    assert scene_preset("noise") == "default"
    assert scene_preset("ir", "night") == "night"


def test_compact_report_extracts_behavior_drop_count():
    compact = compact_report(_report(behavior_drop_count=3, avg_gt_iou=0.61234))

    assert compact["behavior_drop_count"] == 3
    assert compact["avg_gt_iou"] == 0.6123


def test_pair_row_computes_deltas_and_drop_rate():
    off = _report(active_presence_rate=0.80, false_lock_rate=0.05, active_id_changes_per_min=3.0)
    on = _report(
        active_presence_rate=0.79,
        false_lock_rate=0.04,
        active_id_changes_per_min=0.0,
        behavior_drop_count=1,
    )

    row = pair_row("clip.mp4", "ir", "antiuav_thermal", off, on)

    assert row["delta_presence"] == -0.01
    assert row["delta_false_lock"] == -0.01
    assert row["delta_idchg_pm"] == -3.0
    assert row["on_behavior_drop_rate"] == 0.01


def test_row_failures_accepts_small_positive_ir_delta():
    row = pair_row(
        "ir.mp4",
        "ir",
        "antiuav_thermal",
        _report(false_lock_rate=0.10, hits_iou_01=80),
        _report(false_lock_rate=0.105, hits_iou_01=79, behavior_drop_count=1),
    )

    assert row_failures(row, _thresholds()) == []


def test_row_failures_rejects_default_off_drops():
    row = pair_row(
        "day.mp4",
        "day",
        "default",
        _report(behavior_drop_count=1),
        _report(),
    )

    assert "off_behavior_drop_count_nonzero" in row_failures(row, _thresholds())


def test_row_failures_rejects_non_noise_presence_regression():
    row = pair_row(
        "day.mp4",
        "day",
        "default",
        _report(active_presence_rate=0.90),
        _report(active_presence_rate=0.80),
    )

    assert "presence_drop>0.01" in row_failures(row, _thresholds())


def test_row_failures_rejects_noise_false_lock_increase():
    row = pair_row(
        "noise.mp4",
        "noise",
        "default",
        _report(gt_frames=0, false_lock_rate=0.10),
        _report(gt_frames=0, false_lock_rate=0.20),
    )

    assert "noise_false_lock_increase>0.01" in row_failures(row, _thresholds())
