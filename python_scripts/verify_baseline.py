#!/usr/bin/env python3
"""
OQ-005 — Baseline integrity verification.

Checks that models/baseline.pt matches the SHA256 recorded in
models/baseline_manifest.json. Detects corruption or accidental replacement.

Usage:
    python python_scripts/verify_baseline.py
    python python_scripts/verify_baseline.py --model models/night_model.pt --manifest models/night_manifest.json
    python python_scripts/verify_baseline.py --verbose

Exit codes:
    0 — PASS (SHA256 matches, manifest valid)
    1 — error (file not found, manifest malformed)
    4 — FAIL (SHA256 mismatch)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(model_path: Path, manifest_path: Path, verbose: bool = False) -> bool:
    """Returns True if verification passes."""

    if not manifest_path.exists():
        print(f"[error] Manifest not found: {manifest_path}")
        sys.exit(1)

    if not model_path.exists():
        print(f"[error] Model not found: {model_path}")
        sys.exit(1)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[error] Cannot parse manifest: {exc}")
        sys.exit(1)

    expected_sha = manifest.get("source_sha256", "")
    if not expected_sha:
        print("[error] Manifest has no source_sha256 field")
        sys.exit(1)

    print(f"[verify] Model:    {model_path}")
    print(f"[verify] Manifest: {manifest_path}")

    if verbose:
        print(f"[verify] Installed:  {manifest.get('installed_at', '?')}")
        print(f"[verify] Source:     {manifest.get('source_path', '?')}")
        print(f"[verify] Notes:      {manifest.get('notes', '?')[:80]}...")
        reports = manifest.get("preset_gate_reports", {})
        for ctx, rpath in reports.items():
            exists = "✓" if Path(ROOT / rpath).exists() else "✗ missing"
            print(f"[verify] Gate [{ctx}]: {rpath}  ({exists})")

    print(f"[verify] Expected SHA256: {expected_sha}")
    actual_sha = _sha256(model_path)
    print(f"[verify] Actual   SHA256: {actual_sha}")

    if actual_sha == expected_sha:
        print("[verify] PASS — baseline intact")
        return True
    else:
        print("[verify] FAIL — SHA256 mismatch (model replaced or corrupted)")
        return False


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OQ-005 Baseline integrity check.")
    p.add_argument("--model", type=Path, default=MODELS_DIR / "baseline.pt")
    p.add_argument("--manifest", type=Path, default=MODELS_DIR / "baseline_manifest.json")
    p.add_argument("--verbose", action="store_true", help="Show install metadata and gate report paths")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    passed = verify(args.model, args.manifest, verbose=args.verbose)
    return 0 if passed else 4


if __name__ == "__main__":
    sys.exit(main())
