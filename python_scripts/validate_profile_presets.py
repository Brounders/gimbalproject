#!/usr/bin/env python3
"""Validate configs/*.yaml preset files against the profile_io key mapping.

Reads the YAML key-to-Config-attr mapping from src/uav_tracker/profile_io.py
using stdlib ast (no import of the module itself), then checks each YAML file:

  - Unknown keys  : present in YAML, absent from mapping
  - Invalid types : value type mismatches well-known bool/numeric/str fields
  - Non-flat YAMLs: files with nested dict/list values are skipped (not presets)

Exit code: 0 — all files pass, 1 — one or more issues found.

Usage:
    ./tracker_env/bin/python python_scripts/validate_profile_presets.py
    ./tracker_env/bin/python python_scripts/validate_profile_presets.py \\
        --configs-dir configs --profile-io src/uav_tracker/profile_io.py
    ./tracker_env/bin/python python_scripts/validate_profile_presets.py \\
        configs/night.yaml configs/fast.yaml
"""

from __future__ import annotations

import argparse
import ast
import sys
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

# Known type constraints: key → expected Python type(s)
_TYPE_RULES: dict[str, tuple[type, ...]] = {
    # booleans
    'small_target_mode': (bool,),
    'night_enabled': (bool,),
    'roi_assist_enabled': (bool,),
    'budget_enabled': (bool,),
    'adaptive_scan_enabled': (bool,),
    'lock_tracker_enabled': (bool,),
    'active_strict_lock_switch': (bool,),
    'show_gt_overlay': (bool,),
    'show_debug_timings': (bool,),
    'show_focus_window': (bool,),
    'show_lock_search_window': (bool,),
    'lock_focus_only': (bool,),
    'disable_night_on_lock': (bool,),
    'reticle_overlay_enabled': (bool,),
    'ir_mode_enabled': (bool,),
    'night_run_when_primary_seen': (bool,),
    'display_box_adaptive': (bool,),
    'lock_event_log_enabled': (bool,),
    'show_trails': (bool,),
    'operator_minimal_overlay': (bool,),
    # numeric (int or float accepted)
    'imgsz': (int,),
    'conf_thresh': (int, float),
    'roi_conf_thresh': (int, float),
    'budget_target_fps': (int, float),
    'budget_high_load': (int, float),
    'budget_low_load': (int, float),
    'budget_level_max': (int,),
    'budget_roi_min_candidates': (int,),
    'budget_night_skip_level1': (int,),
    'budget_night_skip_level2': (int,),
    'budget_roi_skip_level2': (int,),
    'budget_scan_interval_boost_per_level': (int, float),
    'budget_local_validate_boost_per_level': (int, float),
    'night_mot_thresh': (int,),
    'night_diff_thresh': (int,),
    'night_min_area': (int,),
    'night_max_area': (int,),
    'night_confirm': (int,),
    'night_border': (int,),
    'night_max_ar': (int, float),
    'night_track_dist': (int, float),
    'night_lost_max': (int,),
    'yolo_lost_max': (int,),
    'global_scan_interval': (int,),
    'roi_max_candidates': (int,),
    'local_track_img_size': (int,),
    'local_track_conf': (int, float),
    'local_validate_interval': (int,),
    'local_small_box_area': (int,),
    'local_small_box_ratio': (int, float),
    'local_small_img_size': (int,),
    'local_small_conf': (int, float),
    'local_boost_lock_score_thresh': (int, float),
    'lock_tracker_min_score': (int, float),
    'lock_tracker_search_scale': (int, float),
    'velocity_alpha': (int, float),
    'lock_reacquire_predict_gain': (int, float),
    'lock_reacquire_predict_horizon_max': (int,),
    'lock_mode_acquire_frames': (int,),
    'lock_mode_release_frames': (int,),
    'lock_lost_grace': (int,),
    'active_id_switch_cooldown_frames': (int,),
    'active_id_switch_allow_if_lost_frames': (int,),
    'track_state_acquire_frames': (int,),
    'track_state_lost_frames': (int,),
    'track_state_reset_frames': (int,),
    'class_ema_alpha': (int, float),
    'drone_lock_score_min': (int, float),
    'drone_reacquire_score_min': (int, float),
    'reticle_half_size': (int,),
    'reticle_dot_radius': (int,),
    'reticle_center_alpha': (int, float),
    'reticle_hold_frames': (int,),
    'display_box_alpha': (int, float),
    'display_box_alpha_min': (int, float),
    'display_box_alpha_max': (int, float),
    'display_box_speed_gain': (int, float),
    'display_box_size_gain': (int, float),
    'display_box_hold_frames': (int,),
    'ir_noise_threshold': (int, float),
    'confirmation_frames_ir_noise': (int,),
    'ir_noise_unverified_rate': (int, float),
    'ir_noise_unverified_rate_city_lights': (int, float),
    'ir_noise_ema_alpha': (int, float),
    'confidence_ema_alpha': (int, float),
    'confidence_display_update_sec': (int, float),
    'night_primary_cooldown': (int,),
    'display_min_hit_streak_primary': (int,),
    'display_min_hit_streak_night': (int,),
    'display_max_lost_frames': (int,),
    # strings
    'model_path': (str,),
    'device': (str,),
    'runtime_mode': (str,),
    'lock_event_log_path': (str,),
}


def extract_mapping_keys(profile_io_path: Path) -> frozenset[str]:
    """Parse profile_io.py with ast and return the preset key set.

    Looks for the assignment ``mapping = {...}`` inside apply_overrides().
    Falls back to an empty frozenset if parsing fails.
    """
    try:
        source = profile_io_path.read_text(encoding='utf-8')
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        print(f'Warning: cannot parse {profile_io_path}: {exc}', file=sys.stderr)
        return frozenset()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'mapping':
                if isinstance(node.value, ast.Dict):
                    keys: set[str] = set()
                    for k in node.value.keys:
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            keys.add(k.value)
                    if keys:
                        return frozenset(keys)
    return frozenset()


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


def validate_file(path: Path, known_keys: frozenset[str]) -> FileResult:
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

    for key, value in data.items():
        if key not in all_valid:
            result.unknown.append(key)
            continue
        if key in _TYPE_RULES and value is not None:
            expected = _TYPE_RULES[key]
            if not isinstance(value, expected):
                result.type_errors.append(
                    f"  {key}: expected {'/'.join(t.__name__ for t in expected)}"
                    f", got {type(value).__name__} ({value!r})"
                )

    return result


def validate_files(paths: list[Path], known_keys: frozenset[str]) -> list[FileResult]:
    return [validate_file(p, known_keys) for p in paths]


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
    results = validate_files(paths, known_keys)
    print_results(results)

    has_failures = any(not r.ok and not r.skipped for r in results)
    return 1 if has_failures else 0


if __name__ == '__main__':
    sys.exit(main())
