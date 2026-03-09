#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Stats:
    files_total: int = 0
    files_changed: int = 0
    lines_total: int = 0
    lines_kept_boxes: int = 0
    lines_converted_segments: int = 0
    lines_dropped_invalid: int = 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Normalize YOLO labels to pure detection format: <cls cx cy w h>."
    )
    p.add_argument("--dataset-root", type=Path, required=True, help="YOLO dataset root with labels/<split>.")
    p.add_argument("--fix", action="store_true", help="Write changes in place. Without this flag runs dry-run.")
    p.add_argument("--clamp", action=argparse.BooleanOptionalAction, default=True, help="Clamp coords to [0, 1].")
    return p.parse_args()


def _to_float(token: str) -> float | None:
    try:
        return float(token)
    except Exception:
        return None


def _format_box(class_id: int, cx: float, cy: float, w: float, h: float) -> str:
    return f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"


def _convert_line(line: str, clamp: bool, stats: Stats) -> str | None:
    s = line.strip()
    if not s:
        return None
    stats.lines_total += 1
    parts = s.split()
    if len(parts) < 5:
        stats.lines_dropped_invalid += 1
        return None

    cls_value = _to_float(parts[0])
    if cls_value is None:
        stats.lines_dropped_invalid += 1
        return None
    class_id = int(cls_value)

    if len(parts) == 5:
        vals = [_to_float(v) for v in parts[1:5]]
        if any(v is None for v in vals):
            stats.lines_dropped_invalid += 1
            return None
        cx, cy, w, h = vals  # type: ignore[misc]
        if clamp:
            cx = min(max(cx, 0.0), 1.0)
            cy = min(max(cy, 0.0), 1.0)
            w = min(max(w, 1e-6), 1.0)
            h = min(max(h, 1e-6), 1.0)
        if w <= 0.0 or h <= 0.0:
            stats.lines_dropped_invalid += 1
            return None
        stats.lines_kept_boxes += 1
        return _format_box(class_id, cx, cy, w, h)

    coords = [_to_float(v) for v in parts[1:]]
    if any(v is None for v in coords):
        stats.lines_dropped_invalid += 1
        return None
    if len(coords) < 4 or (len(coords) % 2) != 0:
        stats.lines_dropped_invalid += 1
        return None

    xs = coords[0::2]  # type: ignore[assignment]
    ys = coords[1::2]  # type: ignore[assignment]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    w = xmax - xmin
    h = ymax - ymin
    if w <= 0.0 or h <= 0.0:
        stats.lines_dropped_invalid += 1
        return None

    cx = xmin + w / 2.0
    cy = ymin + h / 2.0
    if clamp:
        cx = min(max(cx, 0.0), 1.0)
        cy = min(max(cy, 0.0), 1.0)
        w = min(max(w, 1e-6), 1.0)
        h = min(max(h, 1e-6), 1.0)
    stats.lines_converted_segments += 1
    return _format_box(class_id, cx, cy, w, h)


def process_file(path: Path, fix: bool, clamp: bool, stats: Stats) -> None:
    stats.files_total += 1
    try:
        original = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return

    out_lines: list[str] = []
    for line in original:
        converted = _convert_line(line, clamp=clamp, stats=stats)
        if converted:
            out_lines.append(converted)

    new_text = "\n".join(out_lines) + ("\n" if out_lines else "")
    old_text = "\n".join(original) + ("\n" if original else "")
    if new_text != old_text:
        stats.files_changed += 1
        if fix:
            path.write_text(new_text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    labels_root = args.dataset_root / "labels"
    if not labels_root.exists():
        raise FileNotFoundError(f"Labels folder not found: {labels_root}")

    stats = Stats()
    files = sorted(labels_root.rglob("*.txt"))
    for p in files:
        process_file(p, fix=bool(args.fix), clamp=bool(args.clamp), stats=stats)

    mode = "FIX" if args.fix else "DRY_RUN"
    print(f"[{mode}] dataset={args.dataset_root}")
    print(f"[{mode}] files_total={stats.files_total}")
    print(f"[{mode}] files_changed={stats.files_changed}")
    print(f"[{mode}] lines_total={stats.lines_total}")
    print(f"[{mode}] lines_kept_boxes={stats.lines_kept_boxes}")
    print(f"[{mode}] lines_converted_segments={stats.lines_converted_segments}")
    print(f"[{mode}] lines_dropped_invalid={stats.lines_dropped_invalid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
