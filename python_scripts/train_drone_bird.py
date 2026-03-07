#!/usr/bin/env python3
"""
Fine-tuning YOLO11n on Drone-vs-Bird dataset.

This script supports multiple dataset layouts and can auto-fix bad splits where
one class is missing in train/val by performing a stratified re-split.
"""

from __future__ import annotations

import argparse
import random
import shutil
from collections import Counter
from pathlib import Path
from typing import Iterable

import yaml
from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLO11n on drone/bird dataset")
    parser.add_argument("--dataset-root", type=Path, required=True, help="Raw dataset root")
    parser.add_argument("--workdir", type=Path, default=Path("datasets/drone_bird_yolo"), help="Prepared YOLO dataset dir")
    parser.add_argument("--model", type=Path, default=Path("models/yolo11n.pt"), help="Base model path")
    parser.add_argument("--project", type=Path, default=Path("runs"), help="Ultralytics runs directory")
    parser.add_argument("--name", type=str, default="drone_bird_v2", help="Run name")

    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--time-hours", type=float, default=0.0, help="Train time budget in hours (0 disables time budget)")
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", type=str, default="mps", help="mps/cpu/0")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fraction", type=float, default=1.0, help="Use only a fraction of the dataset for faster experiments")
    parser.add_argument("--freeze", type=int, default=0, help="Freeze first N layers")
    parser.add_argument("--save-period", type=int, default=-1, help="Checkpoint period in epochs; -1 disables periodic saves")
    parser.add_argument(
        "--cache",
        choices=["none", "disk", "ram"],
        default="none",
        help="Dataset cache mode",
    )
    parser.add_argument(
        "--train-val",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run validation during training",
    )

    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--force-resplit", action="store_true", help="Always rebuild split from all data")
    parser.add_argument(
        "--auto-resplit-missing-classes",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Auto re-split if any class is missing in train/val",
    )

    parser.add_argument("--lr0", type=float, default=0.003)
    parser.add_argument("--lrf", type=float, default=0.01)
    parser.add_argument("--patience", type=int, default=25)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--prepare-only", action="store_true", help="Only prepare dataset + write dataset.yaml")
    parser.add_argument("--no-validate", action="store_true", help="Skip final model.val()")
    parser.add_argument("--eval-test", action=argparse.BooleanOptionalAction, default=True, help="Run model.val on test split if exists")
    return parser.parse_args()


def normalize_ratios(args: argparse.Namespace) -> tuple[float, float, float]:
    ratios = [args.train_ratio, args.val_ratio, args.test_ratio]
    if any(r < 0 for r in ratios):
        raise ValueError("Split ratios must be >= 0")
    s = sum(ratios)
    if s <= 0:
        raise ValueError("At least one split ratio must be > 0")
    return tuple(r / s for r in ratios)


def find_image_files(root: Path) -> list[Path]:
    exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.JPG", "*.JPEG", "*.PNG")
    files: list[Path] = []
    for ext in exts:
        files.extend(root.rglob(ext))
    return sorted(files)


def parse_label_classes(label_path: Path) -> list[int]:
    classes: list[int] = []
    for line in label_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        token = line.split()[0]
        try:
            classes.append(int(float(token)))
        except ValueError:
            continue
    return classes


def detect_split_layout(dataset_root: Path) -> tuple[str, str] | None:
    # Layout A: dataset_root/images/train + dataset_root/labels/train
    val_a = "val" if (dataset_root / "images" / "val").exists() else "valid"
    if (
        (dataset_root / "images" / "train").exists()
        and (dataset_root / "labels" / "train").exists()
        and (dataset_root / "images" / val_a).exists()
        and (dataset_root / "labels" / val_a).exists()
    ):
        return ("A", val_a)

    # Layout B: dataset_root/train/images + dataset_root/train/labels
    val_b = "val" if (dataset_root / "val").exists() else "valid"
    if (
        (dataset_root / "train" / "images").exists()
        and (dataset_root / "train" / "labels").exists()
        and (dataset_root / val_b / "images").exists()
        and (dataset_root / val_b / "labels").exists()
    ):
        return ("B", val_b)

    return None


