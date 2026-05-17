"""DTS quality + duplicate detection helpers (real, deterministic).

Pure-data layer: takes ``AnnotationRecord`` objects and (optionally) opens
source videos via cv2 to compute Laplacian sharpness, mean exposure, crop
readability and bbox-fit metrics.  The functions are designed to be safe
without cv2 (return ``unavailable`` rows) and never to raise on missing
sources.

All thresholds are named module constants — change here, not at call sites.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from app.training_desk_data import AnnotationRecord


# ── Quality state codes (used by UI + tests) ────────────────────────────────
QUALITY_OK = 'ok'
QUALITY_WARN = 'warn'
QUALITY_FAIL = 'fail'
QUALITY_NA = 'na'


# ── Thresholds ──────────────────────────────────────────────────────────────
SMALL_AREA_RATIO_WARN = 0.0008      # bbox area / frame area
LARGE_AREA_RATIO_WARN = 0.65
MIN_CROP_PIXELS = 8                  # below this width or height crop is unusable
SHARPNESS_WARN = 25.0                # Laplacian variance below = blurry
SHARPNESS_FAIL = 8.0
EXPOSURE_DARK_FAIL = 12.0            # mean brightness below = near-black
EXPOSURE_DARK_WARN = 30.0
EXPOSURE_BRIGHT_WARN = 230.0         # mean brightness above = washed out
EXPOSURE_BRIGHT_FAIL = 248.0

# Duplicate detection thresholds
DUP_NEAR_FRAME_DISTANCE = 5
DUP_NEAR_IOU = 0.85
DUP_SAME_FRAME_IOU = 0.50


@dataclass
class QualityRow:
    """A single quality check result."""
    name: str
    state: str
    value: str = ''
    note: str = ''

    @property
    def is_warning(self) -> bool:
        return self.state in {QUALITY_WARN, QUALITY_FAIL}


@dataclass
class QualityReport:
    """Aggregate quality assessment for one record."""
    record_id: str
    rows: list[QualityRow]
    warnings: int = 0
    fails: int = 0

    @classmethod
    def from_rows(cls, record_id: str, rows: list[QualityRow]) -> 'QualityReport':
        warns = sum(1 for r in rows if r.state == QUALITY_WARN)
        fails = sum(1 for r in rows if r.state == QUALITY_FAIL)
        return cls(record_id=record_id, rows=rows, warnings=warns, fails=fails)


# ── BBox / area helpers ────────────────────────────────────────────────────


def _bbox_area(bbox: tuple[int, int, int, int]) -> int:
    x1, y1, x2, y2 = bbox
    w = max(0, x2 - x1)
    h = max(0, y2 - y1)
    return w * h


def _bbox_inside(bbox: tuple[int, int, int, int], frame_w: int, frame_h: int) -> bool:
    x1, y1, x2, y2 = bbox
    return 0 <= x1 < x2 <= frame_w and 0 <= y1 < y2 <= frame_h


def bbox_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    """Standard IoU between two xyxy bboxes; 0 if either is degenerate."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    if ax2 <= ax1 or ay2 <= ay1 or bx2 <= bx1 or by2 <= by1:
        return 0.0
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return float(inter) / float(union)


# ── Frame access (cv2-aware, fault-tolerant) ───────────────────────────────


def _read_frame(source: str, frame_index: int) -> Optional['object']:  # numpy.ndarray when cv2 ok
    try:
        import cv2  # type: ignore
    except Exception:
        return None
    if not source:
        return None
    src_path = Path(source)
    if not src_path.exists():
        return None
    cap = cv2.VideoCapture(str(src_path))
    try:
        if not cap.isOpened():
            return None
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(frame_index)))
        ok, frame = cap.read()
    finally:
        cap.release()
    return frame if ok else None


def _frame_size(source: str) -> Optional[tuple[int, int]]:
    """Return (width, height) of the source video, or None if unreadable."""
    try:
        import cv2  # type: ignore
    except Exception:
        return None
    src_path = Path(source)
    if not src_path.exists():
        return None
    cap = cv2.VideoCapture(str(src_path))
    try:
        if not cap.isOpened():
            return None
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    finally:
        cap.release()
    if w <= 0 or h <= 0:
        return None
    return w, h


