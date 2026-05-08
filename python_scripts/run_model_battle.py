#!/usr/bin/env python3
"""Compare candidate detector models on the project regression packs.

This is a measurement-only runner. It does not promote models, change presets,
start training, or alter the runtime pipeline. It runs the existing quality gate
with explicit candidate model overrides and optionally saves overlay previews so
failures can be inspected visually.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_tracker.config import Config
from uav_tracker.modes import apply_runtime_mode
from uav_tracker.pipeline import apply_runtime_preset, parse_video_source, run_tracker
from uav_tracker.profile_io import load_preset


@dataclass(frozen=True)
class ContextSpec:
    name: str
    preset: str
    pack_file: Path
    thresholds: tuple[str, ...]


CONTEXTS_FULL: dict[str, ContextSpec] = {
    "day": ContextSpec(
        name="day",
        preset="default",
        pack_file=Path("configs/regression_pack_day.csv"),
        thresholds=("--max-false-lock-rate", "0.10"),
    ),
    "night": ContextSpec(
        name="night",
        preset="night",
        pack_file=Path("configs/regression_pack_night.csv"),
        thresholds=("--max-false-lock-rate", "0.55", "--max-night-id-changes-per-min", "18.0"),
    ),
    "ir": ContextSpec(
        name="ir",
        preset="antiuav_thermal",
        pack_file=Path("configs/regression_pack_ir.csv"),
        thresholds=("--max-false-lock-rate", "0.70"),
    ),
}

CONTEXTS_SMOKE: dict[str, ContextSpec] = {
    "day": CONTEXTS_FULL["day"],
    "night": ContextSpec(
        name="night",
        preset="night",
        pack_file=Path("configs/regression_pack_problem_night.csv"),
        thresholds=CONTEXTS_FULL["night"].thresholds,
    ),
    "ir": ContextSpec(
        name="ir",
        preset="antiuav_thermal",
        pack_file=Path("configs/regression_pack_problem_ir.csv"),
        thresholds=CONTEXTS_FULL["ir"].thresholds,
    ),
}

DEFAULT_MODELS = ("baseline", "yolo26n.pt", "yolo26s.pt")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run a baseline vs candidate model battle on GimbalProject packs.")
    p.add_argument("--models", default=",".join(DEFAULT_MODELS),
                   help="Comma-separated models. Use 'baseline' for current preset/fallback model.")
    p.add_argument("--scope", choices=("smoke", "full"), default="smoke",
                   help="smoke uses problem packs and max frame limits; full uses full current regression packs.")
    p.add_argument("--contexts", default="day,night,ir", help="Comma-separated contexts: day,night,ir.")
    p.add_argument("--max-frames", type=int, default=180,
                   help="Per-source frame limit. Use 0 for unlimited. Smoke default is 180.")
    p.add_argument("--preview-frames", type=int, default=180, help="Per-source overlay preview frame limit.")
    p.add_argument("--no-preview", action="store_true", help="Skip overlay video generation.")
    p.add_argument("--device", default="", help="Optional device override, e.g. cpu/mps/cuda.")
    p.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/model_battle"))
    p.add_argument("--tag", default="", help="Optional run tag prefix.")
    return p.parse_args()


def _safe_name(value: str) -> str:
    value = Path(value).stem if value != "baseline" else value
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return value or "model"


def _load_pack(path: Path) -> list[dict[str, str]]:
    resolved = path if path.is_absolute() else ROOT / path
    entries: list[dict[str, str]] = []
    for raw in resolved.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",", 1)]
        entries.append({"source": parts[0], "scene": parts[1].lower() if len(parts) > 1 else "unknown"})
    return entries


def _resolve_source(raw_source: str) -> str:
    if raw_source.isdigit():
        return raw_source
    path = Path(raw_source)
    if path.is_absolute() and path.exists():
        return str(path)
    if path.exists():
        return str(path)
    rooted = ROOT / path
    if rooted.exists():
        return str(rooted)
    return raw_source


def _ensure_model_available(model_spec: str) -> str:
    if model_spec == "baseline":
        return ""
    search_paths = [
        Path(model_spec),
        ROOT / model_spec,
        ROOT / "models" / "candidates" / model_spec,
    ]
    for path in search_paths:
        if path.exists():
            return str(path)
    path = Path(model_spec)
    if path.is_absolute() or "/" in model_spec:
        return model_spec

    # Ultralytics can download known model names, but TrackerPipeline requires a
    # real local file before backend construction. Trigger the download once.
    try:
        from ultralytics import YOLO

        YOLO(model_spec)
    except Exception as exc:
        raise RuntimeError(f"Ultralytics не смог подготовить {model_spec}: {exc}") from exc

    for candidate in (ROOT / model_spec, Path.cwd() / model_spec, Path(model_spec), ROOT / "models" / "candidates" / model_spec):
        if candidate.exists():
            return str(candidate)
    return model_spec


def _gate_cmd(
    *,
    context: ContextSpec,
    model_label: str,
    model_path: str,
    out_dir: Path,
    max_frames: int,
    device: str,
) -> list[str]:
    cmd = [
        sys.executable,
        str(ROOT / "python_scripts" / "run_quality_gate.py"),
        "--pack-file",
        str(context.pack_file),
        "--preset",
        context.preset,
        "--out-dir",
        str(out_dir),
        "--tag",
        f"{model_label}_",
    ]
    cmd.extend(context.thresholds)
    if max_frames > 0:
        cmd.extend(["--max-frames", str(max_frames)])
    if model_path:
        cmd.extend(["--model", model_path])
    if device:
        cmd.extend(["--device", device])
    return cmd


def _run_gate(cmd: list[str]) -> int:
    print("[battle] gate:", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=str(ROOT))
    return int(result.returncode)


def _quality_json_path(model_label: str, context: ContextSpec, out_dir: Path) -> Path:
    return out_dir / f"{model_label}_quality_gate_{context.preset}.json"


def _load_quality(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"gate_passed": False, "rows": [], "mean": {}, "failures": [f"missing:{path}"]}
    return json.loads(path.read_text(encoding="utf-8"))


def _build_cfg(context: ContextSpec, model_path: str, device: str) -> tuple[Config, bool]:
    cfg = Config()
    cfg, preset_data = load_preset(context.preset, cfg)
    if device:
        cfg.DEVICE = device
    if model_path:
        cfg.MODEL_PATH = model_path
    if context.preset == "default":
        cfg = apply_runtime_mode(cfg, "operator")
    small_target = bool(preset_data.get("small_target_mode", False))
    cfg = apply_runtime_preset(cfg, small_target_mode=small_target)
    return cfg, small_target


def _save_previews(
    *,
    context: ContextSpec,
    model_label: str,
    model_path: str,
    out_dir: Path,
    preview_frames: int,
    device: str,
) -> list[Path]:
    preview_dir = out_dir / "previews" / model_label / context.name
    preview_dir.mkdir(parents=True, exist_ok=True)
    cfg, small_target = _build_cfg(context, model_path, device)
    written: list[Path] = []

    for entry in _load_pack(context.pack_file):
        source = parse_video_source(_resolve_source(entry["source"]))
        source_name = Path(str(source)).stem if isinstance(source, str) else f"camera_{source}"
        output = preview_dir / f"{source_name}.mp4"
        try:
            run_tracker(
                cfg,
                source=source,
                output_path=str(output),
                no_display=True,
                max_frames=max(0, preview_frames),
                small_target_mode=small_target,
            )
        except Exception as exc:
            (preview_dir / f"{source_name}.error.txt").write_text(str(exc), encoding="utf-8")
            continue
        written.append(output)
    return written


def _failure_reasons(row: dict[str, Any], baseline_row: dict[str, Any] | None) -> list[str]:
    scene = str(row.get("scene", "unknown"))
    reasons = [r for r in str(row.get("fail_reasons", "")).split(";") if r]
    active_presence = float(row.get("active_presence_rate", 0.0))
    false_lock = float(row.get("false_lock_rate", 0.0))
    id_chg = float(row.get("active_id_changes_per_min", 0.0))
    fps = float(row.get("avg_fps", 0.0))
    gt_frames = int(row.get("gt_frames", 0))

    if gt_frames > 0 and active_presence <= 0.02:
        reasons.append("why:no_detection")
    elif gt_frames > 0 and active_presence < 0.08:
        reasons.append("why:low_presence")
    if gt_frames > 0 and false_lock > 0.55:
        reasons.append("why:false_lock")
    if id_chg > (18.0 if scene == "night" else 8.0):
        reasons.append("why:id_churn")
    if fps < 8.0:
        reasons.append("why:fps_regression")
    if scene == "ir":
        reasons.append("risk:ir_domain_gap")
    if scene == "night":
        reasons.append("risk:night_motion_gap")
    if gt_frames == 0:
        reasons.append("note:no_gt_false_lock_not_discriminator")

    if baseline_row is not None:
        base_presence = float(baseline_row.get("active_presence_rate", 0.0))
        base_false = float(baseline_row.get("false_lock_rate", 0.0))
        base_id = float(baseline_row.get("active_id_changes_per_min", 0.0))
        if active_presence < base_presence - 0.03:
            reasons.append("vs_baseline:presence_drop")
        if false_lock > base_false + 0.02:
            reasons.append("vs_baseline:false_lock_increase")
        if id_chg > base_id + 0.3:
            reasons.append("vs_baseline:id_churn_increase")

    deduped: list[str] = []
    for reason in reasons:
        if reason not in deduped:
            deduped.append(reason)
    return deduped


def _rows_by_source(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        source = str(row.get("source", ""))
        if not source:
            continue
        result[source] = row
        result[Path(source).name] = row
        result[Path(source).stem] = row
    return result


def _find_baseline(baseline_rows: dict[str, dict[str, Any]], source: str) -> dict[str, Any] | None:
    return baseline_rows.get(source) or baseline_rows.get(Path(source).name) or baseline_rows.get(Path(source).stem)


def _write_summary(
    *,
    out_dir: Path,
    records: list[dict[str, Any]],
    run_meta: dict[str, Any],
) -> None:
    summary_csv = out_dir / "summary.csv"
    headers = [
        "model",
        "context",
        "passed",
        "avg_fps",
        "active_presence_rate",
        "continuity_score",
        "active_id_changes_per_min",
        "false_lock_rate",
        "failures",
    ]
    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for record in records:
            writer.writerow({k: record.get(k, "") for k in headers})

    lines = [
        "# Model Battle",
        "",
        f"- generated: {run_meta['generated_at']}",
        f"- scope: {run_meta['scope']}",
        f"- max_frames: {run_meta['max_frames']}",
        f"- preview_frames: {run_meta['preview_frames']}",
        f"- models: {', '.join(run_meta['models'])}",
        f"- contexts: {', '.join(run_meta['contexts'])}",
        "",
        "## Summary",
        "",
        "| Model | Context | Pass | FPS | Presence | Continuity | ID chg/min | False lock |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for record in records:
        lines.append(
            "| {model} | {context} | {passed} | {avg_fps:.2f} | {active_presence_rate:.3f} | "
            "{continuity_score:.3f} | {active_id_changes_per_min:.2f} | {false_lock_rate:.3f} |".format(
                **record
            )
        )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_why_failed(out_dir: Path, failure_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Why Failed",
        "",
        "Heuristic explanation of candidate failures. Visual previews are in `previews/`.",
        "",
    ]
    if not failure_rows:
        lines.append("No failed rows.")
    else:
        lines.extend([
            "| Model | Context | Source | Reasons |",
            "|---|---|---|---|",
        ])
        for row in failure_rows:
            lines.append(
                f"| {row['model']} | {row['context']} | {row['source']} | {', '.join(row['reasons'])} |"
            )
    (out_dir / "why_failed.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    requested_models = [m.strip() for m in args.models.split(",") if m.strip()]
    requested_contexts = [c.strip() for c in args.contexts.split(",") if c.strip()]
    context_pool = CONTEXTS_SMOKE if args.scope == "smoke" else CONTEXTS_FULL
    contexts = [context_pool[name] for name in requested_contexts]

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_name = f"{args.tag}_{timestamp}" if args.tag else timestamp
    out_dir = (ROOT / args.out_dir / run_name).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    model_paths: dict[str, str] = {}
    model_labels: dict[str, str] = {}
    for model in requested_models:
        label = _safe_name(model)
        model_labels[model] = label
        try:
            model_paths[model] = _ensure_model_available(model)
        except Exception as exc:
            model_paths[model] = ""
            (out_dir / f"{label}.model_error.txt").write_text(str(exc), encoding="utf-8")
            print(f"[battle] model unavailable: {model}: {exc}")

    summary_records: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    baseline_by_context: dict[str, dict[str, dict[str, Any]]] = {}

    _valid_models = [m for m in requested_models if m == "baseline" or model_paths.get(m)]
    _total_steps = len(_valid_models) * len(contexts)
    _step = 0

    for model in requested_models:
        label = model_labels[model]
        model_path = model_paths[model]
        if model != "baseline" and not model_path:
            continue
        for context in contexts:
            _step += 1
            print(f"PROGRESS context={context.name} step={_step} total={_total_steps}", flush=True)
            context_dir = out_dir / "gates" / label / context.name
            context_dir.mkdir(parents=True, exist_ok=True)
            gate_code = _run_gate(
                _gate_cmd(
                    context=context,
                    model_label=label,
                    model_path=model_path,
                    out_dir=context_dir,
                    max_frames=int(args.max_frames),
                    device=args.device,
                )
            )
            data = _load_quality(_quality_json_path(label, context, context_dir))
            mean = data.get("mean", {})
            summary_records.append({
                "model": label,
                "context": context.name,
                "passed": bool(data.get("gate_passed", False)),
                "avg_fps": float(mean.get("avg_fps", 0.0)),
                "active_presence_rate": float(mean.get("active_presence_rate", 0.0)),
                "continuity_score": float(mean.get("continuity_score", 0.0)),
                "active_id_changes_per_min": float(mean.get("active_id_changes_per_min", 0.0)),
                "false_lock_rate": float(mean.get("false_lock_rate", 0.0)),
                "failures": "; ".join(data.get("failures", [])),
                "gate_exit_code": gate_code,
            })

            if label == "baseline":
                baseline_by_context[context.name] = _rows_by_source(data.get("rows", []))

            if not args.no_preview:
                print(f"[battle] preview model={label} context={context.name}", flush=True)
                _save_previews(
                    context=context,
                    model_label=label,
                    model_path=model_path,
                    out_dir=out_dir,
                    preview_frames=int(args.preview_frames),
                    device=args.device,
                )

            baseline_rows = baseline_by_context.get(context.name, {})
            for row in data.get("rows", []):
                if bool(row.get("passed", False)):
                    continue
                source = str(row.get("source", ""))
                failure_rows.append({
                    "model": label,
                    "context": context.name,
                    "source": Path(source).name if source else "",
                    "reasons": _failure_reasons(row, _find_baseline(baseline_rows, source)),
                })

    run_meta = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "scope": args.scope,
        "max_frames": int(args.max_frames),
        "preview_frames": int(args.preview_frames),
        "models": [model_labels[m] for m in requested_models],
        "contexts": [c.name for c in contexts],
    }
    (out_dir / "run_meta.json").write_text(json.dumps(run_meta, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_summary(out_dir=out_dir, records=summary_records, run_meta=run_meta)
    _write_why_failed(out_dir, failure_rows)

    print(f"[battle] out_dir={out_dir}")
    print(f"[battle] summary={out_dir / 'summary.md'}")
    print(f"[battle] why={out_dir / 'why_failed.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