def has_yolo_split(dataset_root: Path) -> bool:
    return detect_split_layout(dataset_root) is not None


def iter_pairs_flat(images_root: Path, labels_root: Path) -> Iterable[tuple[Path, Path]]:
    for img in find_image_files(images_root):
        rel = img.relative_to(images_root)
        label = labels_root / rel.with_suffix(".txt")
        if label.exists():
            yield img, label


def collect_pairs_from_split_layout(dataset_root: Path) -> tuple[dict[str, list[tuple[Path, Path]]], list[tuple[Path, Path]]]:
    layout = detect_split_layout(dataset_root)
    if layout is None:
        raise RuntimeError("Split dataset detection failed unexpectedly.")

    layout_kind, src_val_dir = layout
    split_map = {"train": "train", "val": src_val_dir}

    has_test = (
        (dataset_root / "images" / "test").exists() and (dataset_root / "labels" / "test").exists()
        if layout_kind == "A"
        else (dataset_root / "test" / "images").exists() and (dataset_root / "test" / "labels").exists()
    )
    if has_test:
        split_map["test"] = "test"

    by_split: dict[str, list[tuple[Path, Path]]] = {}
    all_pairs: list[tuple[Path, Path]] = []

    for out_split, src_split in split_map.items():
        if layout_kind == "A":
            src_i = dataset_root / "images" / src_split
            src_l = dataset_root / "labels" / src_split
        else:
            src_i = dataset_root / src_split / "images"
            src_l = dataset_root / src_split / "labels"

        pairs = list(iter_pairs_flat(src_i, src_l))
        by_split[out_split] = pairs
        all_pairs.extend(pairs)

    return by_split, all_pairs


def summarize_pairs(pairs: list[tuple[Path, Path]]) -> dict:
    box_counts: Counter[int] = Counter()
    image_counts: Counter[int] = Counter()
    empty = 0

    for _, label in pairs:
        classes = parse_label_classes(label)
        if not classes:
            empty += 1
            continue
        uniq = set(classes)
        for c in classes:
            box_counts[c] += 1
        for c in uniq:
            image_counts[c] += 1

    return {
        "files": len(pairs),
        "empty": empty,
        "box_counts": dict(sorted(box_counts.items())),
        "image_counts": dict(sorted(image_counts.items())),
    }


def print_split_stats(stats_by_split: dict[str, dict], title: str) -> None:
    print(f"[INFO] {title}")
    for split, st in stats_by_split.items():
        print(
            f"  {split}: files={st['files']} empty={st['empty']} "
            f"boxes={st['box_counts']} imgs={st['image_counts']}"
        )


def split_group(
    items: list[tuple[Path, Path]],
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
) -> tuple[list[tuple[Path, Path]], list[tuple[Path, Path]], list[tuple[Path, Path]]]:
    n = len(items)
    if n == 0:
        return [], [], []

    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    n_test = n - n_train - n_val

    # Keep at least one item in requested splits when possible.
    requested = [0]
    if val_ratio > 0:
        requested.append(1)
    if test_ratio > 0:
        requested.append(2)

    counts = [n_train, n_val, n_test]

    if n <= len(requested):
        counts = [0, 0, 0]
        for i in range(n):
            counts[requested[i]] = 1
    else:
        for idx in requested:
            if counts[idx] == 0:
                donor = max(range(3), key=lambda j: counts[j])
                if counts[donor] > 1:
                    counts[donor] -= 1
                    counts[idx] += 1

    n_train, n_val, n_test = counts
    train = items[:n_train]
    val = items[n_train : n_train + n_val]
    test = items[n_train + n_val : n_train + n_val + n_test]
    return train, val, test


