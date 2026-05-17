#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import cv2
from PIL import Image, ImageDraw


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render YOLO pack contact sheets from manifest.json.")
    p.add_argument("--pack-dir", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--max-per-group", type=int, default=48)
    p.add_argument("--tile-width", type=int, default=280)
    p.add_argument("--tile-height", type=int, default=220)
    p.add_argument("--cols", type=int, default=4)
    return p.parse_args()


def _read_label(path: Path, frame_w: int, frame_h: int) -> list[tuple[int, tuple[int, int, int, int]]]:
    boxes: list[tuple[int, tuple[int, int, int, int]]] = []
    if not path.exists():
        return boxes
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        class_id = int(float(parts[0]))
        cx, cy, w, h = [float(value) for value in parts[1:]]
        x1 = int((cx - w / 2.0) * frame_w)
        y1 = int((cy - h / 2.0) * frame_h)
        x2 = int((cx + w / 2.0) * frame_w)
        y2 = int((cy + h / 2.0) * frame_h)
        boxes.append((class_id, (x1, y1, x2, y2)))
    return boxes


def _draw_box(draw: ImageDraw.ImageDraw, bbox: tuple[int, int, int, int], color: tuple[int, int, int], label: str) -> None:
    x1, y1, x2, y2 = bbox
    for inset in range(2):
        draw.rectangle((x1 - inset, y1 - inset, x2 + inset, y2 + inset), outline=color)
    text_w = max(46, len(label) * 7)
    draw.rectangle((x1, max(0, y1 - 15), x1 + text_w, y1), fill=(0, 0, 0))
    draw.text((x1 + 2, max(0, y1 - 14)), label, fill=color)


def _tile(record: dict[str, Any], tile_w: int, tile_h: int) -> Image.Image | None:
    image_path = Path(record.get("image_path", ""))
    label_path = Path(record.get("label_path", ""))
    frame = cv2.imread(str(image_path))
    if frame is None:
        return None
    frame_h, frame_w = frame.shape[:2]
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img.thumbnail((tile_w, tile_h - 34))
    sx = img.width / frame_w
    sy = img.height / frame_h
    canvas = Image.new("RGB", (tile_w, tile_h), (12, 14, 18))
    ox = (tile_w - img.width) // 2
    oy = 6
    canvas.paste(img, (ox, oy))
    draw = ImageDraw.Draw(canvas)
    for class_id, (x1, y1, x2, y2) in _read_label(label_path, frame_w, frame_h):
        color = (60, 220, 120) if class_id == 0 else (255, 190, 60)
        scaled = (int(ox + x1 * sx), int(oy + y1 * sy), int(ox + x2 * sx), int(oy + y2 * sy))
        _draw_box(draw, scaled, color, f"c{class_id}")
    caption = f"{record.get('split', '')} f{record.get('frame_index', '')} {record.get('sample_kind', '')}"
    draw.text((8, tile_h - 25), caption[:48], fill=(235, 238, 242))
    return canvas


def render(pack_dir: Path, out_dir: Path, max_per_group: int, tile_w: int, tile_h: int, cols: int) -> list[Path]:
    manifest_path = pack_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in manifest.get("records", []):
        if record.get("status") != "ok":
            continue
        group = str(record.get("group") or record.get("sample_kind") or "unknown")
        if len(groups[group]) < max_per_group:
            groups[group].append(record)

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for group, records in sorted(groups.items()):
        tiles = [tile for record in records if (tile := _tile(record, tile_w, tile_h)) is not None]
        if not tiles:
            continue
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tile_w, rows * tile_h), (8, 10, 14))
        for i, tile in enumerate(tiles):
            sheet.paste(tile, ((i % cols) * tile_w, (i // cols) * tile_h))
        out_path = out_dir / f"{group}.jpg"
        sheet.save(out_path, quality=92)
        written.append(out_path)
    index = ["# YOLO Pack Contact Sheets", "", f"Pack: `{pack_dir}`", ""]
    for path in written:
        index.append(f"- `{path}`")
    (out_dir / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return written


def main() -> int:
    args = parse_args()
    for path in render(args.pack_dir, args.out_dir, max(1, args.max_per_group), args.tile_width, args.tile_height, max(1, args.cols)):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
