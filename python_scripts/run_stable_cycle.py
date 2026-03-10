#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "tracker_env" / "bin" / "python"

# ---------------------------------------------------------------------------
# Pre-flight: validate preset YAML before running benchmark
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
try:
    from validate_profile_presets import extract_mapping_keys, build_type_rules, validate_file
    _HAS_VALIDATOR = True
except ImportError:
    _HAS_VALIDATOR = False


def _preflight_validate_preset(preset_name: str) -> bool:
    """Validate the named preset YAML. Returns True if OK or validation not available."""
    if not _HAS_VALIDATOR:
        print('[preflight] WARNING: validate_profile_presets not available — skipping preset check.')
        return True

    preset_path = ROOT / 'configs' / f'{preset_name}.yaml'
    if not preset_path.exists():
        print(f'[preflight] ERROR: preset file not found: {preset_path}')
        return False

    profile_io = ROOT / 'src' / 'uav_tracker' / 'profile_io.py'
    src_dir = ROOT / 'src'
    known_keys = extract_mapping_keys(profile_io)
    if not known_keys:
        print(f'[preflight] WARNING: could not load key mapping from {profile_io} — skipping type checks.')
        return True

    type_rules = build_type_rules(profile_io, src_dir)
    result = validate_file(preset_path, known_keys, type_rules)

    if result.skipped:
        print(f'[preflight] WARNING: preset validation skipped ({result.skipped}) — continuing.')
        return True
    if not result.ok:
        print(f'[preflight] ERROR: preset "{preset_name}" has {result.issue_count} issue(s):')
        for key in result.unknown:
            print(f'  unknown key: {key}')
        for te in result.type_errors:
            print(te)
        return False

    print(f'[preflight] preset "{preset_name}" OK ({len(known_keys)} keys validated)')
    return True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stable cycle orchestrator: RTX artifact -> benchmark -> quality gate -> release decision.")
    p.add_argument("--rtx-model", type=Path, default=Path("models/checkpoints/rtx_drone_first_6h_v2_best.pt"))
    p.add_argument("--candidate-preset", type=str, default="night_rtx_candidate")
    p.add_argument("--pack-file", type=Path, default=Path("configs/regression_pack.csv"))
    p.add_argument("--device", type=str, default="mps")
    p.add_argument("--mode", type=str, default="operator")
    p.add_argument("--max-frames", type=int, default=240)
    p.add_argument("--run-ab", action="store_true")
    p.add_argument("--ab-base-preset", type=str, default="night_ir_lock_v2")
    p.add_argument("--ab-profiles", type=str, default="operator_standard,fast")
    p.add_argument("--tag", type=str, default="")
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/stable_cycle"))
    return p.parse_args()


def _run(cmd: list[str], *, allow_fail: bool = False) -> int:
    print("[exec]", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=ROOT, check=False)
    if proc.returncode != 0 and not allow_fail:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    return int(proc.returncode)


def _latest_matching(path_glob: str) -> Path | None:
    matches = sorted(ROOT.glob(path_glob), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # Pre-flight: validate candidate preset before spending time on benchmark
    if not _preflight_validate_preset(args.candidate_preset):
        print(f'[stable_cycle] Aborted: preset "{args.candidate_preset}" failed pre-flight validation.')
        return 2

    if not args.rtx_model.exists():
        print(f"[error] RTX model not found: {args.rtx_model}")
        return 2

    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    tag = f"{args.tag}stable_{stamp}_"

    ab_winner = "operator_standard"
    ab_json_path: Path | None = None
    if args.run_ab:
        _run(
            [
                str(PY),
                "python_scripts/run_profile_ab.py",
                "--base-preset",
                args.ab_base_preset,
                "--profiles",
                args.ab_profiles,
                "--mode",
                args.mode,
                "--device",
                args.device,
                "--max-frames",
                str(args.max_frames),
                "--tag",
                tag,
            ]
        )
        ab_json_path = _latest_matching(f"runs/evaluations/ab/{tag}profile_ab_*.json")
        if ab_json_path and ab_json_path.exists():
            payload = json.loads(ab_json_path.read_text(encoding="utf-8"))
            ab_winner = str(payload.get("winner") or "operator_standard")

    _run(
        [
            str(PY),
            "python_scripts/run_offline_benchmark.py",
            "--source-list",
            str(args.pack_file),
            "--preset",
            args.candidate_preset,
            "--mode",
            args.mode,
            "--device",
            args.device,
            "--max-frames",
            str(args.max_frames),
            "--tag",
            tag,
        ]
    )

    gate_code = _run(
        [
            str(PY),
            "python_scripts/run_quality_gate.py",
            "--pack-file",
            str(args.pack_file),
            "--preset",
            args.candidate_preset,
            "--mode",
            args.mode,
            "--device",
            args.device,
            "--max-frames",
            str(args.max_frames),
            "--tag",
            tag,
        ],
        allow_fail=True,
    )

    bench_json = _latest_matching(f"runs/evaluations/benchmark/{tag}benchmark_{args.candidate_preset}.json")
    gate_json = _latest_matching(f"runs/evaluations/quality_gate/{tag}quality_gate_{args.candidate_preset}.json")
    if gate_json is None or not gate_json.exists():
        print("[error] quality gate report not found")
        return 3

    gate_payload = json.loads(gate_json.read_text(encoding="utf-8"))
    gate_passed = bool(gate_payload.get("gate_passed", False))
    mean_score = float((gate_payload.get("mean") or {}).get("score", 0.0))
    release_decision = "release_candidate" if (gate_passed and mean_score >= 45.0) else "hold_and_tune"

    summary = {
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "stages": {
            "rtx_training": "provided_artifact",
            "rtx_export": str(args.rtx_model),
            "mac_benchmark": str(bench_json) if bench_json else "",
            "mac_quality_gate": str(gate_json),
            "mac_quality_gate_exit_code": gate_code,
        },
        "candidate_preset": args.candidate_preset,
        "operator_profile_winner": ab_winner,
        "quality_gate_passed": gate_passed,
        "quality_gate_mean_score": mean_score,
        "release_decision": release_decision,
        "ab_report": str(ab_json_path) if ab_json_path else "",
        "next_action": (
            "release profile" if release_decision == "release_candidate" else "retune ir-noise thresholds / lock confirm"
        ),
    }

    out_json = args.out_dir / f"{tag}stable_cycle_decision.json"
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[summary] decision={release_decision}")
    print(f"[summary] json={out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
