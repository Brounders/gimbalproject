from __future__ import annotations

import csv
import json
from pathlib import Path

import app.qml_bridge.target_lab_bridge as lab_mod
import app.qml_bridge.gt_assist_bridge as gt_mod


def _make_video(path: Path) -> None:
    import cv2
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (64, 48))
    assert writer.isOpened()
    for _ in range(3):
        frame = np.zeros((48, 64, 3), dtype=np.uint8)
        frame[12:24, 20:32] = (255, 255, 255)
        writer.write(frame)
    writer.release()


class _DummyDts:
    totalCount = 9
    candidateFrameCount = 3
    candidateStatusLabel = "данные готовы"

    def countStatus(self, status: str) -> int:
        return {
            "new": 4,
            "accepted": 2,
            "hard_negative": 1,
            "rejected": 2,
        }.get(status, 0)


def _write_gt(path: Path, source: str, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["source", "frame_index", "visible", "x1", "y1", "x2", "y2", "note"])
        writer.writeheader()
        for row in rows:
            data = {
                "source": source,
                "frame_index": row.get("frame_index", 0),
                "visible": row.get("visible", 1),
                "x1": row.get("x1", 10),
                "y1": row.get("y1", 20),
                "x2": row.get("x2", 30),
                "y2": row.get("y2", 40),
                "note": row.get("note", "manual"),
            }
            if not data["visible"]:
                data.update({"x1": "", "y1": "", "x2": "", "y2": "", "note": "invisible"})
            writer.writerow(data)