def stratified_resplit(
    pairs: list[tuple[Path, Path]],
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> tuple[list[tuple[Path, Path]], list[tuple[Path, Path]], list[tuple[Path, Path]]]:
    rng = random.Random(seed)

    has_bird: list[tuple[Path, Path]] = []
    no_bird: list[tuple[Path, Path]] = []

    for pair in pairs:
        _, label = pair
        classes = set(parse_label_classes(label))
        if 1 in classes:
            has_bird.append(pair)
        else:
            no_bird.append(pair)

    rng.shuffle(has_bird)
    rng.shuffle(no_bird)

    t1, v1, te1 = split_group(has_bird, train_ratio, val_ratio, test_ratio)
    t0, v0, te0 = split_group(no_bird, train_ratio, val_ratio, test_ratio)

    train = t1 + t0
    val = v1 + v0
    test = te1 + te0

    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return train, val, test


def copy_pairs_to_split(pairs: list[tuple[Path, Path]], out_root: Path, split: str) -> None:
    out_img = out_root / "images" / split
    out_lbl = out_root / "labels" / split
    out_img.mkdir(parents=True, exist_ok=True)
    out_lbl.mkdir(parents=True, exist_ok=True)

    for idx, (img, lbl) in enumerate(pairs):
        # Prefix index avoids collisions from nested source folders.
        stem = f"{idx:06d}_{img.stem}"
        dst_img = out_img / f"{stem}{img.suffix.lower()}"
        dst_lbl = out_lbl / f"{stem}.txt"
        shutil.copy2(img, dst_img)
        shutil.copy2(lbl, dst_lbl)


def recreate_output_root(out_root: Path) -> None:
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)


def prepare_dataset(args: argparse.Namespace) -> Path:
    dataset_root = args.dataset_root
    out_root = args.workdir
    train_ratio, val_ratio, test_ratio = normalize_ratios(args)

    if has_yolo_split(dataset_root):
        print("[INFO] Found pre-split YOLO dataset.")
        by_split, all_pairs = collect_pairs_from_split_layout(dataset_root)
        source_stats = {k: summarize_pairs(v) for k, v in by_split.items()}
        print_split_stats(source_stats, "Source split stats")

        do_resplit = args.force_resplit
        if args.auto_resplit_missing_classes and not do_resplit:
            missing_in_train = source_stats.get("train", {}).get("image_counts", {}).get(1, 0) == 0
            missing_in_val = source_stats.get("val", {}).get("image_counts", {}).get(1, 0) == 0
            if missing_in_train or missing_in_val:
                print("[WARN] Class 1 (bird) is missing in train/val. Enabling auto re-split.")
                do_resplit = True

        if do_resplit:
            recreate_output_root(out_root)
            train_pairs, val_pairs, test_pairs = stratified_resplit(
                all_pairs,
                train_ratio=train_ratio,
                val_ratio=val_ratio,
                test_ratio=test_ratio,
                seed=args.seed,
            )
            copy_pairs_to_split(train_pairs, out_root, "train")
            copy_pairs_to_split(val_pairs, out_root, "val")
            if test_pairs:
                copy_pairs_to_split(test_pairs, out_root, "test")
            print(
                f"[INFO] Re-split prepared: train={len(train_pairs)} "
                f"val={len(val_pairs)} test={len(test_pairs)}"
            )
        else:
            recreate_output_root(out_root)
            for split_name, pairs in by_split.items():
                copy_pairs_to_split(pairs, out_root, split_name)
            print("[INFO] Reused original split without re-splitting.")

        final_stats = {}
        for split in ["train", "val", "test"]:
            img_dir = out_root / "images" / split
            lbl_dir = out_root / "labels" / split
            if img_dir.exists() and lbl_dir.exists():
                final_stats[split] = summarize_pairs(list(iter_pairs_flat(img_dir, lbl_dir)))
        print_split_stats(final_stats, "Prepared split stats")
        return out_root

    images_root = dataset_root / "images"
    labels_root = dataset_root / "labels"
    if not images_root.exists() or not labels_root.exists():
        raise FileNotFoundError(
            f"Expected either split YOLO dataset or flat images/labels under: {dataset_root}"
        )

    pairs = list(iter_pairs_flat(images_root, labels_root))
    if not pairs:
        raise RuntimeError("No image/label pairs found. Check dataset structure.")

    recreate_output_root(out_root)
    train_pairs, val_pairs, test_pairs = stratified_resplit(
        pairs,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=args.seed,
    )
    copy_pairs_to_split(train_pairs, out_root, "train")
    copy_pairs_to_split(val_pairs, out_root, "val")
    if test_pairs:
        copy_pairs_to_split(test_pairs, out_root, "test")

    print(
        f"[INFO] Prepared dataset from flat source: train={len(train_pairs)} "
        f"val={len(val_pairs)} test={len(test_pairs)}"
    )
    return out_root


