#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

import cv2

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_tracker.config import Config
from uav_tracker.modes import apply_runtime_mode
from uav_tracker.pipeline import TrackerPipeline, VideoSession, apply_runtime_preset, parse_video_source
from uav_tracker.profile_io import available_presets, load_preset
from utils.geometry import iou

try:
    from validate_tracking_gt import GtAnnotation, _expand_inputs, load_annotations, resolve_source, validate_paths
except ModuleNotFoundError:
    from python_scripts.validate_tracking_gt import GtAnnotation, _expand_inputs, load_annotations, resolve_source, validate_paths


def _percentile(values: list[float], p: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = max(0, math.ceil(p / 100 * len(ordered)) - 1)
    return ordered[min(idx, len(ordered) - 1)]


def _bbox_center(bbox: tuple[int, int, int, int]) -> tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def _bbox_area(bbox: tuple[int, int, int, int]) -> float:
    x1, y1, x2, y2 = bbox
    return float(max(0, x2 - x1) * max(0, y2 - y1))


def _resolve_cfg(preset: str, *, mode: str = "", device: str = "", model: str = "", imgsz: int = 0, conf: float = 0.0) -> tuple[Config, bool]:
    if preset not in set(available_presets()):
        raise ValueError(f"Unknown preset: {preset}")
    cfg = Config()
    cfg, preset_data = load_preset(preset, cfg)
    if mode:
        cfg = apply_runtime_mode(cfg, mode)
    if device:
        cfg.DEVICE = device
    small_target = bool(preset_data.get("small_target_mode", False))
    cfg = apply_runtime_preset(
        cfg,
        small_target_mode=small_target,
        imgsz=imgsz if imgsz > 0 else int(cfg.IMG_SIZE),
        conf=conf if conf > 0 else float(cfg.CONF_THRESH),
    )
    if model:
        cfg.MODEL_PATH = model
    return cfg, small_target


def _classify_scene(*parts: str) -> str:
    text = " ".join(parts).lower()
    normalized = text.replace("\\", "/")
    negative = any(token in text for token in ("bird", "airplane", "plane", "negative", "false"))
    if "infrared" in text or "_ir" in text or "ir_" in text or text.startswith("ir") or "/ir/" in normalized:
        return "IR_NEGATIVE" if negative else "IR"
    if "night" in text:
        return "NIGHT_NEGATIVE" if negative else "NIGHT"
    if "_eo" in text or " eo" in text or "rgb" in text or "day" in text or "/eo/" in normalized:
        return "EO_NEGATIVE" if negative else "EO"
    return "NEGATIVE" if negative else "UNKNOWN"


def _safe_stem(value: str) -> str:
    text = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value.strip())
    return text.strip("_")[:120] or "clip"


def _frame_outcome(
    annotation: GtAnnotation,
    active_bbox: tuple[int, int, int, int] | None,
) -> tuple[str, float | None]:
    if annotation.visible:
        if active_bbox is None:
            return "missed", None
        score = iou(active_bbox, annotation.bbox) if annotation.bbox else 0.0
        return ("matched" if score >= 0.10 else "off_target"), float(score)
    if active_bbox is not None:
        return "false_active", None
    return "clear_negative", None


