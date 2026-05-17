from __future__ import annotations

import csv
import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QObject, Property, QSize, Qt, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtWidgets import QFileDialog

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class GtRow:
    source: str
    frame_index: int
    visible: bool
    bbox: Optional[tuple[int, int, int, int]]
    note: str = ""


class GtFrameProvider(QQuickImageProvider):
    """Expose the current GT assist video frame to QML."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)
        self._lock = threading.RLock()
        self._image = QImage(960, 540, QImage.Format_RGB32)
        self._image.fill(0x050810)

    def update_frame(self, frame: np.ndarray | None) -> None:
        if frame is None or frame.size == 0 or frame.ndim != 3:
            return
        height, width = frame.shape[:2]
        rgb = frame[:, :, :3][:, :, ::-1].copy()
        image = QImage(rgb.data, width, height, rgb.strides[0], QImage.Format_RGB888).copy()
        with self._lock:
            self._image = image

    def requestImage(self, id_: str, size: QSize, requested_size: QSize) -> QImage:
        _ = id_
        with self._lock:
            image = self._image.copy()
        if requested_size.isValid() and requested_size.width() > 0 and requested_size.height() > 0:
            image = image.scaled(requested_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        size.setWidth(image.width())
        size.setHeight(image.height())
        return image


class GtAssistBridge(QObject):
    changed = Signal()
    previewChanged = Signal()
    exported = Signal()

    def __init__(self, frame_provider: GtFrameProvider) -> None:
        super().__init__()
        self._provider = frame_provider
        self._cap: cv2.VideoCapture | None = None
        self._source_path = ""
        self._source_name = ""
        self._frame_index = 0
        self._frame_count = 0
        self._frame_width = 0
        self._frame_height = 0
        self._preview_revision = 0
        self._status = "GT Assist готов"
        self._bbox: tuple[int, int, int, int] | None = None
        self._rows: dict[int, GtRow] = {}
        self._export_path = ""
        self._last_dir = str(ROOT / "test_videos")
        self._current_frame: np.ndarray | None = None

    @Property(str, notify=changed)
    def sourcePath(self) -> str:
        return self._source_path

    @Property(str, notify=changed)
    def sourceName(self) -> str:
        return self._source_name

    @Property(int, notify=changed)
    def frameIndex(self) -> int:
        return int(self._frame_index)

    @Property(int, notify=changed)
    def frameCount(self) -> int:
        return int(self._frame_count)

    @Property(int, notify=changed)
    def frameWidth(self) -> int:
        return int(self._frame_width)

    @Property(int, notify=changed)
    def frameHeight(self) -> int:
        return int(self._frame_height)

    @Property(str, notify=previewChanged)
    def previewSource(self) -> str:
        return f"image://gtFrames/current?rev={self._preview_revision}"

    @Property(str, notify=changed)
    def selectedBboxJson(self) -> str:
        return json.dumps(list(self._bbox) if self._bbox is not None else [])

    @Property(int, notify=changed)
    def rowCount(self) -> int:
        return len(self._rows)

    @Property(str, notify=changed)
    def statusText(self) -> str:
        return self._status

    @Property(str, notify=changed)
    def exportPath(self) -> str:
        return self._export_path

    @Property(bool, notify=changed)
    def hasSource(self) -> bool:
        return self._cap is not None and bool(self._source_path)

    @Property(bool, notify=changed)
    def hasBbox(self) -> bool:
        return self._bbox is not None

    def _set_status(self, text: str) -> str:
        self._status = text
        self.changed.emit()
        return text

    def _emit_frame(self) -> None:
        self._provider.update_frame(self._current_frame)
        self._preview_revision += 1
        self.previewChanged.emit()
        self.changed.emit()

    def _clip_bbox(self, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int] | None:
        if self._frame_width <= 0 or self._frame_height <= 0:
            return None
        x1, y1, x2, y2 = [int(v) for v in bbox]
        x1 = max(0, min(self._frame_width - 1, x1))
        y1 = max(0, min(self._frame_height - 1, y1))
        x2 = max(0, min(self._frame_width, x2))
        y2 = max(0, min(self._frame_height, y2))
        if x2 - x1 < 4 or y2 - y1 < 4:
            return None
        return x1, y1, x2, y2

    def _read_frame(self, index: int) -> bool:
        if self._cap is None:
            return False
        index = max(0, min(int(index), max(0, self._frame_count - 1)))
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return False
        self._frame_index = index
        self._current_frame = frame
        row = self._rows.get(index)
        self._bbox = row.bbox if row is not None and row.visible else self._bbox
        self._emit_frame()
        return True

    @Slot(result=str)
    def browseVideoFile(self) -> str:
        path, _ = QFileDialog.getOpenFileName(
            None,
            "Выбрать видео для GT Assist",
            self._last_dir,
            "Video files (*.mp4 *.avi *.mov *.mkv);;All files (*)",
        )
        if path:
            self._last_dir = str(Path(path).parent)
        return path or ""

    @Slot(str, result=str)
    def openVideo(self, path: str) -> str:
        source = Path(path).expanduser()
        if not source.is_absolute():
            source = ROOT / source
        if not source.exists():
            return self._set_status(f"Файл не найден: {path}")

        if self._cap is not None:
            self._cap.release()
        cap = cv2.VideoCapture(str(source))
        if not cap.isOpened():
            self._cap = None
            return self._set_status(f"Не удалось открыть видео: {source.name}")

        self._cap = cap
        self._source_path = str(source)
        self._source_name = source.name
        self._frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        self._frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
        self._frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
        self._rows = {}
        self._bbox = None
        self._export_path = ""
        self._last_dir = str(source.parent)
        if not self._read_frame(0):
            return self._set_status(f"Видео открыто, но первый кадр не прочитан: {source.name}")
        return self._set_status(f"Открыто: {source.name} · {self._frame_count} кадров")

    @Slot(int, result=str)
    def goToFrame(self, index: int) -> str:
        if self._cap is None:
            return self._set_status("Сначала откройте видео")
        if self._read_frame(index):
            return self._set_status(f"Кадр {self._frame_index}")
        return self._set_status(f"Кадр не прочитан: {index}")

    @Slot(result=str)
    def nextFrame(self) -> str:
        return self.goToFrame(self._frame_index + 1)

    @Slot(result=str)
    def prevFrame(self) -> str:
        return self.goToFrame(self._frame_index - 1)

    @Slot(int, int, int, int, result=str)
    def setBbox(self, x1: int, y1: int, x2: int, y2: int) -> str:
        bbox = self._clip_bbox((x1, y1, x2, y2))
        if bbox is None:
            return self._set_status("BBox слишком маленький или вне кадра")
        self._bbox = bbox
        self._rows[self._frame_index] = GtRow(self._source_path, self._frame_index, True, bbox, "manual")
        self.changed.emit()
        return self._set_status(f"BBox сохранён на кадре {self._frame_index}")

    @Slot(result=str)
    def markInvisible(self) -> str:
        if not self._source_path:
            return self._set_status("Сначала откройте видео")
        self._rows[self._frame_index] = GtRow(self._source_path, self._frame_index, False, None, "invisible")
        self.changed.emit()
        return self._set_status(f"Кадр {self._frame_index}: цель не видна")

    @Slot(result=str)
    def clearCurrent(self) -> str:
        self._rows.pop(self._frame_index, None)
        self.changed.emit()
        return self._set_status(f"Разметка кадра {self._frame_index} очищена")

    def _track_next(
        self,
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
        template_gray: np.ndarray,
    ) -> tuple[tuple[int, int, int, int] | None, float]:
        x1, y1, x2, y2 = bbox
        bw, bh = x2 - x1, y2 - y1
        pad_x = max(24, bw * 3)
        pad_y = max(24, bh * 3)
        sx1 = max(0, x1 - pad_x)
        sy1 = max(0, y1 - pad_y)
        sx2 = min(self._frame_width, x2 + pad_x)
        sy2 = min(self._frame_height, y2 + pad_y)
        search = cv2.cvtColor(frame[sy1:sy2, sx1:sx2], cv2.COLOR_BGR2GRAY)
        if search.shape[0] < template_gray.shape[0] or search.shape[1] < template_gray.shape[1]:
            return None, 0.0
        response = cv2.matchTemplate(search, template_gray, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(response)
        nx1 = sx1 + int(max_loc[0])
        ny1 = sy1 + int(max_loc[1])
        return self._clip_bbox((nx1, ny1, nx1 + bw, ny1 + bh)), float(max_val)

    @Slot(int, result=str)
    def propagate(self, frame_limit: int = 120) -> str:
        if self._cap is None or self._current_frame is None:
            return self._set_status("Сначала откройте видео")
        if self._bbox is None:
            return self._set_status("Сначала выделите bbox цели")

        start_index = int(self._frame_index)
        bbox = self._bbox
        x1, y1, x2, y2 = bbox
        template = cv2.cvtColor(self._current_frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        if template.size == 0:
            return self._set_status("Template пустой — выделите bbox заново")

        made = 0
        min_score = 0.42
        alpha = 0.16
        max_index = min(self._frame_count - 1, start_index + max(1, int(frame_limit)))
        for index in range(start_index + 1, max_index + 1):
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = self._cap.read()
            if not ok or frame is None:
                break
            next_bbox, score = self._track_next(frame, bbox, template)
            if next_bbox is None or score < min_score:
                self._frame_index = index
                self._current_frame = frame
                self._bbox = bbox
                self._emit_frame()
                return self._set_status(f"Протяжка остановлена на {index}: score {score:.2f}")

            bbox = next_bbox
            self._rows[index] = GtRow(self._source_path, index, True, bbox, f"propagated:{score:.3f}")
            nx1, ny1, nx2, ny2 = bbox
            patch = cv2.cvtColor(frame[ny1:ny2, nx1:nx2], cv2.COLOR_BGR2GRAY)
            if patch.shape == template.shape:
                template = cv2.addWeighted(patch, alpha, template, 1.0 - alpha, 0.0)
            made += 1

        self._read_frame(start_index + made)
        return self._set_status(f"Протянуто кадров: {made}")

    @Slot(result=str)
    def exportCsv(self) -> str:
        if not self._rows:
            return self._set_status("Нет разметки для экспорта")
        out_dir = ROOT / "configs" / "gt_minipack" / "generated"
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(self._source_path).stem or "source"
        out_path = out_dir / f"{stem}_gt_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        with out_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["source", "frame_index", "visible", "x1", "y1", "x2", "y2", "note"])
            writer.writeheader()
            for frame_index in sorted(self._rows):
                row = self._rows[frame_index]
                x1 = y1 = x2 = y2 = ""
                if row.visible and row.bbox is not None:
                    x1, y1, x2, y2 = row.bbox
                writer.writerow({
                    "source": row.source,
                    "frame_index": row.frame_index,
                    "visible": 1 if row.visible else 0,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "note": row.note,
                })
        self._export_path = str(out_path.relative_to(ROOT))
        self.exported.emit()
        return self._set_status(f"Экспортировано: {self._export_path}")
