#!/usr/bin/env python3
"""Build a filesystem inventory of the project: directory tree, size stats, entrypoints.

Produces three sections:
  1. Directory tree (limited depth, with per-dir size)
  2. Top-N heaviest directories
  3. Critical runtime entrypoints check

Usage:
    ./tracker_env/bin/python python_scripts/filesystem_inventory.py
    ./tracker_env/bin/python python_scripts/filesystem_inventory.py \\
        --root . --max-depth 3 --top-n 25 --output-md runs/fs_inventory.md
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Size helpers
# ---------------------------------------------------------------------------

def _dir_size(path: Path) -> int:
    """Recursively sum file sizes under path (bytes). Skips unreadable entries."""
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=True):
                    total += entry.stat(follow_symlinks=True).st_size
                elif entry.is_dir(follow_symlinks=True):
                    total += _dir_size(Path(entry.path))
            except (OSError, PermissionError):
                pass
    except (OSError, PermissionError):
        pass
    return total


def _fmt_size(n: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f'{n:.1f} {unit}'
        n /= 1024
    return f'{n:.1f} TB'


# ---------------------------------------------------------------------------
# Tree
# ---------------------------------------------------------------------------

# Directories to skip entirely (heavy artifacts, envs, caches)
_SKIP_DIRS: frozenset[str] = frozenset({
    'tracker_env', '.git', '__pycache__', '.mypy_cache', '.pytest_cache',
    'node_modules', '.venv', 'venv', '.tox',
})


def _tree_lines(
    path: Path,
    root: Path,
    max_depth: int,
    current_depth: int = 0,
    prefix: str = '',
) -> list[str]:
    lines: list[str] = []
    try:
        entries = sorted(path.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    except (OSError, PermissionError):
        return lines

    visible = [e for e in entries if e.name not in _SKIP_DIRS]

    for i, entry in enumerate(visible):
        is_last = i == len(visible) - 1
        connector = '└── ' if is_last else '├── '
        if entry.is_dir():
            if current_depth >= max_depth:
                lines.append(f'{prefix}{connector}{entry.name}/ [...]')
                continue
            sz = _dir_size(entry)
            lines.append(f'{prefix}{connector}{entry.name}/  ({_fmt_size(sz)})')
            extension = '    ' if is_last else '│   '
            lines.extend(_tree_lines(entry, root, max_depth, current_depth + 1, prefix + extension))
        else:
            try:
                sz = entry.stat(follow_symlinks=True).st_size
            except OSError:
                sz = 0
            lines.append(f'{prefix}{connector}{entry.name}  ({_fmt_size(sz)})')
    return lines


def build_tree(root: Path, max_depth: int) -> str:
    total = _dir_size(root)
    lines = [f'{root.name}/  ({_fmt_size(total)} total)', '']
    lines.extend(_tree_lines(root, root, max_depth))
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Top-N directories by size
# ---------------------------------------------------------------------------

def top_dirs(root: Path, n: int) -> list[tuple[Path, int]]:
    """Return top-N non-skipped directories by total size, relative to root."""
    result: list[tuple[Path, int]] = []

    def _walk(p: Path) -> None:
        try:
            for entry in os.scandir(p):
                if entry.is_dir(follow_symlinks=True):
                    if entry.name in _SKIP_DIRS:
                        continue
                    ep = Path(entry.path)
                    sz = _dir_size(ep)
                    result.append((ep, sz))
                    _walk(ep)
        except (OSError, PermissionError):
            pass

    _walk(root)
    result.sort(key=lambda x: x[1], reverse=True)
    return result[:n]


# ---------------------------------------------------------------------------
# Entrypoints check
# ---------------------------------------------------------------------------

CRITICAL_ENTRYPOINTS: list[str] = [
    'main_tracker.py',
    'tracker_gui.py',
    'app/__init__.py',
    'src/uav_tracker/__init__.py',
    'src/uav_tracker/pipeline.py',
    'src/uav_tracker/config.py',
    'src/uav_tracker/tracking/target_manager.py',
    'python_scripts/run_stable_cycle.py',
    'python_scripts/run_quality_gate.py',
    'python_scripts/run_offline_benchmark.py',
    'python_scripts/ingest_rtx_cycle.py',
]


def check_entrypoints(root: Path) -> list[tuple[str, bool]]:
    return [(ep, (root / ep).exists()) for ep in CRITICAL_ENTRYPOINTS]


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(root: Path, max_depth: int, top_n: int) -> str:
    lines: list[str] = []

    lines.append('# Filesystem Inventory')
    lines.append(f'\nRoot: `{root.resolve()}`')
    lines.append(f'Max depth: {max_depth} | Top-N dirs: {top_n}')

    # --- tree ---
    lines.append('\n## Directory Tree\n')
    lines.append('```')
    lines.append(build_tree(root, max_depth))
    lines.append('```')

    # --- top dirs ---
    lines.append(f'\n## Top-{top_n} Heaviest Directories (excl. skip-list)\n')
    lines.append('| Rank | Path | Size |')
    lines.append('|---|---|---|')
    for rank, (p, sz) in enumerate(top_dirs(root, top_n), 1):
        rel = p.relative_to(root)
        lines.append(f'| {rank} | `{rel}` | {_fmt_size(sz)} |')

    # --- entrypoints ---
    lines.append('\n## Critical Entrypoints\n')
    lines.append('| Path | Present |')
    lines.append('|---|---|')
    for ep, present in check_entrypoints(root):
        status = 'YES' if present else 'MISSING'
        lines.append(f'| `{ep}` | {status} |')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description='Build filesystem inventory of the project.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--root', default='.', metavar='DIR', help='Project root (default: .).')
    p.add_argument('--max-depth', type=int, default=3, metavar='N', help='Tree depth (default: 3).')
    p.add_argument('--top-n', type=int, default=25, metavar='N', help='Top-N dirs by size (default: 25).')
    p.add_argument('--output-md', metavar='PATH', default='', help='Save report as Markdown.')
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f'Error: root not found: {root}', file=sys.stderr)
        return 2

    report = build_report(root, args.max_depth, args.top_n)
    print(report)

    if args.output_md:
        out = Path(args.output_md)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding='utf-8')
        print(f'\nMarkdown saved: {out}', file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
