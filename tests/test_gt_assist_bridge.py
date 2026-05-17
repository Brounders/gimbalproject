from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np

import app.qml_bridge.gt_assist_bridge as gt_mod


def _make_video(path: Path, *, frames: int = 8) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (96, 72))
    assert writer.isOpened()
    for idx in range(frames):
        frame = np.zeros((72, 96, 3), dtype=np.uint8)
        x = 18 + idx * 3
        y = 20 + idx
        frame[y : y + 14, x : x + 14] = (255, 255, 255)
        writer.write(frame)
    writer.release()


def test_open_video_sets_frame_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(gt_mod, "ROOT", tmp_path)
    video = tmp_path / "clip.mp4"
    _make_video(video)

    bridge = gt_mod.GtAssistBridge(gt_mod.GtFrameProvider())
    message = bridge.openVideo(str(video))

    assert "Открыто" in message
    assert bridge.sourceName == "clip.mp4"
    assert bridge.frameCount == 8
    assert bridge.frameWidth == 96
    assert bridge.frameHeight == 72
    assert bridge.frameIndex == 0


def test_set_bbox_creates_visible_row_and_json(tmp_path, monkeypatch):
    monkeypatch.setattr(gt_mod, "ROOT", tmp_path)
    video = tmp_path / "clip.mp4"
    _make_video(video)

    bridge = gt_mod.GtAssistBridge(gt_mod.GtFrameProvider())
    bridge.openVideo(str(video))
    message = bridge.setBbox(18, 20, 32, 34)

    assert "BBox" in message
    assert bridge.rowCount == 1
    assert bridge.selectedBboxJson == "[18, 20, 32, 34]"


def test_mark_invisible_allows_empty_bbox_export(tmp_path, monkeypatch):
    monkeypatch.setattr(gt_mod, "ROOT", tmp_path)
    video = tmp_path / "clip.mp4"
    _make_video(video)

    bridge = gt_mod.GtAssistBridge(gt_mod.GtFrameProvider())
    bridge.openVideo(str(video))
    bridge.markInvisible()
    message = bridge.exportCsv()

    assert "Экспортировано" in message
    out_path = tmp_path / bridge.exportPath
    rows = list(csv.DictReader(out_path.open("r", encoding="utf-8")))
    assert rows[0]["visible"] == "0"
    assert rows[0]["x1"] == ""
    assert rows[0]["note"] == "invisible"


def test_propagate_tracks_moving_square_and_exports_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(gt_mod, "ROOT", tmp_path)
    video = tmp_path / "clip.mp4"
    _make_video(video, frames=10)

    bridge = gt_mod.GtAssistBridge(gt_mod.GtFrameProvider())
    bridge.openVideo(str(video))
    bridge.setBbox(18, 20, 32, 34)
    message = bridge.propagate(5)

    assert "Протянуто" in message
    assert bridge.rowCount >= 2

    bridge.exportCsv()
    rows = list(csv.DictReader((tmp_path / bridge.exportPath).open("r", encoding="utf-8")))
    visible_rows = [row for row in rows if row["visible"] == "1"]
    assert len(visible_rows) >= 2
    assert visible_rows[0]["frame_index"] == "0"


def test_invalid_tiny_bbox_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(gt_mod, "ROOT", tmp_path)
    video = tmp_path / "clip.mp4"
    _make_video(video)

    bridge = gt_mod.GtAssistBridge(gt_mod.GtFrameProvider())
    bridge.openVideo(str(video))

    assert "слишком маленький" in bridge.setBbox(10, 10, 11, 11)
    assert bridge.rowCount == 0
