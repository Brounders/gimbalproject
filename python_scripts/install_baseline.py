#!/usr/bin/env python3
"""
Install an accepted model as the local production baseline.

Copies the source .pt to models/baseline.pt and writes models/baseline_manifest.json
with traceability metadata (sha256, source path, install date, gate report link).

Usage:
    python python_scripts/install_baseline.py \\
        --source <path_to_accepted.pt> \\
        --notes "Accepted YYYYMMDD: brief description" \\
        --gate-report runs/evaluations/quality_gate/<tag>_quality_gate_<preset>.json

    # Dry run (inspect manifest without copying)
    python python_scripts/install_baseline.py --source <path> --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
BASELINE_PT = MODELS_DIR / "baseline.pt"
MANIFEST_PATH = MODELS_DIR / "baseline_manifest.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Install accepted model as local baseline with traceability manifest."
    )
    p.add_argument("--source", type=Path, required=True, help="Path to the accepted .pt model.")
    p.add_argument("--notes", type=str, default="", help="Free-form acceptance note (date, description).")
    p.add_argument(
        "--gate-report",
        type=Path,
        default=None,
        help="Path to quality gate JSON output for traceability.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print manifest without copying files.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    src = args.source.resolve()
    if not src.exists():
        print(f"ERROR: source not found: {src}", file=sys.stderr)
        raise SystemExit(1)

    gate_report_path = None
    if args.gate_report is not None:
        gate_report_path = str(args.gate_report.resolve())
        if not args.gate_report.exists() and not args.dry_run:
            print(f"WARNING: gate-report not found: {args.gate_report}", file=sys.stderr)

    manifest = {
        "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": str(src),
        "source_sha256": _sha256(src),
        "notes": args.notes,
        "gate_report_path": gate_report_path,
    }

    if args.dry_run:
        print("DRY RUN — manifest preview:")
        print(json.dumps(manifest, indent=2))
        print(f"\nWould install: {src}")
        print(f"  -> {BASELINE_PT}")
        print(f"  -> {MANIFEST_PATH}")
        return

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, BASELINE_PT)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Installed baseline: {BASELINE_PT}")
    print(f"Manifest written:   {MANIFEST_PATH}")
    print(f"SHA256: {manifest['source_sha256']}")


if __name__ == "__main__":
    main()
