#!/usr/bin/env python3
"""Validate configs/*.yaml preset files against the profile_io key mapping.

Reads the YAML key-to-Config-attr mapping from src/uav_tracker/profile_io.py
using stdlib ast (no import of the module itself), then checks each YAML file:

  - Unknown keys  : present in YAML, absent from mapping
  - Invalid types : value type mismatches derived from Config dataclass fields
  - Non-flat YAMLs: files with nested dict/list values are skipped (not presets)

Type rules are derived automatically from uav_tracker.config.Config via
dataclasses.fields() when PYTHONPATH=src is available. Without PYTHONPATH
the validator degrades gracefully: unknown-key checks still work, type checks
are skipped with a warning.

Exit code: 0 — all files pass, 1 — one or more issues found, 2 — critical error.

Usage:
    ./tracker_env/bin/python python_scripts/validate_profile_presets.py
    PYTHONPATH=src ./tracker_env/bin/python python_scripts/validate_profile_presets.py \\
        --configs-dir configs --profile-io src/uav_tracker/profile_io.py
    PYTHONPATH=src ./tracker_env/bin/python python_scripts/validate_profile_presets.py \\
        configs/night.yaml configs/fast.yaml
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import sys
import typing
from pathlib import Path
from typing import Any

try:
    import yaml as _yaml
    def _load_yaml(path: Path) -> dict:
        data = _yaml.safe_load(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
except ImportError:
    print('Error: PyYAML not found. Run with tracker_env: ./tracker_env/bin/python ...', file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Key extraction from profile_io.py (stdlib ast, no import of the module)
# ---------------------------------------------------------------------------

# Keys that are valid at the top-level of a YAML but are NOT preset keys —
# they belong to profile/launcher configs.
PROFILE_ONLY_KEYS: frozenset[str] = frozenset({
    'preset', 'source', 'record_output', 'output_path',
})

# Keys that are informational / non-preset but tolerated at the top level.
INFORMATIONAL_KEYS: frozenset[str] = frozenset({'name'})

# ---------------------------------------------------------------------------
# Type rules: auto-derived from Config dataclass via dataclasses.fields()
# ---------------------------------------------------------------------------

def _annotation_to_yaml_types(ann: Any) -> tuple[type, ...] | None:
    """Convert a Config field type annotation to allowed YAML Python types.

    Rules:
      bool        → (bool,)          YAML true/false only
      int         → (int,)           YAML integers only
      float       → (int, float)     YAML allows int literals for float fields
      str         → (str,)
      Union[...]  → union of above rules for each arg (skip Optional/None/list)
      other       → None (skip; too complex to validate meaningfully)
    """
    _SIMPLE: dict[type, tuple[type, ...]] = {
        bool: (bool,),
        int: (int,),
        float: (int, float),   # YAML integer is a valid float value
        str: (str,),
    }
    if ann in _SIMPLE:
        return _SIMPLE[ann]

    origin = typing.get_origin(ann)
    if origin is typing.Union:
        result: list[type] = []
        for arg in typing.get_args(ann):
            if arg is type(None):
                continue
            mapped = _SIMPLE.get(arg)
            if mapped:
                for t in mapped:
                    if t not in result:
                        result.append(t)
        return tuple(result) if result else None

    return None  # complex type (list, dict, etc.) — skip validation


def extract_mapping_dict(profile_io_path: Path) -> dict[str, str]:
    """Parse profile_io.py with ast and return {yaml_key: CONFIG_ATTR} mapping."""
    try:
        source = profile_io_path.read_text(encoding='utf-8')
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        print(f'Warning: cannot parse {profile_io_path}: {exc}', file=sys.stderr)
        return {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'mapping':
                if isinstance(node.value, ast.Dict):
                    result: dict[str, str] = {}
                    for k, v in zip(node.value.keys, node.value.values):
                        if (isinstance(k, ast.Constant) and isinstance(k.value, str)
                                and isinstance(v, ast.Constant) and isinstance(v.value, str)):
                            result[k.value] = v.value
                        elif (isinstance(k, ast.Constant) and isinstance(k.value, str)
                              and isinstance(v, ast.Constant) and v.value is None):
                            result[k.value] = ''   # None value means: key exists but no attr mapping
                    if result:
                        return result
    return {}


def build_type_rules(profile_io_path: Path, src_dir: Path | None = None) -> dict[str, tuple[type, ...]]:
    """Build {yaml_key: allowed_types} by reading Config field annotations.

    Uses dataclasses.fields() on uav_tracker.config.Config.
    If Config cannot be imported (no PYTHONPATH), returns empty dict and
    prints a warning — validation continues without type checks.
    """
    mapping = extract_mapping_dict(profile_io_path)
    if not mapping:
        return {}

    # Try to import Config. Add src_dir to sys.path temporarily if given.
    _added = False
    if src_dir is not None:
        src_str = str(src_dir.resolve())
        if src_str not in sys.path:
            sys.path.insert(0, src_str)
            _added = True
    try:
        from uav_tracker.config import Config  # type: ignore[import]
        cfg_fields: dict[str, Any] = {f.name: f.type for f in dataclasses.fields(Config)}
    except ImportError:
        print(
            'Warning: cannot import uav_tracker.config.Config — type checks disabled.\n'
            '  Run with PYTHONPATH=src to enable type validation.',
            file=sys.stderr,
        )
        return {}
    finally:
        if _added and sys.path and sys.path[0] == src_str:
            sys.path.pop(0)

    rules: dict[str, tuple[type, ...]] = {}
    for yaml_key, config_attr in mapping.items():
        if not config_attr:
            continue
        ann = cfg_fields.get(config_attr)
        if ann is None:
            continue
        allowed = _annotation_to_yaml_types(ann)
        if allowed is not None:
            rules[yaml_key] = allowed
    return rules


def extract_mapping_keys(profile_io_path: Path) -> frozenset[str]:
    """Parse profile_io.py with ast and return the preset key set.

    Thin wrapper around extract_mapping_dict() kept for backward compatibility.
    """
    return frozenset(extract_mapping_dict(profile_io_path).keys())


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

class FileResult:
    def __init__(self, path: Path):
        self.path = path
        self.skipped: str = ''         # non-empty → file was skipped, reason here
        self.unknown: list[str] = []
        self.type_errors: list[str] = []

    @property
    def ok(self) -> bool:
        return not self.skipped and not self.unknown and not self.type_errors

    @property
    def issue_count(self) -> int:
        return len(self.unknown) + len(self.type_errors)


def _is_flat(data: dict) -> bool:
    """Return True if all top-level values are scalars (no nested dicts/lists)."""
    return all(not isinstance(v, (dict, list)) for v in data.values())


def validate_file(
    path: Path,
    known_keys: frozenset[str],
    type_rules: dict[str, tuple[type, ...]] | None = None,
) -> FileResult:
    result = FileResult(path)
    try:
        data = _load_yaml(path)
    except Exception as exc:
        result.skipped = f'YAML parse error: {exc}'
        return result

    if not _is_flat(data):
        result.skipped = 'non-flat structure (not a preset)'
        return result

    all_valid = known_keys | PROFILE_ONLY_KEYS | INFORMATIONAL_KEYS
    rules = type_rules or {}

    for key, value in data.items():
        if key not in all_valid:
            result.unknown.append(key)
            continue
        if key in rules and value is not None:
            expected = rules[key]
            if not isinstance(value, expected):
                result.type_errors.append(
                    f"  {key}: expected {'/'.join(t.__name__ for t in expected)}"
                    f", got {type(value).__name__} ({value!r})"
                )

    return result


def validate_files(
    paths: list[Path],
    known_keys: frozenset[str],
    type_rules: dict[str, tuple[type, ...]] | None = None,
) -> list[FileResult]:
    return [validate_file(p, known_keys, type_rules) for p in paths]


def print_results(results: list[FileResult]) -> None:
    any_issues = False
    for r in results:
        if r.skipped:
            print(f'  SKIP  {r.path.name}: {r.skipped}')
            continue
        if r.ok:
            print(f'  OK    {r.path.name}')
        else:
            any_issues = True
            print(f'  FAIL  {r.path.name}  ({r.issue_count} issue(s))')
            if r.unknown:
                print(f'    unknown keys: {", ".join(sorted(r.unknown))}')
            for te in r.type_errors:
                print(te)
    if any_issues:
        print()
        failed = sum(1 for r in results if not r.ok and not r.skipped)
        print(f'FAIL: {failed} file(s) with issues.')
    else:
        checked = sum(1 for r in results if not r.skipped)
        print(f'OK: {checked} preset(s) valid.')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description='Validate YAML preset files against profile_io key mapping.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        'files',
        nargs='*',
        metavar='YAML',
        help='Explicit YAML file(s) to validate. If omitted, scans --configs-dir.',
    )
    p.add_argument(
        '--configs-dir',
        metavar='DIR',
        default='configs',
        help='Directory to scan for *.yaml files (default: configs).',
    )
    p.add_argument(
        '--profile-io',
        metavar='PATH',
        default='src/uav_tracker/profile_io.py',
        help='Path to profile_io.py to extract the key mapping from.',
    )
    p.add_argument(
        '--src-dir',
        metavar='DIR',
        default='src',
        help='Path to src/ dir added to PYTHONPATH for Config import (default: src).',
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    profile_io_path = Path(args.profile_io)
    known_keys = extract_mapping_keys(profile_io_path)
    if not known_keys:
        print(f'Error: could not extract key mapping from {profile_io_path}', file=sys.stderr)
        return 2
    print(f'Loaded {len(known_keys)} known preset keys from {profile_io_path}')

    src_dir = Path(args.src_dir) if args.src_dir else None
    type_rules = build_type_rules(profile_io_path, src_dir)
    if type_rules:
        print(f'Auto-derived type rules for {len(type_rules)} keys from Config dataclass')
    else:
        print('Type rules unavailable — only unknown-key checks active', file=sys.stderr)

    if args.files:
        paths = [Path(f) for f in args.files]
        missing = [p for p in paths if not p.exists()]
        for m in missing:
            print(f'Error: file not found: {m}', file=sys.stderr)
        paths = [p for p in paths if p.exists()]
    else:
        configs_dir = Path(args.configs_dir)
        if not configs_dir.exists():
            print(f'Error: configs dir not found: {configs_dir}', file=sys.stderr)
            return 2
        paths = sorted(configs_dir.glob('*.yaml'))

    if not paths:
        print('No YAML files to validate.')
        return 0

    print(f'Validating {len(paths)} file(s):\n')
    results = validate_files(paths, known_keys, type_rules)
    print_results(results)

    has_failures = any(not r.ok and not r.skipped for r in results)
    return 1 if has_failures else 0


if __name__ == '__main__':
    sys.exit(main())