# ── Per-row quality checks ─────────────────────────────────────────────────


def _row_structural(record: AnnotationRecord) -> QualityRow:
    if record.event != 'operator_bbox':
        return QualityRow('Структура', QUALITY_FAIL, value='—',
                          note=f'event={record.event} (ожидается operator_bbox)')
    if record.bbox_xyxy is None:
        return QualityRow('Структура', QUALITY_FAIL, value='—', note='нет bbox')
    if record.frame_index < 0:
        return QualityRow('Структура', QUALITY_FAIL, value='—', note='frame_index<0')
    if not record.source:
        return QualityRow('Структура', QUALITY_FAIL, value='—', note='нет source')
    return QualityRow('Структура', QUALITY_OK, value='OK')


def _row_source(record: AnnotationRecord) -> QualityRow:
    if not record.source:
        return QualityRow('Источник', QUALITY_FAIL, value='—', note='нет пути')
    if not Path(record.source).exists():
        return QualityRow('Источник', QUALITY_FAIL, value='нет файла',
                          note=Path(record.source).name)
    size = _frame_size(record.source)
    if size is None:
        return QualityRow('Источник', QUALITY_NA, value='cv2 нет/не открывается')
    w, h = size
    return QualityRow('Источник', QUALITY_OK, value=f'{w}×{h}')


def _row_bbox_bounds(record: AnnotationRecord) -> QualityRow:
    if record.bbox_xyxy is None:
        return QualityRow('BBox bounds', QUALITY_FAIL, value='—')
    size = _frame_size(record.source) if record.source else None
    if size is None:
        return QualityRow('BBox bounds', QUALITY_NA, value='размер кадра неизвестен')
    w, h = size
    if not _bbox_inside(record.bbox_xyxy, w, h):
        return QualityRow('BBox bounds', QUALITY_FAIL, value='вне кадра',
                          note=f'bbox={record.bbox_xyxy} frame={w}×{h}')
    return QualityRow('BBox bounds', QUALITY_OK, value='в кадре')


def _row_bbox_size(record: AnnotationRecord) -> QualityRow:
    if record.bbox_xyxy is None:
        return QualityRow('BBox size', QUALITY_FAIL, value='—')
    size = _frame_size(record.source) if record.source else None
    if size is None:
        return QualityRow('BBox size', QUALITY_NA, value='нет размера кадра')
    w, h = size
    bbox_area = _bbox_area(record.bbox_xyxy)
    frame_area = max(1, w * h)
    ratio = bbox_area / frame_area
    if ratio < SMALL_AREA_RATIO_WARN:
        return QualityRow('BBox size', QUALITY_WARN, value=f'{ratio*100:.2f}%',
                          note='слишком мелкий')
    if ratio > LARGE_AREA_RATIO_WARN:
        return QualityRow('BBox size', QUALITY_WARN, value=f'{ratio*100:.1f}%',
                          note='слишком большой')
    return QualityRow('BBox size', QUALITY_OK, value=f'{ratio*100:.2f}%')


def _row_crop_readable(record: AnnotationRecord, frame=None) -> QualityRow:
    if record.bbox_xyxy is None:
        return QualityRow('Crop', QUALITY_FAIL, value='—')
    x1, y1, x2, y2 = record.bbox_xyxy
    cw = max(0, x2 - x1)
    ch = max(0, y2 - y1)
    if cw < MIN_CROP_PIXELS or ch < MIN_CROP_PIXELS:
        return QualityRow('Crop', QUALITY_FAIL, value=f'{cw}×{ch}',
                          note='слишком маленький crop для обучения')
    return QualityRow('Crop', QUALITY_OK, value=f'{cw}×{ch}')


