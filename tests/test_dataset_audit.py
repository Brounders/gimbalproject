"""Tests for dataset_audit.py — audit logic, scene heuristics, contract parsing."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

_AUDIT_PATH = Path(__file__).resolve().parents[1] / "python_scripts" / "dataset_audit.py"
_spec = importlib.util.spec_from_file_location("dataset_audit", _AUDIT_PATH)
_mod = importlib.util.module_from_spec(_spec)   # type: ignore[arg-type]
_spec.loader.exec_module(_mod)                  # type: ignore[union-attr]

audit          = _mod.audit
_detect_scene  = _mod._detect_scene
_scan_labels   = _mod._scan_labels
_extract_thresholds = _mod._extract_thresholds

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "configs" / "dataset_contract.yaml"

# ── helpers ───────────────────────────────────────────────────────────────────

def _make_dataset(tmp: Path, images: dict[str, int], labels: dict[str, list[int]]) -> Path:
    """
    images  = {"night": N, "ir": N, "day": N}
    labels  = {"night": [cls, cls, ...], "ir": [...], "day": [...]}
    Creates a minimal YOLO dataset under tmp/.
    """
    for scene, count in images.items():
        img_dir   = tmp / "images" / "train" / scene
        label_dir = tmp / "labels" / "train" / scene
        img_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            # fake image file
            (img_dir / f"img_{i:04d}.jpg").write_bytes(b"\xff")
            # label file: one bbox per class entry
            cls_list = labels.get(scene, [])
            line = f"{cls_list[i % len(cls_list)]} 0.5 0.5 0.1 0.1\n" if cls_list else ""
            (label_dir / f"img_{i:04d}.txt").write_text(line, encoding="utf-8")
    return tmp


# ── scene heuristic tests ─────────────────────────────────────────────────────

class TestDetectScene(unittest.TestCase):

    def test_night_keyword(self):
        self.assertEqual(_detect_scene(Path("datasets/night_clips/img.jpg")), "night")

    def test_ir_keyword(self):
        self.assertEqual(_detect_scene(Path("datasets/ir_data/img.jpg")), "ir")

    def test_thermal_keyword(self):
        self.assertEqual(_detect_scene(Path("datasets/thermal/img.jpg")), "ir")

    def test_antiuav_keyword(self):
        self.assertEqual(_detect_scene(Path("datasets/antiuav_rgbt/img.jpg")), "ir")

    def test_day_fallback(self):
        self.assertEqual(_detect_scene(Path("datasets/outdoor/img.jpg")), "day")

    def test_ir_beats_night(self):
        # IR takes priority over night keyword
        self.assertEqual(_detect_scene(Path("datasets/ir_night/img.jpg")), "ir")


# ── label scanning tests ──────────────────────────────────────────────────────

class TestScanLabels(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.label_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_label(self, name: str, lines: list[str]) -> None:
        (self.label_dir / name).write_text("\n".join(lines), encoding="utf-8")

    def test_counts_drone_and_bird(self):
        self._write_label("a.txt", ["0 0.5 0.5 0.1 0.1", "1 0.5 0.5 0.1 0.1"])
        self._write_label("b.txt", ["0 0.5 0.5 0.1 0.1"])
        d, b, imgs = _scan_labels(self.label_dir, drone_id=0, bird_id=1)
        self.assertEqual(d, 2)
        self.assertEqual(b, 1)
        self.assertEqual(imgs, 2)

    def test_empty_label_file_counts_as_image(self):
        self._write_label("bg.txt", [])
        d, b, imgs = _scan_labels(self.label_dir, drone_id=0, bird_id=1)
        self.assertEqual(d, 0)
        self.assertEqual(b, 0)
        self.assertEqual(imgs, 1)

    def test_ignores_unknown_class(self):
        self._write_label("x.txt", ["99 0.5 0.5 0.1 0.1"])
        d, b, imgs = _scan_labels(self.label_dir, drone_id=0, bird_id=1)
        self.assertEqual(d, 0)
        self.assertEqual(b, 0)


# ── contract threshold extraction ─────────────────────────────────────────────

class TestExtractThresholds(unittest.TestCase):

    _CONTRACT = {
        "classes": {"drone_class_id": 0, "bird_class_id": 1},
        "composition": {
            "min_total_images": 5000,
            "night_visible_light_min_pct": 20,
            "ir_min_pct": 15,
            "day_max_pct": 65,
            "drone_bird_ratio_max": 10,
            "bird_negatives_min_pct": 5,
        },
    }

    def test_all_fields_present(self):
        t = _extract_thresholds(self._CONTRACT)
        self.assertEqual(t["min_total_images"], 5000)
        self.assertEqual(t["night_visible_light_min_pct"], 20.0)
        self.assertEqual(t["ir_min_pct"], 15.0)
        self.assertEqual(t["day_max_pct"], 65.0)
        self.assertEqual(t["drone_bird_ratio_max"], 10.0)
        self.assertEqual(t["bird_negatives_min_pct"], 5.0)
        self.assertEqual(t["drone_class_id"], 0)
        self.assertEqual(t["bird_class_id"], 1)


# ── integration audit tests ───────────────────────────────────────────────────

class TestAudit(unittest.TestCase):

    def _run(self, images: dict, labels: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            ds = _make_dataset(Path(tmp), images, labels)
            return audit(ds, split="train", contract_path=CONTRACT_PATH)

    def test_pass_balanced(self):
        # 5500 images: 1500 night, 1000 ir, 3000 day → night=27%, ir=18%, day=55%
        # labels: 500 drone + 500 bird per scene type (ratio 1:1)
        result = self._run(
            images={"night": 1500, "ir": 1000, "day": 3000},
            labels={"night": [0, 1], "ir": [0, 1], "day": [0, 1]},
        )
        self.assertTrue(result["passed"], result["failures"])

    def test_fail_too_few_images(self):
        result = self._run(
            images={"night": 500, "ir": 200, "day": 300},
            labels={"night": [0, 1], "ir": [0, 1], "day": [0, 1]},
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("total_images" in f for f in result["failures"]))

    def test_fail_no_bird_negatives(self):
        # All labels are drone (class 0)
        result = self._run(
            images={"night": 1500, "ir": 1000, "day": 3000},
            labels={"night": [0], "ir": [0], "day": [0]},
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("bird_negatives" in f for f in result["failures"]))

    def test_fail_drone_bird_ratio(self):
        # 11 drone bboxes per 1 bird → ratio > 10
        result = self._run(
            images={"night": 1500, "ir": 1000, "day": 3000},
            labels={"night": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                    "ir":    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                    "day":   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]},
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("drone:bird ratio" in f for f in result["failures"]))

    def test_fail_night_pct_too_low(self):
        # Only day images → night_pct ≈ 0%
        result = self._run(
            images={"day": 5500},
            labels={"day": [0, 1]},
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("night_pct" in f for f in result["failures"]))


if __name__ == "__main__":
    unittest.main()
