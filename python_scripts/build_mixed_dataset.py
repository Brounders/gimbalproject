#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build mixed YOLO dataset lists from multiple dataset roots.")
    p.add_argument("--primary-root", type=Path, required=True, help="Primary YOLO dataset root (drone+bird).")
    p.add_argument("--night-root", type=Path, required=True, help="Night YOLO dataset root (uav).")
    p.add_argument("--out-root", type=Path, required=True, help="Output dataset folder with train/val/test txt + yaml.")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--shuffle", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument(
        "--night-multiplier",
        type=float,
        default=2.0,
        help="Duplicate night samples in train list to increase night prior (>=1.0).",
    )
    return p.parse_args()


def _collect_images(root: Path, split: str) -> list[Path]:
    img_dir = root / "images" / split
    if not img_dir.exists():
        return []
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    files = [p for p in img_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts]
    return sorted(files)


def _write_list(path: Path, items: list[Path]) -> None:
    lines = [str(p.resolve()) for p in items]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _combine_split(
    primary_root: Path,
    night_root: Path,
    split: str,
    rng: random.Random,
    shuffle: bool,
    night_multiplier: float,
) -> list[Path]:
    primary = _collect_images(primary_root, split)
    night = _collect_images(night_root, split)
    merged = list(primary)

    if split == "train" and night and night_multiplier > 1.0:
        dup_count = int((night_multiplier - 1.0) * len(night))
        merged.extend(night)
        if dup_count > 0:
            merged.extend(night[:dup_count])
    else:
        merged.extend(night)

    if shuffle:
        rng.shuffle(merged)
    return merged


def main() -> int:
    args = parse_args()
    if not args.primary_root.exists():
        raise FileNotFoundError(f"Primary root not found: {args.primary_root}")
    if not args.night_root.exists():
        raise FileNotFoundError(f"Night root not found: {args.night_root}")

    args.out_root.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    splits = ["train", "val", "test"]
    counts: dict[str, int] = {}
    for split in splits:
        items = _combine_split(
            primary_root=args.primary_root,
            night_root=args.night_root,
            split=split,
            rng=rng,
            shuffle=args.shuffle,
            night_multiplier=max(1.0, float(args.night_multiplier)),
        )
        out_txt = args.out_root / f"{split}.txt"
        _write_list(out_txt, items)
        counts[split] = len(items)
        print(f"[info] {split}: {counts[split]} images -> {out_txt}")

    yaml_path = args.out_root / "dataset.yaml"
    lines = [
        f"path: {args.out_root.resolve()}",
        "train: train.txt",
        "val: val.txt",
    ]
    if counts.get("test", 0) > 0:
        lines.append("test: test.txt")
    lines.extend(
        [
            "nc: 2",
            "names:",
            "  0: drone",
            "  1: bird",
            "",
        ]
    )
    yaml_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[info] dataset yaml: {yaml_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
