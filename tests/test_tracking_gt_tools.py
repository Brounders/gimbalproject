from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np

import python_scripts.run_tracking_gt_diagnostics as diag
import python_scripts.validate_tracking_gt as validator


def _make_video(path: Path, *, frames: int = 6) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (80, 60))
    assert writer.isOpened()
    for idx in range(frames):
        frame = np.zeros((60, 80, 3), dtype=np.uint8)
        frame[20:32, 10 + idx : 22 + idx] = (255, 255, 255)
        writer.write(frame)
    writer.release()


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["source", "frame_index", "visible", "x1", "y1", "x2", "y2", "note"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_validate_valid_csv_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    video = tmp_path / "clip.mp4"
    _make_video(video)
    gt = tmp_path / "gt.csv"
    _write_csv(gt, [
        {"source": str(video), "frame_index": 0, "visible": 1, "x1": 10, "y1": 20, "x2": 22, "y2": 32, "note": ""},
        {"source": str(video), "frame_index": 1, "visible": 0, "x1": "", "y1": "", "x2": "", "y2": "", "note": "hidden"},
    ])

    summary = validator.validate_paths([gt])

    assert summary.errors == []
    assert summary.rows == 2
    assert summary.visible_rows == 1
    assert summary.invisible_rows == 1


def test_validate_duplicate_frame_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    video = tmp_path / "clip.mp4"
    _make_video(video)
    gt = tmp_path / "gt.csv"
    row = {"source": str(video), "frame_index": 0, "visible": 1, "x1": 10, "y1": 20, "x2": 22, "y2": 32, "note": ""}
    _write_csv(gt, [row, row])

    summary = validator.validate_paths([gt])

    assert summary.duplicate_count == 1
    assert summary.errors


def test_validate_visible_without_bbox_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    video = tmp_path / "clip.mp4"
    _make_video(video)
    gt = tmp_path / "gt.csv"
    _write_csv(gt, [{"source": str(video), "frame_index": 0, "visible": 1, "x1": "", "y1": "", "x2": "", "y2": "", "note": ""}])

    summary = validator.validate_paths([gt])

    assert summary.invalid_count == 1
    assert "without bbox" in summary.errors[0]


def test_validate_outside_frame_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    video = tmp_path / "clip.mp4"
    _make_video(video)
    gt = tmp_path / "gt.csv"
    _write_csv(gt, [{"source": str(video), "frame_index": 0, "visible": 1, "x1": 10, "y1": 20, "x2": 999, "y2": 32, "note": ""}])

    summary = validator.validate_paths([gt])

    assert summary.invalid_count == 1
    assert "outside frame" in summary.errors[0]


def test_build_report_flags_low_recall_and_latency():
    report = diag.build_report(
        [{
            "clip": "clip",
            "false_lock_rate_sampled": 0.1,
            "recall_iou_01": 0.4,
            "visible_gt_frames": 10,
            "latency_p99_ms": 130.0,
            "bbox_scale_step_p95": 0.1,
        }],
        {"rows": 10},
    )

    assert any("low recall" in risk for risk in report["risks"])
    assert any("high latency" in risk for risk in report["risks"])


def test_run_diagnostics_keeps_one_live_preset_for_all_sources(tmp_path, monkeypatch):
    ir_video = tmp_path / "clips" / "ir" / "IR_DRONE_025.mp4"
    eo_video = tmp_path / "clips" / "eo" / "f1_3_EO_dji_mavic_2.mp4"
    night_video = tmp_path / "clips" / "night" / "night_drone.mp4"
    for video in (ir_video, eo_video, night_video):
        _make_video(video, frames=1)

    gt_dir = tmp_path / "gt"
    _write_csv(gt_dir / "IR_DRONE_025_gt.csv", [
        {"source": str(ir_video), "frame_index": 0, "visible": 1, "x1": 10, "y1": 20, "x2": 22, "y2": 32, "note": ""},
    ])
    _write_csv(gt_dir / "f1_3_EO_dji_mavic_2_gt.csv", [
        {"source": str(eo_video), "frame_index": 0, "visible": 1, "x1": 10, "y1": 20, "x2": 22, "y2": 32, "note": ""},
    ])
    _write_csv(gt_dir / "night_drone_gt.csv", [
        {"source": str(night_video), "frame_index": 0, "visible": 1, "x1": 10, "y1": 20, "x2": 22, "y2": 32, "note": ""},
    ])

    used_presets = []

    def _fake_resolve_cfg(preset, **_kwargs):
        used_presets.append(preset)
        return object(), False

    def _fake_run_clip(_cfg, source, _annotations, *, small_target, **_kwargs):
        return {"source": source, "clip": Path(source).stem, "sampled_frames": 1}

    monkeypatch.setattr(diag, "_resolve_cfg", _fake_resolve_cfg)
    monkeypatch.setattr(diag, "_run_clip", _fake_run_clip)

    rows = diag.run_diagnostics(
        [gt_dir],
        preset="tracking_live_auto",
        scene_aware=True,
    )

    assert [row["preset"] for row in rows] == ["tracking_live_auto", "tracking_live_auto", "tracking_live_auto"]
    assert [row["scene"] for row in rows] == ["IR", "EO", "NIGHT"]
    assert used_presets == ["tracking_live_auto"]


def test_scene_aware_diagnostics_do_not_select_preset_from_source_name():
    assert not hasattr(diag, "_preset_for_scene")


def test_write_outputs_creates_report_files(tmp_path):
    report = diag.build_report(
        [{
            "source": "clip.mp4",
            "clip": "clip",
            "sampled_frames": 2,
            "visible_gt_frames": 2,
            "invisible_gt_frames": 0,
            "active_bbox_frames": 2,
            "matched_iou01_frames": 2,
            "false_lock_frames": 0,
            "missed_visible_frames": 0,
            "recall_iou_01": 1.0,
            "recall_iou_03": 1.0,
            "missed_visible_rate": 0.0,
            "false_lock_rate_sampled": 0.0,
            "avg_iou_visible": 0.8,
            "bbox_center_step_p95": 0.0,
            "bbox_scale_step_p95": 0.0,
            "avg_fps": 25.0,
            "latency_p95_ms": 20.0,
            "latency_p99_ms": 25.0,
            "active_id_changes_per_min": 0.0,
            "continuity_score": 1.0,
            "active_presence_rate": 1.0,
        }],
        {"rows": 2},
    )

    diag.write_outputs(report, tmp_path)

    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "summary.csv").exists()
    assert "Tracking GT Diagnostics" in (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "active_bbox_frames" in (tmp_path / "summary.csv").read_text(encoding="utf-8")


def test_run_clip_counts_tracker_match_miss_and_off_target(monkeypatch):
    annotations = [
        diag.GtAnnotation(source="clip.mp4", frame_index=0, visible=True, bbox=(10, 10, 20, 20), note=""),
        diag.GtAnnotation(source="clip.mp4", frame_index=1, visible=True, bbox=(10, 10, 20, 20), note=""),
        diag.GtAnnotation(source="clip.mp4", frame_index=2, visible=True, bbox=(10, 10, 20, 20), note=""),
        diag.GtAnnotation(source="clip.mp4", frame_index=3, visible=False, bbox=None, note="hidden"),
    ]

    class _Session:
        def __init__(self, *_args, **_kwargs):
            self.idx = -1

        def open(self):
            return None

        def read(self):
            self.idx += 1
            if self.idx >= 4:
                return False, None, {}
            return True, np.zeros((40, 40, 3), dtype=np.uint8), {"frame_index": self.idx, "source_fps": 30.0}

        def close(self):
            return None

    class _Result:
        def __init__(self, idx: int):
            self.fps = 30.0
            self.budget_frame_ms = 10.0
            self.timings_ms = {}
            self.active_source = "test"
            self.scan_strategy = "none"
            self.mode = "TRACK"
            self.active_id_changes = 0
            self.active_id_changes_per_min = 0.0
            self.continuity_score = 1.0
            self.active_presence_rate = 0.75
            self.active_bbox = {
                0: (10, 10, 20, 20),
                1: None,
                2: (25, 25, 35, 35),
                3: (5, 5, 12, 12),
            }[idx]

    class _Pipeline:
        def __init__(self, *_args, **_kwargs):
            return None

        def process_frame(self, _frame, *, frame_index, **_kwargs):
            return _Result(frame_index)

    monkeypatch.setattr(diag, "VideoSession", _Session)
    monkeypatch.setattr(diag, "TrackerPipeline", _Pipeline)
    monkeypatch.setattr(diag, "parse_video_source", lambda source: source)

    row = diag._run_clip(object(), "clip.mp4", annotations, small_target=False)

    assert row["sampled_frames"] == 4
    assert row["active_bbox_frames"] == 3
    assert row["matched_iou01_frames"] == 1
    assert row["false_lock_frames"] == 2
    assert row["missed_visible_frames"] == 1
    assert row["recall_iou_01"] == 1 / 3


def test_frame_outcome_names_match_miss_and_off_target():
    visible = diag.GtAnnotation(source="clip.mp4", frame_index=0, visible=True, bbox=(10, 10, 20, 20), note="")
    hidden = diag.GtAnnotation(source="clip.mp4", frame_index=1, visible=False, bbox=None, note="")

    assert diag._frame_outcome(visible, (10, 10, 20, 20))[0] == "matched"
    assert diag._frame_outcome(visible, None)[0] == "missed"
    assert diag._frame_outcome(visible, (25, 25, 35, 35))[0] == "off_target"
    assert diag._frame_outcome(hidden, (10, 10, 20, 20))[0] == "false_active"
    assert diag._frame_outcome(hidden, None)[0] == "clear_negative"


def test_run_clip_writes_visual_error_samples(monkeypatch, tmp_path):
    annotations = [
        diag.GtAnnotation(source="clip.mp4", frame_index=0, visible=True, bbox=(10, 10, 20, 20), note=""),
        diag.GtAnnotation(source="clip.mp4", frame_index=1, visible=True, bbox=(10, 10, 20, 20), note=""),
        diag.GtAnnotation(source="clip.mp4", frame_index=2, visible=True, bbox=(10, 10, 20, 20), note=""),
    ]

    class _Session:
        def __init__(self, *_args, **_kwargs):
            self.idx = -1

        def open(self):
            return None

        def read(self):
            self.idx += 1
            if self.idx >= 3:
                return False, None, {}
            frame = np.zeros((40, 40, 3), dtype=np.uint8)
            frame[10:20, 10:20] = (80, 80, 80)
            return True, frame, {"frame_index": self.idx, "source_fps": 30.0}

        def close(self):
            return None

    class _Result:
        def __init__(self, idx: int):
            self.fps = 30.0
            self.budget_frame_ms = 10.0
            self.timings_ms = {}
            self.active_source = "test"
            self.scan_strategy = "none"
            self.mode = "TRACK"
            self.active_id_changes = 0
            self.active_id_changes_per_min = 0.0
            self.continuity_score = 1.0
            self.active_presence_rate = 1.0
            self.active_bbox = {
                0: (10, 10, 20, 20),
                1: None,
                2: (25, 25, 35, 35),
            }[idx]

    class _Pipeline:
        def __init__(self, *_args, **_kwargs):
            return None

        def process_frame(self, _frame, *, frame_index, **_kwargs):
            return _Result(frame_index)

    monkeypatch.setattr(diag, "VideoSession", _Session)
    monkeypatch.setattr(diag, "TrackerPipeline", _Pipeline)
    monkeypatch.setattr(diag, "parse_video_source", lambda source: source)

    row = diag._run_clip(
        object(),
        "clip.mp4",
        annotations,
        small_target=False,
        error_samples_dir=tmp_path,
        max_error_samples_per_outcome=2,
    )

    outcomes = {sample["outcome"] for sample in row["error_samples"]}
    assert {"matched", "missed", "off_target"} <= outcomes
    for sample in row["error_samples"]:
        assert (tmp_path / sample["file"]).exists()


# ---------------------------------------------------------------------------
# TASK-103a Diagnostic Pack v1
# ---------------------------------------------------------------------------


def test_run_clip_emits_diagnostic_pack_fields(monkeypatch):
    annotations = [
        diag.GtAnnotation(source="clip.mp4", frame_index=0, visible=True, bbox=(10, 10, 30, 30), note=""),
        diag.GtAnnotation(source="clip.mp4", frame_index=1, visible=True, bbox=(10, 10, 30, 30), note=""),
        diag.GtAnnotation(source="clip.mp4", frame_index=2, visible=True, bbox=(10, 10, 30, 30), note=""),
    ]

    class _Session:
        def __init__(self, *_args, **_kwargs):
            self.idx = -1

        def open(self):
            return None

        def read(self):
            self.idx += 1
            if self.idx >= 3:
                return False, None, {}
            return True, np.zeros((40, 40, 3), dtype=np.uint8), {"frame_index": self.idx}

        def close(self):
            return None

    class _Result:
        def __init__(self, idx: int):
            self.fps = 30.0
            self.budget_frame_ms = 10.0
            self.timings_ms = {"global": 1.0 + idx, "lock": 0.5, "manager": 0.2, "total": 5.0}
            self.active_source = "yolo"
            self.scan_strategy = "GLOBAL"
            self.mode = "TRACK"
            self.active_id_changes = 0
            self.active_id_changes_per_min = 0.0
            self.continuity_score = 1.0
            self.active_presence_rate = 1.0
            self.active_bbox = [(10, 10, 20, 20), (10, 10, 30, 30), (10, 10, 40, 40)][idx]
            self.bbox_area = (self.active_bbox[2] - self.active_bbox[0]) * (self.active_bbox[3] - self.active_bbox[1])
            self.scene_label_runtime = ["day", "ir", "ir"][idx]
            self.scene_confidence_runtime = [1.0, 0.5, 1.0][idx]
            self.proposal_count_by_source = {"yolo": 1, "night": idx, "operator": 0}

    class _Pipeline:
        def __init__(self, *_args, **_kwargs):
            return None

        def process_frame(self, _frame, *, frame_index, **_kwargs):
            return _Result(frame_index)

    monkeypatch.setattr(diag, "VideoSession", _Session)
    monkeypatch.setattr(diag, "TrackerPipeline", _Pipeline)
    monkeypatch.setattr(diag, "parse_video_source", lambda source: source)

    row = diag._run_clip(object(), "clip.mp4", annotations, small_target=False)

    assert "bbox_area_cv" in row and row["bbox_area_cv"] > 0
    assert row["scene_runtime_counts"] == {"day": 1, "ir": 2}
    assert 0.0 < row["scene_confidence_avg"] < 1.0
    assert row["proposal_mean_by_source"]["yolo"] == 1.0
    assert row["proposal_seen_rate_by_source"]["yolo"] == 1.0
    assert row["proposal_seen_rate_by_source"].get("operator", 0.0) == 0.0
    assert row["stage_ms_p99"]["global"] > 0
    assert "manager" in row["stage_ms_p99"]
    assert "total" in row["stage_ms_p99"]


def test_build_report_includes_scene_confusion():
    rows = [
        {
            "clip": "ir_clip",
            "scene": "IR",
            "scene_runtime_counts": {"ir": 90, "day": 10},
            "false_lock_rate_sampled": 0.1,
            "recall_iou_01": 0.8,
            "visible_gt_frames": 100,
            "latency_p99_ms": 20.0,
            "bbox_scale_step_p95": 0.1,
        },
        {
            "clip": "eo_clip",
            "scene": "EO",
            "scene_runtime_counts": {"day": 100},
            "false_lock_rate_sampled": 0.1,
            "recall_iou_01": 0.8,
            "visible_gt_frames": 100,
            "latency_p99_ms": 20.0,
            "bbox_scale_step_p95": 0.1,
        },
    ]
    report = diag.build_report(rows, {"rows": 200})
    assert "scene_confusion" in report
    assert report["scene_confusion"]["IR"] == {"ir": 90, "day": 10}
    assert report["scene_confusion"]["EO"] == {"day": 100}


def test_write_outputs_csv_includes_stage_p99_columns(tmp_path):
    rows = [{
        "source": "clip.mp4",
        "clip": "clip",
        "sampled_frames": 1,
        "visible_gt_frames": 1,
        "invisible_gt_frames": 0,
        "active_bbox_frames": 1,
        "matched_iou01_frames": 1,
        "false_lock_frames": 0,
        "missed_visible_frames": 0,
        "recall_iou_01": 1.0,
        "recall_iou_03": 1.0,
        "missed_visible_rate": 0.0,
        "false_lock_rate_sampled": 0.0,
        "avg_iou_visible": 0.8,
        "bbox_center_step_p95": 0.0,
        "bbox_scale_step_p95": 0.0,
        "avg_fps": 25.0,
        "latency_p95_ms": 20.0,
        "latency_p99_ms": 25.0,
        "active_id_changes_per_min": 0.0,
        "continuity_score": 1.0,
        "active_presence_rate": 1.0,
        "bbox_area_cv": 0.15,
        "scene_confidence_avg": 0.92,
        "stage_ms_p99": {"global": 12.0, "lock": 3.0, "manager": 0.4, "total": 18.0},
    }]
    report = diag.build_report(rows, {"rows": 1})
    diag.write_outputs(report, tmp_path)
    text = (tmp_path / "summary.csv").read_text(encoding="utf-8")
    for col in (
        "bbox_area_cv", "scene_confidence_avg",
        "stage_yolo_p99_ms", "stage_lock_p99_ms", "stage_manager_p99_ms", "stage_total_p99_ms",
    ):
        assert col in text
    assert "12.0" in text
    assert "18.0" in text


def test_frame_result_metrics_carries_diagnostic_pack_fields():
    """Adapter must propagate Diagnostic Pack v1 fields from FrameOutput to FrameResult.metrics."""
    from uav_tracker.display.frame_result import FrameOutput
    from uav_tracker.domain.adapters import frame_result_from_output

    output = FrameOutput(
        frame=None, fps=30.0, active_id=1, active_source="yolo",
        active_bbox=(0, 0, 10, 10), target_count=1, visible_target_count=1,
        mode="TRACK", frame_index=0, scan_strategy="GLOBAL",
        gt_visible=False, gt_iou=0.0, lock_score=0.5, display_confidence=0.9,
        continuity_score=1.0, active_presence_rate=1.0, active_id_changes=0,
        median_reacquire_frames=0.0, lock_events=[], lock_switch_count=0,
        lock_switches_per_min=0.0, lock_event_counts={},
        budget_level=0, budget_load=0.5, budget_frame_ms=10.0,
        roi_budget_candidates=0, night_skip=0,
        timings_ms={"global": 5.0, "manager": 0.3, "total": 8.0},
        scene_label_runtime="ir",
        scene_confidence_runtime=0.75,
        proposal_count_by_source={"yolo": 2, "night": 1},
        bbox_area=100,
    )

    fr = frame_result_from_output(output, source="clip.mp4", frame_width=80, frame_height=60)

    assert fr.metrics["scene_label_runtime"] == "ir"
    assert fr.metrics["scene_confidence_runtime"] == 0.75
    assert fr.metrics["proposal_count_by_source"] == {"yolo": 2, "night": 1}
    assert fr.metrics["bbox_area"] == 100
    assert fr.metrics["timings_ms"]["manager"] == 0.3
    assert fr.metrics["timings_ms"]["total"] == 8.0