def _row_sharpness(record: AnnotationRecord, frame=None) -> QualityRow:
    if frame is None:
        return QualityRow('Резкость', QUALITY_NA, value='нет кадра')
    if record.bbox_xyxy is None:
        return QualityRow('Резкость', QUALITY_FAIL, value='—')
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return QualityRow('Резкость', QUALITY_NA, value='cv2/numpy нет')
    x1, y1, x2, y2 = record.bbox_xyxy
    h, w = frame.shape[:2]
    cx1 = max(0, x1)
    cy1 = max(0, y1)
    cx2 = min(w, x2)
    cy2 = min(h, y2)
    if cx2 <= cx1 or cy2 <= cy1:
        return QualityRow('Резкость', QUALITY_FAIL, value='пустой crop')
    crop = frame[cy1:cy2, cx1:cx2]
    if crop.size == 0:
        return QualityRow('Резкость', QUALITY_FAIL, value='пустой crop')
    if crop.ndim == 3:
        crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    else:
        crop_gray = crop
    lap = cv2.Laplacian(crop_gray, cv2.CV_64F)
    var = float(np.var(lap))
    if var < SHARPNESS_FAIL:
        return QualityRow('Резкость', QUALITY_FAIL, value=f'{var:.1f}', note='размытый')
    if var < SHARPNESS_WARN:
        return QualityRow('Резкость', QUALITY_WARN, value=f'{var:.1f}', note='слабая резкость')
    return QualityRow('Резкость', QUALITY_OK, value=f'{var:.1f}')


def _row_exposure(record: AnnotationRecord, frame=None) -> QualityRow:
    if frame is None:
        return QualityRow('Экспозиция', QUALITY_NA, value='нет кадра')
    if record.bbox_xyxy is None:
        return QualityRow('Экспозиция', QUALITY_FAIL, value='—')
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return QualityRow('Экспозиция', QUALITY_NA, value='cv2/numpy нет')
    x1, y1, x2, y2 = record.bbox_xyxy
    h, w = frame.shape[:2]
    cx1 = max(0, x1); cy1 = max(0, y1)
    cx2 = min(w, x2); cy2 = min(h, y2)
    if cx2 <= cx1 or cy2 <= cy1:
        return QualityRow('Экспозиция', QUALITY_FAIL, value='пустой crop')
    crop = frame[cy1:cy2, cx1:cx2]
    if crop.size == 0:
        return QualityRow('Экспозиция', QUALITY_FAIL, value='пустой crop')
    if crop.ndim == 3:
        crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    else:
        crop_gray = crop
    mean_v = float(np.mean(crop_gray))
    if mean_v < EXPOSURE_DARK_FAIL:
        return QualityRow('Экспозиция', QUALITY_FAIL, value=f'{mean_v:.0f}',
                          note='почти чёрный')
    if mean_v < EXPOSURE_DARK_WARN:
        return QualityRow('Экспозиция', QUALITY_WARN, value=f'{mean_v:.0f}',
                          note='тёмный crop')
    if mean_v > EXPOSURE_BRIGHT_FAIL:
        return QualityRow('Экспозиция', QUALITY_FAIL, value=f'{mean_v:.0f}',
                          note='пересвет')
    if mean_v > EXPOSURE_BRIGHT_WARN:
        return QualityRow('Экспозиция', QUALITY_WARN, value=f'{mean_v:.0f}',
                          note='слишком светлый')
    return QualityRow('Экспозиция', QUALITY_OK, value=f'{mean_v:.0f}')


# ── Public quality API ─────────────────────────────────────────────────────


def evaluate_record_quality(record: AnnotationRecord) -> QualityReport:
    """Run the full deterministic quality stack for a single record.

    Source/frame access is best-effort: if cv2 cannot open the video the
    pixel-level rows return ``QUALITY_NA``.  This function never raises.
    """
    rows: list[QualityRow] = []
    rows.append(_row_structural(record))
    rows.append(_row_source(record))
    rows.append(_row_bbox_bounds(record))
    rows.append(_row_bbox_size(record))
    rows.append(_row_crop_readable(record))

    # Pixel-level rows need the actual frame; load once.
    frame = None
    if record.bbox_xyxy is not None and record.source and Path(record.source).exists():
        frame = _read_frame(record.source, record.frame_index)

    rows.append(_row_sharpness(record, frame=frame))
    rows.append(_row_exposure(record, frame=frame))
    return QualityReport.from_rows(record.record_id, rows)


