#!/usr/bin/env python3
"""Compatibility wrapper for archived prototype script."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    current = Path(__file__).resolve()
    target = current.parent / "legacy" / "prototypes" / current.name
    if not target.exists():
        print(f"[ERROR] Archived script not found: {target}", file=sys.stderr)
        return 2

    print(
        f"[DEPRECATED] {current.name} moved to {target}. "
        "Use app/main_cli.py or app/main_gui.py for production workflows.",
        file=sys.stderr,
    )
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