def test_target_lab_scans_existing_gt_minipack(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    generated = tmp_path / "configs" / "gt_minipack" / "generated"
    _write_gt(
        generated / "IR_DRONE_025_gt.csv",
        "/clips/IR_DRONE_025.mp4",
        [{"frame_index": 0}, {"frame_index": 1}, {"frame_index": 2, "visible": 0}],
    )
    _write_gt(
        generated / "f1_3_EO_dji_mavic_2_gt.csv",
        "/clips/f1_3_EO_dji_mavic_2.mp4",
        [{"frame_index": 5}, {"frame_index": 6}],
    )

    bridge = lab_mod.TargetLabBridge(dts_bridge=_DummyDts())

    assert bridge.gtFileCount == 2
    assert bridge.gtClipCount == 2
    assert bridge.gtRowCount == 5
    assert bridge.gtVisibleRowCount == 4
    assert bridge.gtInvisibleRowCount == 1
    assert "IR" in bridge.gtSceneSummary
    assert "EO" in bridge.gtSceneSummary
    assert "2 CSV" in bridge.gtSummaryText


def test_target_lab_files_json_exposes_recent_files(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    generated = tmp_path / "configs" / "gt_minipack" / "generated"
    _write_gt(generated / "IR_AIRPLANE_003_gt.csv", "/clips/IR_AIRPLANE_003.mp4", [{"frame_index": 0, "visible": 0}])

    bridge = lab_mod.TargetLabBridge()
    files = json.loads(bridge.gtFilesJson)

    assert files[0]["name"] == "IR_AIRPLANE_003_gt.csv"
    assert files[0]["rows"] == 1
    assert files[0]["visible_rows"] == 0
    assert files[0]["invisible_rows"] == 1
    assert files[0]["scene"] == "IR_NEGATIVE"


def test_target_lab_refresh_picks_up_new_exports(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    bridge = lab_mod.TargetLabBridge()
    assert bridge.gtFileCount == 0

    generated = tmp_path / "configs" / "gt_minipack" / "generated"
    _write_gt(generated / "V_BIRD_030_gt.csv", "/clips/V_BIRD_030.mp4", [{"frame_index": 7, "visible": 0}])

    bridge.refresh()

    assert bridge.gtFileCount == 1
    assert bridge.gtClipCount == 1
    assert bridge.gtSceneSummary == "NEGATIVE:1"


def test_target_lab_classifies_scene_from_source_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    generated = tmp_path / "configs" / "gt_minipack" / "generated"
    _write_gt(generated / "5_minie3_range_far_gt.csv", "/datasets/f3_mini_e/ir/5_minie3_range_far.mp4", [{"frame_index": 0}])
    _write_gt(generated / "7_minie5_range_all_cut_blur_gt.csv", "/datasets/f5_mini_e/eo/7_minie5_range_all_cut_blur.mp4", [{"frame_index": 0}])

    bridge = lab_mod.TargetLabBridge()

    assert "IR:1" in bridge.gtSceneSummary
    assert "EO:1" in bridge.gtSceneSummary
    assert "UNKNOWN" not in bridge.gtSceneSummary


def test_target_lab_mission_summary_combines_dts_and_gt(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    generated = tmp_path / "configs" / "gt_minipack" / "generated"
    _write_gt(generated / "clip_gt.csv", "/clips/clip.mp4", [{"frame_index": 0}])

    bridge = lab_mod.TargetLabBridge(dts_bridge=_DummyDts())

    assert "DTS 9" in bridge.labSummaryText
    assert "NEW 4" in bridge.labSummaryText
    assert "GT 1 CSV" in bridge.labSummaryText
    assert bridge.dtsAcceptedCount == 2
    assert bridge.dtsNegativeCount == 1


def test_target_lab_material_cards_are_user_facing(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    generated = tmp_path / "configs" / "gt_minipack" / "generated"
    _write_gt(generated / "ir_clip_gt.csv", "/clips/ir/ir_clip.mp4", [{"frame_index": 0}, {"frame_index": 1}])
    _write_gt(generated / "eo_bird_gt.csv", "/clips/eo/eo_bird.mp4", [{"frame_index": 0, "visible": 0}])

    bridge = lab_mod.TargetLabBridge(dts_bridge=_DummyDts())
    cards = json.loads(bridge.materialCardsJson)

    assert bridge.materialTitle == "2 клипа · 3 кадра"
    assert bridge.materialSubtitle == "IR:1 · EO_NEGATIVE:1"
    assert cards[0]["scene"] == "IR"
    assert cards[0]["clips"] == 1
    assert cards[0]["frames"] == 2
    assert cards[0]["role"] == "проверка"
    assert cards[1]["scene"] == "EO_NEGATIVE"
    assert cards[1]["role"] == "фон / не цель"


def test_target_lab_without_diagnostics_recommends_tracker_check(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    generated = tmp_path / "configs" / "gt_minipack" / "generated"
    _write_gt(generated / "ir_clip_gt.csv", "/clips/ir/ir_clip.mp4", [{"frame_index": 0}])

    bridge = lab_mod.TargetLabBridge(dts_bridge=_DummyDts())

    assert bridge.nextActionTitle == "Проверить трекер"
    assert "размеченной базе" in bridge.nextActionBody
    assert bridge.nextActionTone == "progress"
    assert bridge.primaryActionLabel == "ПРОВЕРИТЬ ТРЕКЕР"


def test_target_lab_check_cards_and_decision_use_diagnostics_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    result_dir = tmp_path / "runs" / "evaluations" / "tracking_gt_diagnostics" / "target_lab_20260515_220000"
    result_dir.mkdir(parents=True)
    (result_dir / "summary.json").write_text(
        json.dumps({
            "rows": [
                {
                    "source": "/clips/ir/ir_clip.mp4",
                    "clip": "ir_clip",
                    "scene": "IR",
                    "preset": "antiuav_thermal",
                    "sampled_frames": 100,
                    "recall_iou_01": 0.42,
                    "false_lock_rate_sampled": 0.31,
                    "avg_fps": 24.2,
                    "bbox_scale_step_p95": 0.72,
                },
                {
                    "source": "/clips/eo/eo_clip.mp4",
                    "clip": "eo_clip",
                    "scene": "EO",
                    "preset": "small_target",
                    "sampled_frames": 80,
                    "recall_iou_01": 0.84,
                    "false_lock_rate_sampled": 0.08,
                    "avg_fps": 67.0,
                    "bbox_scale_step_p95": 0.10,
                },
            ],
            "risks": ["ir_clip: low recall", "ir_clip: bbox scale jitter"],
        }),
        encoding="utf-8",
    )

    bridge = lab_mod.TargetLabBridge(dts_bridge=_DummyDts())
    bridge._on_gt_diagnostics_finished(0, None, result_dir)
    cards = json.loads(bridge.checkCardsJson)

    assert cards[0]["scene"] == "IR"
    assert cards[0]["recall_pct"] == 42
    assert cards[0]["false_lock_pct"] == 31
    assert cards[0]["status"] == "слабое место"
    assert cards[1]["scene"] == "EO"
    assert bridge.nextActionTitle == "Улучшить IR"
    assert "видит 42%" in bridge.nextActionBody
    assert "держит не там 31%" in bridge.nextActionBody
    assert bridge.nextActionTone == "warn"
    assert bridge.primaryActionLabel == "СОБРАТЬ УЛУЧШЕНИЕ"


def test_target_lab_loads_latest_diagnostics_on_start(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    result_dir = tmp_path / "runs" / "evaluations" / "tracking_gt_diagnostics" / "target_lab_20260515_230000"
    result_dir.mkdir(parents=True)
    (result_dir / "summary.json").write_text(
        json.dumps({
            "rows": [
                {
                    "source": "/clips/ir/ir_clip.mp4",
                    "clip": "ir_clip",
                    "sampled_frames": 100,
                    "recall_iou_01": 0.40,
                    "false_lock_rate_sampled": 0.90,
                    "avg_fps": 20.0,
                    "bbox_scale_step_p95": 0.20,
                }
            ],
            "risks": ["ir_clip: tracker off target on GT sample"],
        }),
        encoding="utf-8",
    )

    bridge = lab_mod.TargetLabBridge(dts_bridge=_DummyDts())
    cards = json.loads(bridge.checkCardsJson)

    assert bridge.checkTitle == "1 сцен · 1 слабых"
    assert "Последняя проверка" in bridge.checkSubtitle
    assert "bbox трекера вне вашей разметки" in bridge.checkSubtitle
    assert bridge.gtDiagnosticsResultDir == "runs/evaluations/tracking_gt_diagnostics/target_lab_20260515_230000"
    assert cards[0]["scene"] == "IR"
    assert cards[0]["false_lock_pct"] == 90


def test_target_lab_diagnostics_command_targets_existing_gt_base(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    generated = tmp_path / "configs" / "gt_minipack" / "generated"
    _write_gt(generated / "IR_DRONE_025_gt.csv", "/clips/IR_DRONE_025.mp4", [{"frame_index": 0}])

    bridge = lab_mod.TargetLabBridge()
    program, args = bridge._gt_diagnostics_command()

    assert program.endswith("python")
    assert str(tmp_path / "python_scripts" / "run_tracking_gt_diagnostics.py") in args
    assert str(generated) in args
    assert "--preset" in args
    assert "tracking_live_auto" in args
    assert "--scene-aware" in args
    assert "--render-errors" in args
    assert "--max-error-samples" in args
    assert "--tag" in args
    assert "target_lab" in args
    assert bridge.gtDiagnosticsCanRun is True


def test_target_lab_diagnostics_finish_reads_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    result_dir = tmp_path / "runs" / "evaluations" / "tracking_gt_diagnostics" / "target_lab_20260515_220000"
    result_dir.mkdir(parents=True)
    (result_dir / "summary.json").write_text(
        json.dumps({"rows": [{"clip": "clip-a"}, {"clip": "clip-b"}], "risks": ["clip-a: low recall"]}),
        encoding="utf-8",
    )

    bridge = lab_mod.TargetLabBridge()
    bridge._on_gt_diagnostics_finished(0, None, result_dir)

    assert bridge.gtDiagnosticsRunning is False
    assert bridge.gtDiagnosticsResultDir == "runs/evaluations/tracking_gt_diagnostics/target_lab_20260515_220000"
    assert "2 клипов" in bridge.gtDiagnosticsBody
    assert "1 риск" in bridge.gtDiagnosticsBody
    assert bridge.gtDiagnosticsTone == "warn"


def test_target_lab_refreshes_when_gt_assist_exports(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_mod, "ROOT", tmp_path)
    monkeypatch.setattr(gt_mod, "ROOT", tmp_path)
    video = tmp_path / "clip.mp4"
    _make_video(video)

    gt_bridge = gt_mod.GtAssistBridge(gt_mod.GtFrameProvider())
    target_lab = lab_mod.TargetLabBridge(gt_assist_bridge=gt_bridge)
    assert target_lab.gtFileCount == 0

    gt_bridge.openVideo(str(video))
    gt_bridge.setBbox(20, 12, 32, 24)
    gt_bridge.exportCsv()

    assert target_lab.gtFileCount == 1
    assert target_lab.gtRowCount == 1