def aggregate_quality(records: Iterable[AnnotationRecord]) -> dict[str, int]:
    """Aggregate counts of warning/fail/na rows across records.

    Lightweight: only structural+bounds+size checks (no frame I/O) so this
    can be called for the whole pack without opening every video.
    """
    total = 0
    invalid_struct = 0
    out_of_bounds = 0
    small_or_large = 0
    missing_source = 0
    for record in records:
        total += 1
        if record.event != 'operator_bbox' or record.bbox_xyxy is None:
            invalid_struct += 1
            continue
        if not record.source:
            missing_source += 1
            continue
        size = _frame_size(record.source) if Path(record.source).exists() else None
        if size is None:
            missing_source += 1
            continue
        w, h = size
        if not _bbox_inside(record.bbox_xyxy, w, h):
            out_of_bounds += 1
            continue
        bbox_area = _bbox_area(record.bbox_xyxy)
        ratio = bbox_area / max(1, w * h)
        if ratio < SMALL_AREA_RATIO_WARN or ratio > LARGE_AREA_RATIO_WARN:
            small_or_large += 1
    return {
        'total': total,
        'invalid_struct': invalid_struct,
        'out_of_bounds': out_of_bounds,
        'small_or_large': small_or_large,
        'missing_source': missing_source,
    }


# ── Duplicate detection ────────────────────────────────────────────────────


@dataclass
class DuplicateLink:
    """Link between two records that look like duplicates of each other."""
    other_record_id: str
    kind: str           # 'exact' | 'near' | 'overlap'
    iou: float
    frame_distance: int
    other_frame_index: int
    other_status: str
    other_source_basename: str


def find_duplicates(records: Iterable[AnnotationRecord]) -> dict[str, list[DuplicateLink]]:
    """Compute duplicate links per record.

    Three rules:
        1. ``exact``  — same source + same frame + same bbox.
        2. ``overlap``— same source + same frame + IoU >= ``DUP_SAME_FRAME_IOU``.
        3. ``near``   — same source + |Δframe| <= ``DUP_NEAR_FRAME_DISTANCE``
                        and IoU >= ``DUP_NEAR_IOU``.

    Records lacking bbox/source are silently ignored (no false-positive link).
    Returns a mapping ``record_id → list[DuplicateLink]`` (omits empty links).
    """
    items: list[AnnotationRecord] = [
        r for r in records
        if r.event == 'operator_bbox' and r.bbox_xyxy is not None and r.source
    ]
    by_source: dict[str, list[AnnotationRecord]] = {}
    for r in items:
        by_source.setdefault(r.source, []).append(r)

    result: dict[str, list[DuplicateLink]] = {}

    for source_records in by_source.values():
        n = len(source_records)
        for i in range(n):
            a = source_records[i]
            for j in range(n):
                if i == j:
                    continue
                b = source_records[j]
                df = abs(int(a.frame_index) - int(b.frame_index))
                iou = bbox_iou(a.bbox_xyxy, b.bbox_xyxy) if (a.bbox_xyxy and b.bbox_xyxy) else 0.0
                kind: Optional[str] = None
                if df == 0 and a.bbox_xyxy == b.bbox_xyxy:
                    kind = 'exact'
                elif df == 0 and iou >= DUP_SAME_FRAME_IOU:
                    kind = 'overlap'
                elif df <= DUP_NEAR_FRAME_DISTANCE and iou >= DUP_NEAR_IOU:
                    kind = 'near'
                if kind is None:
                    continue
                link = DuplicateLink(
                    other_record_id=b.record_id,
                    kind=kind,
                    iou=round(iou, 4),
                    frame_distance=df,
                    other_frame_index=int(b.frame_index),
                    other_status=b.status,
                    other_source_basename=Path(b.source).name,
                )
                result.setdefault(a.record_id, []).append(link)
    return result


def duplicate_summary(links: dict[str, list[DuplicateLink]]) -> dict[str, int]:
    """Counts of records-with-links by kind (each record counted once per kind)."""
    exact = sum(1 for v in links.values() if any(l.kind == 'exact' for l in v))
    overlap = sum(1 for v in links.values() if any(l.kind == 'overlap' for l in v))
    near = sum(1 for v in links.values() if any(l.kind == 'near' for l in v))
    return {
        'records_with_duplicates': len(links),
        'exact': exact,
        'overlap': overlap,
        'near': near,
    }
