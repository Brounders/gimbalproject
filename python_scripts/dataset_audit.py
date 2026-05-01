#!/usr/bin/env python3
"""
DG-001 — Dataset composition auditor.

Reads dataset_contract.yaml, scans a YOLO dataset directory, and reports
whether the dataset meets composition requirements before training starts.

Content-based checks (from label files):
  - Total image count
  - drone:bird label ratio  (class 0 vs class 1 bbox counts)
  - bird_negatives_min_pct  (% of all bboxes that are class 1)

Heuristic scene-split (folder name patterns — explicitly flagged as heuristic):
  - night_visible_light_min_pct
  - ir_min_pct
  - day_max_pct

Usage:
    python python_scripts/dataset_audit.py datasets/my_dataset/
    python python_scripts/dataset_audit.py datasets/my_dataset/ --split train
    python python_scripts/dataset_audit.py datasets/my_dataset/ --contract configs/dataset_contract.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[error] PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DEFAULT = ROOT / "configs" / "dataset_contract.yaml"

# ── scene heuristics ──────────────────────────────────────────────────────────

_NIGHT_KEYWORDS  = {"night", "nite", "dark", "lowlight", "low_light"}
_IR_KEYWORDS     = {"ir", "thermal", "antiuav", "anti_uav", "infrared", "rgbt"}


def _detect_scene(path: Path) -> str:
    """Heuristic: classify image path as 'night', 'ir', or 'day' by folder tokens."""
    # Split every path component by _ and - to get individual tokens
    tokens: set[str] = set()
    for part in path.parts:
        for tok in part.lower().replace("-", "_").split("_"):
            tokens.add(tok)
    if tokens & _IR_KEYWORDS:
        return "ir"
    if tokens & _NIGHT_KEYWORDS:
        return "night"
    return "day"


# ── label scanning ────────────────────────────────────────────────────────────

def _scan_labels(label_dir: Path, drone_id: int, bird_id: int
                 ) -> tuple[int, int, int]:
    """
    Returns (drone_boxes, bird_boxes, images_with_labels).
    Images with empty label files count as images (background negatives).
    """
    drone_boxes = 0
    bird_boxes = 0
    images_with_labels = 0

    for lf in label_dir.rglob("*.txt"):
        images_with_labels += 1
        for line in lf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                cls = int(line.split()[0])
            except (ValueError, IndexError):
                continue
            if cls == drone_id:
                drone_boxes += 1
            elif cls == bird_id:
                bird_boxes += 1

    return drone_boxes, bird_boxes, images_with_labels


def _scan_images(image_dir: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    return [p for p in image_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts]


# ── contract loading ──────────────────────────────────────────────────────────

def _load_contract(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _extract_thresholds(contract: dict) -> dict:
    c = contract.get("composition", {})
    cls = contract.get("classes", {})
    return {
        "min_total_images":          int(c.get("min_total_images", 5000)),
        "night_visible_light_min_pct": float(c.get("night_visible_light_min_pct", 20)),
        "ir_min_pct":                float(c.get("ir_min_pct", 15)),
        "day_max_pct":               float(c.get("day_max_pct", 65)),
        "drone_bird_ratio_max":      float(c.get("drone_bird_ratio_max", 10)),
        "bird_negatives_min_pct":    float(c.get("bird_negatives_min_pct", 5)),
        "drone_class_id":            int(cls.get("drone_class_id", 0)),
        "bird_class_id":             int(cls.get("bird_class_id", 1)),
    }


# ── audit logic ───────────────────────────────────────────────────────────────

def audit(dataset_dir: Path, split: str, contract_path: Path) -> dict:
    """
    Run full audit. Returns dict with keys:
      passed, failures, stats, thresholds
    """
    contract = _load_contract(contract_path)
    t = _extract_thresholds(contract)

    # Locate image and label directories
    img_dir   = dataset_dir / "images" / split
    label_dir = dataset_dir / "labels" / split

    if not img_dir.exists():
        # Fallback: flat dataset with no split subfolder
        img_dir   = dataset_dir / "images"
        label_dir = dataset_dir / "labels"

    failures: list[str] = []
    stats: dict = {}

    # ── image count ──
    images = _scan_images(img_dir) if img_dir.exists() else []
    total_images = len(images)
    stats["total_images"] = total_images

    if total_images < t["min_total_images"]:
        failures.append(
            f"total_images={total_images} < min={t['min_total_images']}"
        )

    # ── scene split (heuristic) ──
    scene_counts: dict[str, int] = {"night": 0, "ir": 0, "day": 0}
    for img in images:
        scene_counts[_detect_scene(img)] += 1

    n = max(1, total_images)
    night_pct = 100.0 * scene_counts["night"] / n
    ir_pct    = 100.0 * scene_counts["ir"]    / n
    day_pct   = 100.0 * scene_counts["day"]   / n

    stats["scene_heuristic"] = {
        "night_pct": round(night_pct, 1),
        "ir_pct":    round(ir_pct, 1),
        "day_pct":   round(day_pct, 1),
        "note": "heuristic — folder-name based, not content analysis",
    }

    if night_pct < t["night_visible_light_min_pct"]:
        failures.append(
            f"night_pct={night_pct:.1f}% < min={t['night_visible_light_min_pct']}% [heuristic]"
        )
    if ir_pct < t["ir_min_pct"]:
        failures.append(
            f"ir_pct={ir_pct:.1f}% < min={t['ir_min_pct']}% [heuristic]"
        )
    if day_pct > t["day_max_pct"]:
        failures.append(
            f"day_pct={day_pct:.1f}% > max={t['day_max_pct']}% [heuristic]"
        )

    # ── label / class balance (content-based) ──
    if label_dir.exists():
        drone_boxes, bird_boxes, labeled_images = _scan_labels(
            label_dir, t["drone_class_id"], t["bird_class_id"]
        )
    else:
        drone_boxes = bird_boxes = labeled_images = 0

    total_boxes = drone_boxes + bird_boxes
    bird_pct    = 100.0 * bird_boxes  / max(1, total_boxes)
    ratio       = drone_boxes / max(1, bird_boxes)

    stats["labels"] = {
        "labeled_images":    labeled_images,
        "drone_boxes":       drone_boxes,
        "bird_boxes":        bird_boxes,
        "total_boxes":       total_boxes,
        "bird_pct_of_boxes": round(bird_pct, 2),
        "drone_bird_ratio":  round(ratio, 1),
        "note": "content-based — read from .txt label files",
    }

    if bird_pct < t["bird_negatives_min_pct"]:
        failures.append(
            f"bird_negatives={bird_pct:.1f}% < min={t['bird_negatives_min_pct']}%"
        )
    if ratio > t["drone_bird_ratio_max"]:
        failures.append(
            f"drone:bird ratio={ratio:.1f} > max={t['drone_bird_ratio_max']}:1"
        )

    return {
        "passed":     len(failures) == 0,
        "failures":   failures,
        "stats":      stats,
        "thresholds": t,
        "split":      split,
        "dataset":    str(dataset_dir),
        "contract":   str(contract_path),
    }


# ── reporting ────────────────────────────────────────────────────────────────

def _print_report(result: dict) -> None:
    verdict = "PASS" if result["passed"] else "FAIL"
    s = result["stats"]
    t = result["thresholds"]
    sc = s.get("scene_heuristic", {})
    lb = s.get("labels", {})

    print(f"\n{'='*58}")
    print(f"  DATASET AUDIT: {verdict}")
    print(f"{'='*58}")
    print(f"  Dataset : {result['dataset']}")
    print(f"  Split   : {result['split']}")
    print(f"  Contract: {result['contract']}")
    print()
    print(f"  ── Images ──")
    print(f"  Total images : {s['total_images']}  (min: {t['min_total_images']})")
    print()
    print(f"  ── Scene split [heuristic — folder names] ──")
    print(f"  Night : {sc.get('night_pct', '?')}%  (min: {t['night_visible_light_min_pct']}%)")
    print(f"  IR    : {sc.get('ir_pct', '?')}%  (min: {t['ir_min_pct']}%)")
    print(f"  Day   : {sc.get('day_pct', '?')}%  (max: {t['day_max_pct']}%)")
    print()
    print(f"  ── Class balance [content-based — label files] ──")
    print(f"  Drone boxes      : {lb.get('drone_boxes', '?')}")
    print(f"  Bird boxes       : {lb.get('bird_boxes', '?')}")
    print(f"  Bird % of bboxes : {lb.get('bird_pct_of_boxes', '?')}%  (min: {t['bird_negatives_min_pct']}%)")
    print(f"  Drone:bird ratio : {lb.get('drone_bird_ratio', '?')}:1  (max: {t['drone_bird_ratio_max']}:1)")
    print()

    if result["failures"]:
        print(f"  ── Failures ──")
        for f in result["failures"]:
            print(f"  ✗ {f}")
    else:
        print(f"  ✓ All checks passed")
    print(f"{'='*58}\n")


# ── main ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="DG-001 Dataset composition auditor.")
    p.add_argument("dataset", type=Path, help="YOLO dataset root (contains images/ and labels/)")
    p.add_argument("--split", default="train", help="Dataset split to audit (default: train)")
    p.add_argument("--contract", type=Path, default=CONTRACT_DEFAULT,
                   help="Path to dataset_contract.yaml")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if not args.dataset.exists():
        print(f"[error] Dataset directory not found: {args.dataset}")
        return 1
    if not args.contract.exists():
        print(f"[error] Contract not found: {args.contract}")
        return 1

    result = audit(args.dataset, args.split, args.contract)
    _print_report(result)
    return 0 if result["passed"] else 4


if __name__ == "__main__":
    sys.exit(main())
