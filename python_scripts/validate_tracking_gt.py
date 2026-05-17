#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import cv2

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class GtAnnotation:
    source: str
    frame_index: int
    visible: bool
    bbox: tuple[int, int, int, int] | None
    note: str = ""


@dataclass
class ValidationSummary:
    files: int = 0
    clips: int = 0
    rows: int = 0
    visible_rows: int = 0
    invisible_rows: int = 0
    duplicate_count: int = 0
    invalid_count: int = 0
    warnings: list[str] | None = None
    errors: list[str] | None = None
    clips_detail: dict[str, dict] | None = None

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []
        if self.clips_detail is None:
            self.clips_detail = {}


def _parse_bool(value: str) -> bool | None:
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return None


def resolve_source(source: str) -> Path | None:
    text = str(source).strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if path.is_absolute():
        return path if path.exists() else None
    if path.exists():
        return path.resolve()
    rooted = ROOT / path
    return rooted.resolve() if rooted.exists() else None


def _video_meta(path: Path) -> tuple[int, int, int]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return 0, 0, 0
    try:
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
        return frames, width, height
    finally:
        cap.release()


def _parse_annotation(row: dict[str, str], *, file_path: Path, line_no: int, errors: list[str]) -> GtAnnotation | None:
    source = str(row.get("source", "")).strip()
    if not source:
        errors.append(f"{file_path}:{line_no}: empty source")
        return None
    try:
        frame_index = int(str(row.get("frame_index", "")).strip())
    except ValueError:
        errors.append(f"{file_path}:{line_no}: bad frame_index")
        return None
    if frame_index < 0:
        errors.append(f"{file_path}:{line_no}: negative frame_index")
        return None
    visible = _parse_bool(str(row.get("visible", "")))
    if visible is None:
        errors.append(f"{file_path}:{line_no}: bad visible value")
        return None

    bbox = None
    if visible:
        raw = [str(row.get(key, "")).strip() for key in ("x1", "y1", "x2", "y2")]
        if any(value == "" for value in raw):
            errors.append(f"{file_path}:{line_no}: visible row without bbox")
            return None
        try:
            x1, y1, x2, y2 = [int(float(value)) for value in raw]
        except ValueError:
            errors.append(f"{file_path}:{line_no}: non-numeric bbox")
            return None
        if x2 <= x1 or y2 <= y1:
            errors.append(f"{file_path}:{line_no}: invalid bbox geometry")
            return None
        bbox = (x1, y1, x2, y2)

    return GtAnnotation(
        source=source,
        frame_index=frame_index,
        visible=visible,
        bbox=bbox,
        note=str(row.get("note", "")).strip(),
    )


def load_annotations(paths: Iterable[Path]) -> list[GtAnnotation]:
    annotations: list[GtAnnotation] = []
    errors: list[str] = []
    for file_path in paths:
        with file_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for line_no, row in enumerate(reader, start=2):
                item = _parse_annotation(row, file_path=file_path, line_no=line_no, errors=errors)
                if item is not None:
                    annotations.append(item)
    if errors:
        raise ValueError("\n".join(errors))
    return annotations


def validate_paths(paths: list[Path]) -> ValidationSummary:
    summary = ValidationSummary(files=len(paths))
    by_clip: dict[str, list[GtAnnotation]] = defaultdict(list)
    seen: set[tuple[str, int]] = set()

    for file_path in paths:
        try:
            items = load_annotations([file_path])
        except Exception as exc:
            summary.invalid_count += 1
            summary.errors.append(str(exc))
            continue
        for item in items:
            key = (item.source, item.frame_index)
            if key in seen:
                summary.duplicate_count += 1
                summary.errors.append(f"{file_path}: duplicate source+frame_index {item.source}:{item.frame_index}")
            seen.add(key)
            by_clip[item.source].append(item)

    for source, rows in by_clip.items():
        resolved = resolve_source(source)
        if resolved is None:
            summary.invalid_count += len(rows)
            summary.errors.append(f"source not found: {source}")
            continue
        frame_count, width, height = _video_meta(resolved)
        if frame_count <= 0 or width <= 0 or height <= 0:
            summary.warnings.append(f"video metadata unavailable: {source}")

        visible = [row for row in rows if row.visible]
        invisible = [row for row in rows if not row.visible]
        bad_bbox = 0
        for row in visible:
            if row.bbox is None:
                bad_bbox += 1
                continue
            x1, y1, x2, y2 = row.bbox
            if width > 0 and height > 0 and not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                bad_bbox += 1
                summary.errors.append(f"bbox outside frame: {source}:{row.frame_index} {row.bbox} frame={width}x{height}")
        bad_frame = 0
        if frame_count > 0:
            for row in rows:
                if row.frame_index >= frame_count:
                    bad_frame += 1
                    summary.errors.append(f"frame_index outside video: {source}:{row.frame_index} frames={frame_count}")

        summary.invalid_count += bad_bbox + bad_frame
        summary.rows += len(rows)
        summary.visible_rows += len(visible)
        summary.invisible_rows += len(invisible)
        frames = [row.frame_index for row in rows]
        summary.clips_detail[source] = {
            "resolved": str(resolved),
            "rows": len(rows),
            "visible_rows": len(visible),
            "invisible_rows": len(invisible),
            "min_frame": min(frames) if frames else 0,
            "max_frame": max(frames) if frames else 0,
            "video_frames": frame_count,
            "frame_width": width,
            "frame_height": height,
            "coverage": round(len(rows) / frame_count, 4) if frame_count else None,
            "bad_bbox": bad_bbox,
            "bad_frame": bad_frame,
        }

    summary.clips = len(summary.clips_detail)
    return summary


def _expand_inputs(inputs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        path = item if item.is_absolute() else ROOT / item
        if path.is_dir():
            paths.extend(sorted(path.glob("*.csv")))
        else:
            paths.append(path)
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate GT Assist CSV files.")
    parser.add_argument("inputs", nargs="+", type=Path, help="CSV file(s) or directories.")
    parser.add_argument("--json-output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = _expand_inputs(args.inputs)
    summary = validate_paths(paths)
    data = asdict(summary)
    text = json.dumps(data, indent=2, ensure_ascii=False)
    print(text)
    if args.json_output:
        output = args.json_output if args.json_output.is_absolute() else ROOT / args.json_output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    return 1 if summary.errors or summary.invalid_count or summary.duplicate_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
