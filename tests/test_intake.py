"""Tests for run_intake.py — verdict logic and contract parsing."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

# Load run_intake as a module without __main__ side-effects
_INTAKE_PATH = Path(__file__).resolve().parents[1] / "python_scripts" / "run_intake.py"
_spec = importlib.util.spec_from_file_location("run_intake", _INTAKE_PATH)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

_compute_verdict = _mod._compute_verdict
_thresholds_from_contract = _mod._thresholds_from_contract
_known_gap_contexts = _mod._known_gap_contexts


class TestComputeVerdict(unittest.TestCase):

    def _res(self, passed: bool, failures: list[str] | None = None) -> dict:
        return {"gate_passed": passed, "mean": {}, "failures": failures or []}

    def test_all_pass_accepted(self):
        results = {"night": self._res(True), "day": self._res(True)}
        verdict, notes = _compute_verdict(results, ["night", "day"], gap_contexts=set())
        self.assertEqual(verdict, "ACCEPTED")

    def test_fail_no_gap_rejected(self):
        results = {"night": self._res(False, ["false_lock_rate>0.55"]), "day": self._res(True)}
        verdict, notes = _compute_verdict(results, ["night", "day"], gap_contexts=set())
        self.assertEqual(verdict, "REJECTED")
        self.assertTrue(any("REJECTED" in n for n in notes))

    def test_fail_with_gap_hold(self):
        results = {"ir": self._res(False, ["false_lock_rate>0.70"]), "night": self._res(True)}
        verdict, notes = _compute_verdict(results, ["night", "ir"], gap_contexts={"ir"})
        self.assertEqual(verdict, "HOLD")
        self.assertTrue(any("HOLD" in n for n in notes))

    def test_dry_run_context_skipped(self):
        results = {"night": {"_dry_run": True}, "day": self._res(True)}
        verdict, notes = _compute_verdict(results, ["night", "day"], gap_contexts=set())
        self.assertEqual(verdict, "ACCEPTED")
        self.assertTrue(any("dry-run" in n for n in notes))

    def test_gap_context_fail_but_non_gap_pass(self):
        """IR fails (gap) + night fails (no gap) → REJECTED, not HOLD."""
        results = {
            "ir":    self._res(False, ["false_lock_rate>0.70"]),
            "night": self._res(False, ["false_lock_rate>0.55"]),
        }
        verdict, _ = _compute_verdict(results, ["night", "ir"], gap_contexts={"ir"})
        self.assertEqual(verdict, "REJECTED")

    def test_all_gap_fail_hold(self):
        """All fails are covered by gaps → HOLD."""
        results = {"ir": self._res(False), "day": self._res(False)}
        verdict, _ = _compute_verdict(results, ["ir", "day"], gap_contexts={"ir", "day"})
        self.assertEqual(verdict, "HOLD")


class TestContractParsing(unittest.TestCase):

    _CONTRACT = {
        "thresholds": {
            "night": {"false_lock_rate": {"max": 0.55}, "id_chg_per_min": {"max": 18.0}},
            "day":   {"false_lock_rate": {"max": 0.10}},
            "ir":    {"false_lock_rate": {"max": 0.70}, "status": "provisional"},
        },
        "known_gaps": [
            {"id": "IR_GAP_2026", "affected_contexts": ["ir"]},
        ],
    }

    def test_thresholds_night(self):
        t = _thresholds_from_contract(self._CONTRACT)
        self.assertEqual(t["night_false_lock"], "0.55")
        self.assertEqual(t["night_id_chg"], "18.0")

    def test_thresholds_day(self):
        t = _thresholds_from_contract(self._CONTRACT)
        self.assertEqual(t["day_false_lock"], "0.1")

    def test_thresholds_ir(self):
        t = _thresholds_from_contract(self._CONTRACT)
        self.assertEqual(t["ir_false_lock"], "0.7")

    def test_gap_contexts(self):
        gaps = _known_gap_contexts(self._CONTRACT)
        self.assertIn("ir", gaps)
        self.assertNotIn("night", gaps)

    def test_empty_gaps(self):
        contract = {**self._CONTRACT, "known_gaps": []}
        gaps = _known_gap_contexts(contract)
        self.assertEqual(gaps, set())


if __name__ == "__main__":
    unittest.main()


# ── verify_baseline tests ─────────────────────────────────────────────────────

import importlib.util as _ilu
import tempfile as _tempfile

_VB_PATH = Path(__file__).resolve().parents[1] / "python_scripts" / "verify_baseline.py"
_vb_spec = _ilu.spec_from_file_location("verify_baseline", _VB_PATH)
_vb_mod = _ilu.module_from_spec(_vb_spec)   # type: ignore[arg-type]
_vb_spec.loader.exec_module(_vb_mod)        # type: ignore[union-attr]
_verify = _vb_mod.verify


class TestVerifyBaseline(unittest.TestCase):

    def _make_model_and_manifest(self, tmp: Path, content: bytes, sha_override: str | None = None) -> tuple[Path, Path]:
        model = tmp / "model.pt"
        model.write_bytes(content)
        import hashlib
        real_sha = hashlib.sha256(content).hexdigest()
        manifest = tmp / "manifest.json"
        manifest.write_text(
            __import__("json").dumps({"source_sha256": sha_override or real_sha,
                                      "installed_at": "2026-01-01T00:00:00Z",
                                      "source_path": "fake/path.pt",
                                      "notes": "test"}),
            encoding="utf-8"
        )
        return model, manifest

    def test_pass_matching_sha(self):
        with _tempfile.TemporaryDirectory() as tmp:
            model, manifest = self._make_model_and_manifest(Path(tmp), b"fake model weights")
            self.assertTrue(_verify(model, manifest))

    def test_fail_mismatched_sha(self):
        with _tempfile.TemporaryDirectory() as tmp:
            model, manifest = self._make_model_and_manifest(
                Path(tmp), b"fake model weights", sha_override="0" * 64
            )
            self.assertFalse(_verify(model, manifest))
