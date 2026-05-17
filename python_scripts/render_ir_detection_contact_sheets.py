#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_tracker.pipeline import VideoSession
from uav_tracker.profile_io import load_preset
from uav_tracker.runtime import create_detector_backend


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render IR raw-detection contact sheets.")
    p.add_argument("--preset", default="antiuav_thermal")
    p.add_argument("--sources", nargs="+", required=True)
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/diagnostics/ir_detection_sheets"))
    p.add_argument("--confs", default="0.12,0.08,0.05")
    p.add_argument("--frames", default="0,40,80,120,160,200,240,280")
    return p.parse_args()


def _source_name(source: str) -> str:
    return Path(source).stem.replace(" ", "_")


def _draw_box(draw: ImageDraw.ImageDraw, bbox, color: tuple[int, int, int], label: str) -> None:
    x1, y1, x2, y2 = [int(v) for v in bbox]
    for inset in range(2):
        draw.rectangle((x1 - inset, y1 - inset, x2 + inset, y2 + inset), outline=color)
    draw.rectangle((x1, max(0, y1 - 14), x1 + max(54, len(label) * 7), y1), fill=(0, 0, 0))
    draw.text((x1 + 2, max(0, y1 - 13)), label, fill=color)


def render_source(source: str, preset: str, confs: list[float], frame_indices: list[int], out_dir: Path) -> list[Path]:
    cfg, _ = load_preset(preset)
    backend = create_detector_backend(cfg.MODEL_PATH, cfg.DEVICE)
    session = VideoSession(cfg, source, manage_cv_windows=False)
    session.open()

    wanted = set(frame_indices)
    frames = {}
    try:
        while True:
            ok, frame, meta = session.read()
            if not ok:
                break
            idx = int(meta.get("frame_index", len(frames)))
            if idx in wanted:
                frames[idx] = frame.copy()
            if len(frames) >= len(wanted):
                break
    finally:
        session.close()

    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for conf in confs:
        tiles = []
        for idx in frame_indices:
            frame = frames.get(idx)
            if frame is None:
                continue
            dets = backend.predict_frame(frame, cfg, conf=conf, imgsz=cfg.IMG_SIZE)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img.thumbnail((320, 220))
            sx = img.width / frame.shape[1]
            sy = img.height / frame.shape[0]
            canvas = Image.new("RGB", (340, 260), (14, 16, 20))
            canvas.paste(img, ((340 - img.width) // 2, 8))
            draw = ImageDraw.Draw(canvas)
            ox = (340 - img.width) // 2
            oy = 8
            for det in dets:
                x1, y1, x2, y2 = det.bbox
                scaled = (ox + x1 * sx, oy + y1 * sy, ox + x2 * sx, oy + y2 * sy)
                _draw_box(draw, scaled, (255, 74, 74), f"{det.conf:.2f}")
            draw.text((8, 232), f"frame {idx} | conf {conf:.2f} | dets {len(dets)}", fill=(235, 238, 242))
            tiles.append(canvas)

        if not tiles:
            continue
        cols = 4
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 340, rows * 260), (8, 10, 14))
        for i, tile in enumerate(tiles):
            sheet.paste(tile, ((i % cols) * 340, (i // cols) * 260))
        out_path = out_dir / f"{_source_name(source)}_conf_{conf:.2f}.jpg"
        sheet.save(out_path, quality=92)
        written.append(out_path)
    return written


def main() -> int:
    args = parse_args()
    confs = [float(item.strip()) for item in args.confs.split(",") if item.strip()]
    frame_indices = [int(item.strip()) for item in args.frames.split(",") if item.strip()]
    for source in args.sources:
        for path in render_source(source, args.preset, confs, frame_indices, args.out_dir):
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