def write_dataset_yaml(dataset_dir: Path) -> Path:
    data = {
        "path": str(dataset_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "nc": 2,
        "names": {0: "drone", 1: "bird"},
    }
    if (dataset_dir / "images" / "test").exists():
        data["test"] = "images/test"

    out = dataset_dir / "dataset.yaml"
    with out.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    return out


def train(args: argparse.Namespace, data_yaml: Path) -> Path:
    model = YOLO(str(args.model))
    if args.time_hours > 0:
        print(
            f"[INFO] Training on device={args.device}, epochs={args.epochs}, "
            f"time_hours={args.time_hours}, batch={args.batch}"
        )
    else:
        print(f"[INFO] Training on device={args.device}, epochs={args.epochs}, batch={args.batch}")

    cache_value: bool | str = False
    if args.cache == "disk":
        cache_value = "disk"
    elif args.cache == "ram":
        cache_value = "ram"

    train_kwargs = dict(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=str(args.project),
        name=args.name,
        exist_ok=True,
        lr0=args.lr0,
        lrf=args.lrf,
        patience=args.patience,
        optimizer="AdamW",
        weight_decay=5e-4,
        warmup_epochs=3.0,
        close_mosaic=10,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.05,
        hsv_h=0.01,
        hsv_s=0.3,
        hsv_v=0.45,
        degrees=8.0,
        translate=0.08,
        scale=0.45,
        fliplr=0.5,
        amp=False,
        plots=True,
        save=True,
        save_period=args.save_period,
        resume=args.resume,
        cache=cache_value,
        val=args.train_val,
        fraction=args.fraction,
        freeze=args.freeze,
    )
    if args.time_hours > 0:
        train_kwargs["time"] = float(args.time_hours)
    model.train(**train_kwargs)

    save_dir = Path(model.trainer.save_dir)
    best = save_dir / "weights" / "best.pt"
    print(f"[INFO] save_dir: {save_dir}")
    return best


def validate(best_path: Path, data_yaml: Path, device: str, imgsz: int, split: str = "val") -> None:
    if not best_path.exists():
        raise FileNotFoundError(f"best.pt was not found at: {best_path}")

    model = YOLO(str(best_path))
    kwargs = {"data": str(data_yaml), "imgsz": imgsz, "device": device}
    if split != "val":
        kwargs["split"] = split

    try:
        metrics = model.val(**kwargs)
    except TypeError:
        if split != "val":
            print(f"[WARN] This ultralytics version does not support split='{split}' in model.val().")
            return
        raise

    print(f"[RESULT] {split} metrics")
    print(f"  mAP50:     {metrics.box.map50:.4f}")
    print(f"  mAP50-95:  {metrics.box.map:.4f}")
    print(f"  Precision: {metrics.box.mp:.4f}")
    print(f"  Recall:    {metrics.box.mr:.4f}")


if __name__ == "__main__":
    args = parse_args()
    dataset_dir = prepare_dataset(args)
    data_yaml = write_dataset_yaml(dataset_dir)

    if args.prepare_only:
        print(f"[INFO] Prepare-only mode done. dataset.yaml: {data_yaml}")
        raise SystemExit(0)

    best = train(args, data_yaml)
    print(f"[INFO] best.pt: {best}")

    if not args.no_validate:
        validate(best, data_yaml, device=args.device, imgsz=args.imgsz, split="val")
        has_test = (dataset_dir / "images" / "test").exists()
        if has_test and args.eval_test:
            validate(best, data_yaml, device=args.device, imgsz=args.imgsz, split="test")
