from __future__ import annotations

from uav_tracker.detection_source import DetectionSource
from uav_tracker.evaluation import EvaluationReport, _telemetry_label


def _report(**overrides) -> EvaluationReport:
    values = {
        "source": "clip.mp4",
        "runtime_mode": "normal",
        "total_frames": 10,
        "gt_frames": 0,
        "active_frames": 2,
        "lock_frames": 0,
        "visible_target_frames": 2,
        "false_alarm_frames": 2,
        "false_lock_frames": 2,
        "false_lock_rate": 0.2,
        "hits_iou_01": 0,
        "hits_iou_03": 0,
        "hits_iou_05": 0,
        "avg_gt_iou": 0.0,
        "avg_fps": 30.0,
        "avg_lock_score": 0.0,
        "continuity_score": 0.0,
        "active_presence_rate": 0.2,
        "active_id_changes": 0,
        "active_id_changes_per_min": 0.0,
        "median_reacquire_frames": 0.0,
        "lock_switches": 0,
        "lock_switches_per_min": 0.0,
        "lock_event_counts": {},
        "mode_counts": {"SEARCH": 8, "TRACK": 2},
        "avg_budget_level": 0.0,
        "avg_budget_load": 0.0,
        "avg_budget_frame_ms": 0.0,
        "elapsed_video_sec": 1.0,
        "time_to_first_active": 4,
        "time_to_first_lock": None,
        "longest_lock_streak": 0,
        "scan_strategy_counts": {"default": 10},
        "avg_stage_ms": {"global": 1.0},
        "behavior_drop_count": 0,
        "tracking_action_counts": {"keep_lock": 2, "global_rescan": 8},
        "decision_path_counts": {"telemetry_only": 10},
        "target_source_counts": {"yolo": 2, "-": 8},
        "target_modality_counts": {"rgb": 10},
        "false_lock_action_counts": {"keep_lock": 2},
        "false_lock_source_counts": {"yolo": 2},
        "avg_target_reliability": 0.42,
        "avg_target_p_present": 0.50,
        "operator_workflow_counts": {"SEARCH": 8, "TRACKING": 2},
        "operator_workflow_event_counts": {"OPERATOR_HINT": 1, "LOCK_CONFIRMED": 1},
        "operator_hint_count": 1,
        "operator_lock_confirmed_count": 1,
        "operator_target_lost_count": 0,
        "avg_operator_click_to_lock_frames": 3.0,
        "avg_operator_verify_age_frames": 1.5,
    }
    values.update(overrides)
    return EvaluationReport(**values)


def test_evaluation_report_to_dict_includes_policy_telemetry():
    data = _report().to_dict()

    assert data["tracking_action_counts"] == {"keep_lock": 2, "global_rescan": 8}
    assert data["decision_path_counts"] == {"telemetry_only": 10}
    assert data["target_source_counts"] == {"yolo": 2, "-": 8}
    assert data["target_modality_counts"] == {"rgb": 10}
    assert data["false_lock_action_counts"] == {"keep_lock": 2}
    assert data["false_lock_source_counts"] == {"yolo": 2}
    assert data["avg_target_reliability"] == 0.42
    assert data["avg_target_p_present"] == 0.50
    assert data["operator_workflow_counts"] == {"SEARCH": 8, "TRACKING": 2}
    assert data["operator_workflow_event_counts"] == {"OPERATOR_HINT": 1, "LOCK_CONFIRMED": 1}
    assert data["operator_hint_count"] == 1
    assert data["operator_lock_confirmed_count"] == 1
    assert data["operator_target_lost_count"] == 0
    assert data["avg_operator_click_to_lock_frames"] == 3.0
    assert data["avg_operator_verify_age_frames"] == 1.5


def test_telemetry_label_uses_detection_source_value():
    assert _telemetry_label(DetectionSource.NIGHT) == "night"
    assert _telemetry_label("-") == "-"


def test_evaluation_report_new_latency_fields_default_none():
    data = _report().to_dict()
    assert "latency_p95_ms" in data
    assert "latency_p99_ms" in data
    assert data["latency_p95_ms"] is None
    assert data["latency_p99_ms"] is None


def test_evaluation_report_track_fragmentation_rate_default_none():
    data = _report().to_dict()
    assert "track_fragmentation_rate" in data
    assert data["track_fragmentation_rate"] is None


def test_evaluation_report_latency_fields_set_correctly():
    data = _report(latency_p95_ms=12.5, latency_p99_ms=18.0).to_dict()
    assert data["latency_p95_ms"] == 12.5
    assert data["latency_p99_ms"] == 18.0


def test_evaluation_report_track_fragmentation_rate_set():
    data = _report(track_fragmentation_rate=0.25).to_dict()
    assert data["track_fragmentation_rate"] == 0.25


def test_evaluation_report_avg_operator_click_to_lock_in_to_dict():
    data = _report(avg_operator_click_to_lock_frames=5.0).to_dict()
    assert data["avg_operator_click_to_lock_frames"] == 5.0
