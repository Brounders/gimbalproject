#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import cv2


SampleKind = Literal["drone_positive", "hard_negative_class", "background_negative"]


@dataclass(frozen=True)
class GtSample:
    source: str
    frame_index: int
    visible: bool
    bbox: tuple[int, int, int, int] | None
    kind: SampleKind
    class_id: int | None
    group: str
    gt_file: str


@dataclass
class PackRecord:
    record_id: str
    status: str
    split: str = ""
    sample_kind: str = ""
    group: str = ""
    source: str = ""
    frame_index: int = 0
    image_path: str = ""
    label_path: str = ""
    reason: str = ""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a YOLO pack from Target Lab GT CSV files.")
    p.add_argument("--positive-gt", nargs="+", type=Path, required=True, help="Drone-positive GT CSV files.")
    p.add_argument("--negative-gt", nargs="*", type=Path, default=[], help="Hard negative GT CSV files.")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--positive-sample-step", type=int, default=5)
    p.add_argument("--negative-sample-step", type=int, default=12)
    p.add_argument("--background-sample-step", type=int, default=25)
    p.add_argument("--max-positive-per-source", type=int, default=180)
    p.add_argument("--max-negative-per-source", type=int, default=80)
    p.add_argument("--max-background-per-source", type=int, default=30)
    p.add_argument("--val-ratio", type=float, default=0.2)
    p.add_argument("--seed", type=str, default="weak4_103h_20260517")
    return p.parse_args()


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _bbox(row: dict[str, str]) -> tuple[int, int, int, int] | None:
    try:
        vals = [row.get(k, "") for k in ("x1", "y1", "x2", "y2")]
        if any(str(v).strip() == "" for v in vals):
            return None
        x1, y1, x2, y2 = [int(float(v)) for v in vals]
    except ValueError:
        return None
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _split(record_id: str, val_ratio: float, seed: str) -> str:
    digest = hashlib.sha1(f"{seed}:{record_id}".encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    return "val" if bucket < val_ratio else "train"


def _safe_stem(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in Path(value).stem)[:90]


def _group_for_positive(path: Path) -> str:
    name = path.name.lower()
    if "9_dji2" in name or "200805" in name:
        return "yolo_absent_thermal_positive"
    if "1_minie3" in name or "205804" in name:
        return "yolo_low_conf_positive"
    return "drone_positive"


def _group_for_negative(path: Path) -> str:
    name = path.name.lower()
    if "airplane" in name:
        return "ir_airplane_hard_negative"
    if "bird" in name or "birds" in name:
        return "bird_hard_negative"
    return "hard_negative"


def _sample_csv(
    path: Path,
    *,
    kind: SampleKind,
    class_id: int | None,
    group: str,
    sample_step: int,
    max_visible: int,
    background_step: int = 0,
    max_background: int = 0,
) -> list[GtSample]:
    samples: list[GtSample] = []
    visible_seen_by_source: dict[str, int] = {}
    selected_visible_by_source: dict[str, int] = {}
    invisible_seen_by_source: dict[str, int] = {}
    selected_background_by_source: dict[str, int] = {}

    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            source = str(row.get("source", "")).strip()
            if not source:
                continue
            frame_index = int(float(row.get("frame_index", "0") or 0))
            visible = _truthy(row.get("visible", ""))
            if visible:
                visible_seen_by_source[source] = visible_seen_by_source.get(source, 0) + 1
                if visible_seen_by_source[source] % max(1, sample_step) != 1:
                    continue
                if selected_visible_by_source.get(source, 0) >= max_visible:
                    continue
                bbox = _bbox(row)
                if bbox is None:
                    continue
                selected_visible_by_source[source] = selected_visible_by_source.get(source, 0) + 1
                samples.append(GtSample(source, frame_index, True, bbox, kind, class_id, group, str(path)))
            elif background_step > 0 and max_background > 0:
                invisible_seen_by_source[source] = invisible_seen_by_source.get(source, 0) + 1
                if invisible_seen_by_source[source] % background_step != 1:
                    continue
                if selected_background_by_source.get(source, 0) >= max_background:
                    continue
                selected_background_by_source[source] = selected_background_by_source.get(source, 0) + 1
                samples.append(
                    GtSample(
                        source,
                        frame_index,
                        False,
                        None,
                        "background_negative",
                        None,
                        "invisible_background_negative",
                        str(path),
                    )
                )
    return samples


def _xyxy_to_yolo(
    bbox: tuple[int, int, int, int], frame_w: int, frame_h: int
) -> tuple[float, float, float, float] | None:
    x1, y1, x2, y2 = bbox
    if frame_w <= 0 or frame_h <= 0:
        return None
    x1 = max(0, min(frame_w - 1, x1))
    x2 = max(0, min(frame_w, x2))
    y1 = max(0, min(frame_h - 1, y1))
    y2 = max(0, min(frame_h, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    cx = (x1 + x2) / 2.0 / frame_w
    cy = (y1 + y2) / 2.0 / frame_h
    w = (x2 - x1) / frame_w
    h = (y2 - y1) / frame_h
    if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
        return None
    return cx, cy, w, h


def build_pack(args: argparse.Namespace) -> dict[str, object]:
    if not (0.0 <= float(args.val_ratio) < 1.0):
        raise ValueError("--val-ratio must be in [0, 1)")

    samples: list[GtSample] = []
    for path in args.positive_gt:
        samples.extend(
            _sample_csv(
                path,
                kind="drone_positive",
                class_id=0,
                group=_group_for_positive(path),
                sample_step=max(1, args.positive_sample_step),
                max_visible=max(1, args.max_positive_per_source),
                background_step=max(0, args.background_sample_step),
                max_background=max(0, args.max_background_per_source),
            )
        )
    for path in args.negative_gt:
        samples.extend(
            _sample_csv(
                path,
                kind="hard_negative_class",
                class_id=1,
                group=_group_for_negative(path),
                sample_step=max(1, args.negative_sample_step),
                max_visible=max(1, args.max_negative_per_source),
            )
        )

    for split in ("train", "val"):
        (args.out_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (args.out_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    records: list[PackRecord] = []
    caps: dict[str, cv2.VideoCapture] = {}
    try:
        for sample in samples:
            source_path = Path(sample.source)
            record_id = f"{_safe_stem(sample.source)}__f{sample.frame_index:06d}__{sample.kind}"
            if not source_path.exists():
                records.append(
                    PackRecord(
                        record_id=record_id,
                        status="skipped_source",
                        sample_kind=sample.kind,
                        group=sample.group,
                        source=sample.source,
                        frame_index=sample.frame_index,
                        reason=f"missing source {sample.source}",
                    )
                )
                continue
            cap = caps.get(sample.source)
            if cap is None:
                cap = cv2.VideoCapture(str(source_path))
                caps[sample.source] = cap
            if not cap.isOpened():
                records.append(
                    PackRecord(
                        record_id=record_id,
                        status="skipped_source",
                        sample_kind=sample.kind,
                        group=sample.group,
                        source=sample.source,
                        frame_index=sample.frame_index,
                        reason="cannot open source",
                    )
                )
                continue
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, sample.frame_index))
            ok, frame = cap.read()
            if not ok or frame is None:
                records.append(
                    PackRecord(
                        record_id=record_id,
                        status="skipped_frame",
                        sample_kind=sample.kind,
                        group=sample.group,
                        source=sample.source,
                        frame_index=sample.frame_index,
                        reason="cannot read frame",
                    )
                )
                continue
            frame_h, frame_w = frame.shape[:2]
            split = _split(record_id, float(args.val_ratio), str(args.seed))
            image_path = args.out_dir / "images" / split / f"{record_id}.jpg"
            label_path = args.out_dir / "labels" / split / f"{record_id}.txt"
            if sample.kind == "background_negative":
                label_text = ""
            else:
                if sample.bbox is None or sample.class_id is None:
                    records.append(
                        PackRecord(
                            record_id=record_id,
                            status="skipped_invalid",
                            sample_kind=sample.kind,
                            group=sample.group,
                            source=sample.source,
                            frame_index=sample.frame_index,
                            reason="missing bbox/class",
                        )
                    )
                    continue
                yolo = _xyxy_to_yolo(sample.bbox, frame_w, frame_h)
                if yolo is None:
                    records.append(
                        PackRecord(
                            record_id=record_id,
                            status="skipped_invalid",
                            sample_kind=sample.kind,
                            group=sample.group,
                            source=sample.source,
                            frame_index=sample.frame_index,
                            reason="bbox outside frame",
                        )
                    )
                    continue
                cx, cy, w, h = yolo
                label_text = f"{sample.class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n"
            cv2.imwrite(str(image_path), frame)
            label_path.write_text(label_text, encoding="utf-8")
            records.append(
                PackRecord(
                    record_id=record_id,
                    status="ok",
                    split=split,
                    sample_kind=sample.kind,
                    group=sample.group,
                    source=sample.source,
                    frame_index=sample.frame_index,
                    image_path=str(image_path),
                    label_path=str(label_path),
                )
            )
    finally:
        for cap in caps.values():
            cap.release()

    ok_records = [record for record in records if record.status == "ok"]
    counts: dict[str, int] = {
        "ok": len(ok_records),
        "train": sum(1 for record in ok_records if record.split == "train"),
        "val": sum(1 for record in ok_records if record.split == "val"),
        "drone_positive": sum(1 for record in ok_records if record.sample_kind == "drone_positive"),
        "hard_negative_class": sum(1 for record in ok_records if record.sample_kind == "hard_negative_class"),
        "background_negative": sum(1 for record in ok_records if record.sample_kind == "background_negative"),
        "skipped_source": sum(1 for record in records if record.status == "skipped_source"),
        "skipped_frame": sum(1 for record in records if record.status == "skipped_frame"),
        "skipped_invalid": sum(1 for record in records if record.status == "skipped_invalid"),
    }
    groups: dict[str, int] = {}
    for record in ok_records:
        groups[record.group] = groups.get(record.group, 0) + 1

    manifest = {
        "output_dir": str(args.out_dir),
        "purpose": "TASK-20260517-104 weak4 targeted detector training preparation",
        "class_map": {"0": "drone", "1": "non_drone_flyer"},
        "counts": counts,
        "groups": groups,
        "positive_gt": [str(path) for path in args.positive_gt],
        "negative_gt": [str(path) for path in args.negative_gt],
        "records": [asdict(record) for record in records],
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    with (args.out_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(asdict(PackRecord(record_id="", status="")).keys()))
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))
    data_yaml = "\n".join(
        [
            f"path: {args.out_dir.resolve()}",
            "train: images/train",
            "val: images/val",
            "nc: 2",
            "names:",
            "  0: drone",
            "  1: non_drone_flyer",
            "",
        ]
    )
    (args.out_dir / "data.yaml").write_text(data_yaml, encoding="utf-8")
    report_lines = [
        "# GT YOLO Pack",
        "",
        f"Output: `{args.out_dir}`",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    for key, value in counts.items():
        report_lines.append(f"| `{key}` | {value} |")
    report_lines.extend(["", "| Group | Count |", "|---|---:|"])
    for key, value in sorted(groups.items()):
        report_lines.append(f"| `{key}` | {value} |")
    (args.out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    args = parse_args()
    manifest = build_pack(args)
    print(json.dumps({"counts": manifest["counts"], "groups": manifest["groups"]}, indent=2, ensure_ascii=False))
    print(f"[gt-yolo-pack] {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
