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

_CONTEXT_SLOTS: dict[str, tuple[str, str]] = {
    "baseline": ("baseline.pt", "baseline_manifest.json"),
    "night":    ("night_model.pt", "night_manifest.json"),
    "ir":       ("ir_model.pt", "ir_manifest.json"),
    "day":      ("day_model.pt", "day_manifest.json"),
}

# Defaults (overridden by --context)
BASELINE_PT = MODELS_DIR / "baseline.pt"
MANIFEST_PATH = MODELS_DIR / "baseline_manifest.json"


def _parse_preset_gates(spec: str) -> dict[str, str]:
    """Parse 'day=path1,night=path2,ir=path3' → {'day': 'path1', ...}."""
    result: dict[str, str] = {}
    for part in spec.split(","):
        part = part.strip()
        if "=" in part:
            key, _, val = part.partition("=")
            key = key.strip()
            val = val.strip()
            if key and val:
                result[key] = val
    return result


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
    p.add_argument(
        "--context",
        type=str,
        default="baseline",
        choices=list(_CONTEXT_SLOTS.keys()),
        help=(
            "Model context slot to install into (default: baseline). "
            "baseline → models/baseline.pt, night → models/night_model.pt, "
            "ir → models/ir_model.pt, day → models/day_model.pt."
        ),
    )
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
    p.add_argument(
        "--preset-gates",
        type=str,
        default="",
        help=(
            "Comma-separated preset-specific gate report paths for traceability. "
            "Format: day=<path>,night=<path>,ir=<path>. "
            "Stored in manifest as preset_gate_reports dict."
        ),
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    src = args.source.resolve()
    if not src.exists():
        print(f"ERROR: source not found: {src}", file=sys.stderr)
        raise SystemExit(1)

    model_filename, manifest_filename = _CONTEXT_SLOTS[args.context]
    target_pt = MODELS_DIR / model_filename
    target_manifest = MODELS_DIR / manifest_filename

    gate_report_path = None
    if args.gate_report is not None:
        gate_report_path = str(args.gate_report.resolve())
        if not args.gate_report.exists() and not args.dry_run:
            print(f"WARNING: gate-report not found: {args.gate_report}", file=sys.stderr)

    manifest = {
        "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "context": args.context,
        "source_path": str(src),
        "source_sha256": _sha256(src),
        "notes": args.notes,
        "gate_report_path": gate_report_path,
        "preset_gate_reports": _parse_preset_gates(args.preset_gates),
    }

    if args.dry_run:
        print("DRY RUN — manifest preview:")
        print(json.dumps(manifest, indent=2))
        print(f"\nWould install [{args.context}]: {src}")
        print(f"  -> {target_pt}")
        print(f"  -> {target_manifest}")
        return

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target_pt)
    target_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Installed [{args.context}]: {target_pt}")
    print(f"Manifest written:             {target_manifest}")
    print(f"SHA256: {manifest['source_sha256']}")


if __name__ == "__main__":
    main()
