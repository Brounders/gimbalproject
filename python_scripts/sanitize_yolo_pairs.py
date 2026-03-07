#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Remove orphan images/labels in YOLO dataset.")
    p.add_argument("--dataset-root", type=Path, required=True, help="YOLO root with images/ and labels/.")
    p.add_argument(
        "--fix",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Delete orphan files. If false, report only.",
    )
    return p.parse_args()


def _collect(root: Path, exts: set[str]) -> dict[tuple[str, str], Path]:
    out: dict[tuple[str, str], Path] = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in exts:
            continue
        rel = p.relative_to(root)
        split = rel.parts[0] if rel.parts else ""
        key = (split, p.stem)
        out[key] = p
    return out


def main() -> int:
    args = parse_args()
    root = args.dataset_root
    img_root = root / "images"
    lbl_root = root / "labels"
    if not img_root.exists() or not lbl_root.exists():
        raise FileNotFoundError(f"Expected images/ and labels/ under {root}")

    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = _collect(img_root, image_exts)
    labels = _collect(lbl_root, {".txt"})

    img_keys = set(images.keys())
    lbl_keys = set(labels.keys())
    orphan_images = sorted(img_keys - lbl_keys)
    orphan_labels = sorted(lbl_keys - img_keys)

    print(f"[info] images={len(images)} labels={len(labels)}")
    print(f"[info] orphan_images={len(orphan_images)} orphan_labels={len(orphan_labels)}")

    if args.fix:
        deleted = 0
        for key in orphan_images:
            try:
                images[key].unlink(missing_ok=True)
                deleted += 1
            except Exception:
                pass
        for key in orphan_labels:
            try:
                labels[key].unlink(missing_ok=True)
                deleted += 1
            except Exception:
                pass
        print(f"[info] deleted={deleted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