def _draw_bbox(
    frame: Any,
    bbox: tuple[int, int, int, int] | None,
    *,
    color: tuple[int, int, int],
    label: str,
) -> None:
    if bbox is None:
        return
    x1, y1, x2, y2 = [int(v) for v in bbox]
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(
        frame,
        label,
        (x1, max(14, y1 - 6)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        color,
        1,
        cv2.LINE_AA,
    )


def _write_error_sample(
    frame: Any,
    *,
    out_dir: Path,
    clip: str,
    frame_index: int,
    outcome: str,
    source: str,
    gt_bbox: tuple[int, int, int, int] | None,
    active_bbox: tuple[int, int, int, int] | None,
    score: float | None,
) -> dict[str, Any]:
    clip_dir = out_dir / _safe_stem(clip)
    clip_dir.mkdir(parents=True, exist_ok=True)
    rel_path = Path(_safe_stem(clip)) / f"{int(frame_index):06d}_{outcome}.jpg"
    image = frame.copy()
    _draw_bbox(image, gt_bbox, color=(64, 210, 115), label="GT")
    _draw_bbox(image, active_bbox, color=(82, 108, 226), label=f"TRACK:{source}")
    caption = f"{outcome} frame={frame_index} source={source}"
    if score is not None:
        caption += f" iou={score:.2f}"
    cv2.putText(image, caption, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (235, 235, 235), 1, cv2.LINE_AA)
    cv2.imwrite(str(out_dir / rel_path), image)
    return {
        "file": rel_path.as_posix(),
        "clip": clip,
        "frame_index": int(frame_index),
        "outcome": outcome,
        "active_source": source,
        "iou": None if score is None else round(float(score), 4),
    }


def _run_clip(
    cfg: Config,
    source: str,
    annotations: list[GtAnnotation],
    *,
    small_target: bool,
    error_samples_dir: Path | None = None,
    max_error_samples_per_outcome: int = 0,
) -> dict[str, Any]:
    annotation_by_frame = {item.frame_index: item for item in annotations}
    max_frame = max(annotation_by_frame) if annotation_by_frame else 0
    session = VideoSession(cfg, parse_video_source(source), manage_cv_windows=False)
    session.open()
    pipeline = TrackerPipeline(cfg)

    sampled_frames = 0
    visible_gt = 0
    invisible_gt = 0
    matched_iou01 = 0
    matched_iou03 = 0
    false_lock = 0
    missed_visible = 0
    ious: list[float] = []
    fps_values: list[float] = []
    latency_values: list[float] = []
    center_errors: list[float] = []
    scale_ratios: list[float] = []
    center_steps: list[float] = []
    scale_steps: list[float] = []
    timings: dict[str, list[float]] = defaultdict(list)
    source_counts: Counter[str] = Counter()
    scan_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    # TASK-103a Diagnostic Pack v1: extra per-frame series.
    bbox_areas: list[int] = []
    scene_runtime_counts: Counter[str] = Counter()
    scene_confidence_values: list[float] = []
    proposal_counts: dict[str, list[int]] = defaultdict(list)
    proposal_seen: Counter[str] = Counter()
    error_sample_counts: Counter[str] = Counter()
    error_samples: list[dict[str, Any]] = []
    prev_bbox: tuple[int, int, int, int] | None = None
    prev_area: float | None = None
    last_result = None

    try:
        while True:
            ok, frame, meta = session.read()
            if not ok:
                break
            frame_index = int(meta.get("frame_index", 0))
            annotation = annotation_by_frame.get(frame_index)
            gt_bbox = annotation.bbox if annotation and annotation.visible else None
            result = pipeline.process_frame(
                frame,
                frame_index=frame_index,
                gt_bbox=gt_bbox,
                small_target_mode=small_target,
                render=False,
                source_fps=meta.get("source_fps"),
            )
            last_result = result

            if annotation is not None:
                sampled_frames += 1
                fps_values.append(float(result.fps))
                latency_values.append(float(result.budget_frame_ms))
                for key, value in result.timings_ms.items():
                    timings[key].append(float(value))
                source_counts[str(result.active_source)] += 1
                scan_counts[str(result.scan_strategy)] += 1
                mode_counts[str(result.mode)] += 1
                # TASK-103a Diagnostic Pack v1: capture diagnostic series.
                bbox_areas.append(int(getattr(result, "bbox_area", 0)))
                scene_runtime_counts[str(getattr(result, "scene_label_runtime", ""))] += 1
                scene_confidence_values.append(float(getattr(result, "scene_confidence_runtime", 1.0)))
                for src, cnt in (getattr(result, "proposal_count_by_source", {}) or {}).items():
                    proposal_counts[str(src)].append(int(cnt))
                    if int(cnt) > 0:
                        proposal_seen[str(src)] += 1

                # TASK-103b: use raw (pre-stabilization) bbox for recall/IoU so
                # the EMA size-smoother does not degrade measured accuracy.
                # active_bbox (stabilized) is kept for bbox_area telemetry only.
                active_bbox = result.active_bbox
                recall_bbox = getattr(result, "active_bbox_raw", None) or active_bbox
                outcome, outcome_iou = _frame_outcome(annotation, recall_bbox)
                if (
                    error_samples_dir is not None
                    and max_error_samples_per_outcome > 0
                    and outcome != "clear_negative"
                    and error_sample_counts[outcome] < max_error_samples_per_outcome
                ):
                    error_samples.append(
                        _write_error_sample(
                            frame,
                            out_dir=error_samples_dir,
                            clip=Path(source).stem,
                            frame_index=frame_index,
                            outcome=outcome,
                            source=str(result.active_source),
                            gt_bbox=annotation.bbox if annotation.visible else None,
                            active_bbox=active_bbox,
                            score=outcome_iou,
                        )
                    )
                    error_sample_counts[outcome] += 1
                if annotation.visible:
                    visible_gt += 1
                    if recall_bbox is None:
                        missed_visible += 1
                    else:
                        score = iou(recall_bbox, annotation.bbox) if annotation.bbox else 0.0
                        ious.append(float(score))
                        if score >= 0.10:
                            matched_iou01 += 1
                        else:
                            false_lock += 1
                        if score >= 0.30:
                            matched_iou03 += 1
                        if annotation.bbox:
                            acx, acy = _bbox_center(recall_bbox)
                            gcx, gcy = _bbox_center(annotation.bbox)
                            center_errors.append(((acx - gcx) ** 2 + (acy - gcy) ** 2) ** 0.5)
                            gt_area = max(1.0, _bbox_area(annotation.bbox))
                            scale_ratios.append(_bbox_area(recall_bbox) / gt_area)
                else:
                    invisible_gt += 1
                    if recall_bbox is not None:
                        false_lock += 1

                if recall_bbox is not None:
                    if prev_bbox is not None:
                        pcx, pcy = _bbox_center(prev_bbox)
                        acx, acy = _bbox_center(recall_bbox)
                        center_steps.append(((acx - pcx) ** 2 + (acy - pcy) ** 2) ** 0.5)
                    area = _bbox_area(recall_bbox)
                    if prev_area is not None and prev_area > 0:
                        scale_steps.append(abs(area / prev_area - 1.0))
                    prev_bbox = recall_bbox
                    prev_area = area

            if frame_index >= max_frame:
                break
    finally:
        session.close()

    safe_sampled = max(1, sampled_frames)
    safe_visible = max(1, visible_gt)
    avg_stage_ms = {key: mean(values) if values else 0.0 for key, values in timings.items()}
    # TASK-103a Diagnostic Pack v1 aggregates.
    stage_ms_p50 = {key: _percentile(values, 50) for key, values in timings.items()}
    stage_ms_p95 = {key: _percentile(values, 95) for key, values in timings.items()}
    stage_ms_p99 = {key: _percentile(values, 99) for key, values in timings.items()}
    _bbox_positive = [a for a in bbox_areas if a > 0]
    if len(_bbox_positive) >= 2:
        _bbox_mean = mean(_bbox_positive)
        _bbox_var = sum((a - _bbox_mean) ** 2 for a in _bbox_positive) / len(_bbox_positive)
        bbox_area_cv = (_bbox_var ** 0.5) / _bbox_mean if _bbox_mean > 0 else 0.0
    else:
        bbox_area_cv = 0.0
    proposal_mean = {key: (mean(values) if values else 0.0) for key, values in proposal_counts.items()}
    proposal_seen_rate = {key: (cnt / safe_sampled) for key, cnt in proposal_seen.items()}
    scene_confidence_avg = mean(scene_confidence_values) if scene_confidence_values else 0.0
    return {
        "source": source,
        "clip": Path(source).stem,
        "sampled_frames": sampled_frames,
        "visible_gt_frames": visible_gt,
        "invisible_gt_frames": invisible_gt,
        "active_bbox_frames": matched_iou01 + false_lock,
        "matched_iou01_frames": matched_iou01,
        "false_lock_frames": false_lock,
        "missed_visible_frames": missed_visible,
        "recall_iou_01": matched_iou01 / safe_visible,
        "recall_iou_03": matched_iou03 / safe_visible,
        "missed_visible_rate": missed_visible / safe_visible,
        "false_lock_rate_sampled": false_lock / safe_sampled,
        "avg_iou_visible": mean(ious) if ious else 0.0,
        "median_iou_visible": median(ious) if ious else 0.0,
        "center_error_p95": _percentile(center_errors, 95),
        "scale_ratio_p95": _percentile(scale_ratios, 95),
        "bbox_center_step_p95": _percentile(center_steps, 95),
        "bbox_scale_step_p95": _percentile(scale_steps, 95),
        "avg_fps": mean(fps_values) if fps_values else 0.0,
        "latency_p95_ms": _percentile(latency_values, 95),
        "latency_p99_ms": _percentile(latency_values, 99),
        "avg_stage_ms": avg_stage_ms,
        "source_counts": dict(source_counts),
        "scan_counts": dict(scan_counts),
        "mode_counts": dict(mode_counts),
        "error_samples": error_samples,
        "active_id_changes": int(getattr(last_result, "active_id_changes", 0)) if last_result else 0,
        "active_id_changes_per_min": float(getattr(last_result, "active_id_changes_per_min", 0.0)) if last_result else 0.0,
        "continuity_score": float(getattr(last_result, "continuity_score", 0.0)) if last_result else 0.0,
        "active_presence_rate": float(getattr(last_result, "active_presence_rate", 0.0)) if last_result else 0.0,
        # TASK-103a Diagnostic Pack v1.
        "stage_ms_p50": stage_ms_p50,
        "stage_ms_p95": stage_ms_p95,
        "stage_ms_p99": stage_ms_p99,
        "bbox_area_cv": bbox_area_cv,
        "scene_runtime_counts": dict(scene_runtime_counts),
        "scene_confidence_avg": scene_confidence_avg,
        "proposal_mean_by_source": proposal_mean,
        "proposal_seen_rate_by_source": proposal_seen_rate,
    }


def build_report(rows: list[dict[str, Any]], validation: dict[str, Any]) -> dict[str, Any]:
    risks: list[str] = []
    for row in rows:
        if row["false_lock_rate_sampled"] > 0.35:
            risks.append(f"{row['clip']}: tracker off target on GT sample")
        if row["recall_iou_01"] < 0.65 and row["visible_gt_frames"] > 0:
            risks.append(f"{row['clip']}: low recall")
        if (row.get("latency_p99_ms") or 0) > 120:
            risks.append(f"{row['clip']}: high latency p99")
        if (row.get("bbox_scale_step_p95") or 0) > 0.60:
            risks.append(f"{row['clip']}: bbox scale jitter")
    # TASK-103a Diagnostic Pack v1: scene confusion gt_scene → runtime_scene_top.
    scene_confusion: dict[str, dict[str, int]] = {}
    for row in rows:
        gt_scene = str(row.get("scene", "UNKNOWN"))
        rt_counts = row.get("scene_runtime_counts") or {}
        if not rt_counts:
            continue
        sub = scene_confusion.setdefault(gt_scene, {})
        for rt_scene, cnt in rt_counts.items():
            sub[str(rt_scene)] = sub.get(str(rt_scene), 0) + int(cnt)
    return {
        "report_type": "tracking_gt_diagnostics",
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "validation": validation,
        "rows": rows,
        "risks": risks,
        "scene_confusion": scene_confusion,
    }


def _source_scene_map(paths: list[Path]) -> dict[str, str]:
    scenes: dict[str, str] = {}
    for path in paths:
        for annotation in load_annotations([path]):
            scenes.setdefault(annotation.source, _classify_scene(path.name, annotation.source))
    return scenes


def run_diagnostics(
    inputs: list[Path],
    *,
    preset: str = "antiuav_thermal",
    mode: str = "",
    device: str = "",
    model: str = "",
    imgsz: int = 0,
    conf: float = 0.0,
    scene_aware: bool = False,
    error_samples_dir: Path | None = None,
    max_error_samples_per_outcome: int = 0,
) -> list[dict[str, Any]]:
    paths = _expand_inputs(inputs)
    annotations = load_annotations(paths)
    source_scenes = _source_scene_map(paths) if scene_aware else {}
    by_source: dict[str, list[GtAnnotation]] = defaultdict(list)
    for item in annotations:
        by_source[item.source].append(item)

    cfg_cache: dict[str, tuple[Config, bool]] = {}
    rows = []
    for source, items in by_source.items():
        resolved = resolve_source(source)
        if resolved is None:
            continue
        scene = source_scenes.get(source, _classify_scene(source))
        selected_preset = preset
        if selected_preset not in cfg_cache:
            cfg_cache[selected_preset] = _resolve_cfg(
                selected_preset,
                mode=mode,
                device=device,
                model=model,
                imgsz=imgsz,
                conf=conf,
            )
        cfg, small_target = cfg_cache[selected_preset]
        print(
            f"[tracking-gt] {Path(source).name} rows={len(items)} scene={scene} preset={selected_preset}",
            flush=True,
        )
        row = _run_clip(
            cfg,
            str(resolved),
            sorted(items, key=lambda x: x.frame_index),
            small_target=small_target,
            error_samples_dir=error_samples_dir,
            max_error_samples_per_outcome=max_error_samples_per_outcome,
        )
        row["scene"] = scene
        row["preset"] = selected_preset
        rows.append(row)
    return rows


def write_outputs(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    headers = [
        "clip", "scene", "preset", "sampled_frames", "visible_gt_frames", "invisible_gt_frames",
        "active_bbox_frames", "matched_iou01_frames", "false_lock_frames", "missed_visible_frames",
        "recall_iou_01", "recall_iou_03", "missed_visible_rate", "false_lock_rate_sampled",
        "avg_iou_visible", "bbox_center_step_p95", "bbox_scale_step_p95",
        "avg_fps", "latency_p95_ms", "latency_p99_ms", "active_id_changes_per_min",
        "continuity_score", "active_presence_rate",
        # TASK-103a Diagnostic Pack v1.
        "bbox_area_cv", "scene_confidence_avg",
        "stage_yolo_p99_ms", "stage_lock_p99_ms", "stage_local_p99_ms",
        "stage_roi_p99_ms", "stage_night_p99_ms", "stage_manager_p99_ms",
        "stage_draw_p99_ms", "stage_total_p99_ms",
    ]
    def _flatten_row(row: dict[str, Any]) -> dict[str, Any]:
        out = {key: row.get(key, "") for key in headers}
        stage_p99 = row.get("stage_ms_p99") or {}
        out["stage_yolo_p99_ms"] = stage_p99.get("global", 0.0)
        out["stage_lock_p99_ms"] = stage_p99.get("lock", 0.0)
        out["stage_local_p99_ms"] = stage_p99.get("local", 0.0)
        out["stage_roi_p99_ms"] = stage_p99.get("roi", 0.0)
        out["stage_night_p99_ms"] = stage_p99.get("night", 0.0)
        out["stage_manager_p99_ms"] = stage_p99.get("manager", 0.0)
        out["stage_draw_p99_ms"] = stage_p99.get("draw", 0.0)
        out["stage_total_p99_ms"] = stage_p99.get("total", 0.0)
        return out
    with (out_dir / "summary.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow(_flatten_row(row))

    lines = ["# Tracking GT Diagnostics", ""]
    lines.append(f"Generated: `{report['generated_at']}`")
    lines.append("")
    lines.append("> Off target means the tracker bbox did not overlap the GT bbox; it does not mean the GT annotation is false.")
    lines.append("")
    lines.append("| Clip | Scene | Preset | Frames | Matched | Missed | Off target | Recall@0.1 | FPS | p99 ms | BBox scale p95 |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in report["rows"]:
        lines.append(
            f"| {row['clip']} | {row.get('scene', '')} | {row.get('preset', '')} | {row['sampled_frames']} | {row.get('matched_iou01_frames', '')} | "
            f"{row.get('missed_visible_frames', '')} | {row.get('false_lock_frames', '')} | "
            f"{row['recall_iou_01']:.3f} | {row['avg_fps']:.1f} | "
            f"{row.get('latency_p99_ms') or 0:.1f} | {row.get('bbox_scale_step_p95') or 0:.3f} |"
        )
    lines.append("")
    lines.append("## Risks")
    if report["risks"]:
        lines.extend(f"- {risk}" for risk in report["risks"])
    else:
        lines.append("- No immediate diagnostic risk")
    sample_rows = [
        sample
        for row in report["rows"]
        for sample in row.get("error_samples", [])
        if isinstance(sample, dict)
    ]
    if sample_rows:
        lines.append("")
        lines.append("## Visual Samples")
        lines.append("")
        lines.append("| Clip | Frame | Outcome | Source | Image |")
        lines.append("|---|---:|---|---|---|")
        for sample in sample_rows[:80]:
            file_path = str(sample.get("file", ""))
            lines.append(
                f"| {sample.get('clip', '')} | {sample.get('frame_index', '')} | "
                f"{sample.get('outcome', '')} | {sample.get('active_source', '')} | "
                f"[jpg](errors/{file_path}) |"
            )
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run current tracker against GT Assist CSV files.")
    parser.add_argument("inputs", nargs="+", type=Path, help="GT CSV file(s) or directories.")
    parser.add_argument("--preset", default="antiuav_thermal")
    parser.add_argument("--mode", default="")
    parser.add_argument("--device", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--imgsz", type=int, default=0)
    parser.add_argument("--conf", type=float, default=0.0)
    parser.add_argument("--scene-aware", action="store_true", help="Choose preset per GT scene: IR, EO, night.")
    parser.add_argument("--render-errors", action="store_true", help="Write visual matched/missed/off-target frame samples.")
    parser.add_argument("--max-error-samples", type=int, default=5, help="Max samples per outcome per clip.")
    parser.add_argument("--out-dir", type=Path, default=Path("runs/evaluations/tracking_gt_diagnostics"))
    parser.add_argument("--tag", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = _expand_inputs(args.inputs)
    validation_summary = validate_paths(paths)
    if validation_summary.errors or validation_summary.invalid_count or validation_summary.duplicate_count:
        print(json.dumps(asdict(validation_summary), indent=2, ensure_ascii=False))
        return 2

    stamp = time.strftime("%Y%m%d_%H%M%S")
    tag = f"{args.tag}_" if args.tag else ""
    out_dir = (ROOT / args.out_dir / f"{tag}{stamp}").resolve()
    rows = run_diagnostics(
        paths,
        preset=args.preset,
        mode=args.mode,
        device=args.device,
        model=args.model,
        imgsz=args.imgsz,
        conf=args.conf,
        scene_aware=args.scene_aware,
        error_samples_dir=(out_dir / "errors") if args.render_errors else None,
        max_error_samples_per_outcome=max(0, int(args.max_error_samples)),
    )

    report = build_report(rows, asdict(validation_summary))
    write_outputs(report, out_dir)
    print(f"[tracking-gt] out_dir={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
