#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".mts", ".m4v"}
LABEL_EXTS = {".txt", ".xml", ".json"}
ARCHIVE_EXTS = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".xz"}
IGNORE_NAMES = {".ds_store", "thumbs.db"}
READY_DATASET_NAMES = {"dataset.yaml", "data.yaml"}
ACTIVE_DATASET_STATUSES = {"new", "queued", "in_progress"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return value or "dataset"


def scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.lower() in IGNORE_NAMES:
            continue
        files.append(path)
    return files


def compute_fingerprint(root: Path, files: list[Path]) -> str:
    digest = hashlib.sha256()
    digest.update(str(root.resolve()).encode("utf-8"))
    for file_path in files:
        stat = file_path.stat()
        rel = file_path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(str(stat.st_size).encode("utf-8"))
        digest.update(str(int(stat.st_mtime)).encode("utf-8"))
    return digest.hexdigest()[:24]


def infer_scene_profile(name: str) -> str:
    lower = name.lower()
    if any(token in lower for token in ("ir", "thermal", "rgbt")):
        return "ir"
    if any(token in lower for token in ("night", "dark", "noct")):
        return "night"
    if any(token in lower for token in ("day", "visdrone", "visible")):
        return "day"
    return "mixed"


def infer_class_profile(name: str) -> str:
    lower = name.lower()
    has_drone = any(token in lower for token in ("drone", "uav", "antiuav"))
    has_bird = "bird" in lower
    if has_drone and has_bird:
        return "drone_bird"
    if has_drone:
        return "drone"
    if has_bird:
        return "bird"
    return "unknown"


def priority_for(scene_profile: str, class_profile: str) -> int:
    score = {
        "ir": 100,
        "night": 90,
        "mixed": 60,
        "day": 40,
    }.get(scene_profile, 50)
    if class_profile in {"drone", "drone_bird"}:
        score += 20
    return score


def suggest_budget(image_count: int, video_count: int, scene_profile: str) -> int:
    effective_units = image_count + video_count * 200
    if effective_units < 2_000:
        budget = 24
    elif effective_units < 10_000:
        budget = 48
    elif effective_units < 30_000:
        budget = 96
    else:
        budget = 144
    if scene_profile in {"ir", "night"}:
        budget += 12
    return budget


def find_dataset_yaml(root: Path) -> Path | None:
    direct = [root / name for name in READY_DATASET_NAMES]
    for path in direct:
        if path.exists():
            return path
    for candidate in sorted(root.rglob("dataset.yaml")):
        if candidate.is_file():
            return candidate
    for candidate in sorted(root.rglob("data.yaml")):
        if candidate.is_file():
            return candidate
    return None


@dataclass
class DatasetSummary:
    dataset_id: str
    dataset_name: str
    dataset_path: str
    dataset_type: str
    dataset_yaml_path: str | None
    fingerprint: str
    scene_profile: str
    class_profile: str
    priority: int
    status: str
    ready_for_training: bool
    total_files: int
    image_files: int
    video_files: int
    label_files: int
    total_bytes: int
    latest_mtime: str | None
    epoch_budget_total: int


class ConveyorState:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.registry_path = state_dir / "dataset_registry.json"
        self.ledger_path = state_dir / "training_ledger.json"
        self.manifest_path = state_dir / "artifact_manifest.json"
        self.decisions_path = state_dir / "decision_log.json"

        self.registry = load_json(self.registry_path, {"version": 1, "updated_at": None, "dataset_root": None, "datasets": []})
        self.ledger = load_json(self.ledger_path, {"version": 1, "updated_at": None, "entries": []})
        self.manifest = load_json(self.manifest_path, {"version": 1, "updated_at": None, "artifacts": []})
        self.decisions = load_json(self.decisions_path, {"version": 1, "updated_at": None, "decisions": []})

    def save(self) -> None:
        self.registry["updated_at"] = utc_now()
        self.ledger["updated_at"] = utc_now()
        self.manifest["updated_at"] = utc_now()
        self.decisions["updated_at"] = utc_now()
        save_json(self.registry_path, self.registry)
        save_json(self.ledger_path, self.ledger)
        save_json(self.manifest_path, self.manifest)
        save_json(self.decisions_path, self.decisions)

    def registry_index(self) -> dict[str, dict[str, Any]]:
        return {entry["dataset_id"]: entry for entry in self.registry.get("datasets", [])}

    def ledger_index(self) -> dict[str, dict[str, Any]]:
        return {entry["dataset_id"]: entry for entry in self.ledger.get("entries", [])}


def init_state(state: ConveyorState, force: bool) -> dict[str, Any]:
    if force:
        state.registry = {"version": 1, "updated_at": None, "dataset_root": None, "datasets": []}
        state.ledger = {"version": 1, "updated_at": None, "entries": []}
        state.manifest = {"version": 1, "updated_at": None, "artifacts": []}
        state.decisions = {"version": 1, "updated_at": None, "decisions": []}
    state.save()
    return {
        "status": "ok",
        "state_dir": str(state.state_dir),
        "files": [
            str(state.registry_path),
            str(state.ledger_path),
            str(state.manifest_path),
            str(state.decisions_path),
        ],
    }


def analyze_dataset(entry: Path) -> DatasetSummary:
    dataset_name = entry.name
    dataset_id = slugify(dataset_name)
    scene_profile = infer_scene_profile(dataset_name)
    class_profile = infer_class_profile(dataset_name)

    if entry.is_file() and entry.suffix.lower() in ARCHIVE_EXTS:
        stat = entry.stat()
        fingerprint = hashlib.sha256(f"{entry.name}:{stat.st_size}:{int(stat.st_mtime)}".encode("utf-8")).hexdigest()[:24]
        return DatasetSummary(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            dataset_path=str(entry.resolve()),
            dataset_type="archive",
            dataset_yaml_path=None,
            fingerprint=fingerprint,
            scene_profile=scene_profile,
            class_profile=class_profile,
            priority=priority_for(scene_profile, class_profile),
            status="blocked_archive",
            ready_for_training=False,
            total_files=1,
            image_files=0,
            video_files=0,
            label_files=0,
            total_bytes=stat.st_size,
            latest_mtime=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            epoch_budget_total=0,
        )

    files = scan_files(entry)
    image_files = sum(1 for path in files if path.suffix.lower() in IMAGE_EXTS)
    video_files = sum(1 for path in files if path.suffix.lower() in VIDEO_EXTS)
    label_files = sum(1 for path in files if path.suffix.lower() in LABEL_EXTS)
    total_bytes = sum(path.stat().st_size for path in files)
    latest_mtime_ts = max((path.stat().st_mtime for path in files), default=entry.stat().st_mtime)
    dataset_yaml = find_dataset_yaml(entry)
    ready = dataset_yaml is not None
    status = "queued" if ready else "blocked_no_dataset_yaml"
    return DatasetSummary(
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        dataset_path=str(entry.resolve()),
        dataset_type="directory",
        dataset_yaml_path=str(dataset_yaml.resolve()) if dataset_yaml else None,
        fingerprint=compute_fingerprint(entry, files),
        scene_profile=scene_profile,
        class_profile=class_profile,
        priority=priority_for(scene_profile, class_profile),
        status=status,
        ready_for_training=ready,
        total_files=len(files),
        image_files=image_files,
        video_files=video_files,
        label_files=label_files,
        total_bytes=total_bytes,
        latest_mtime=datetime.fromtimestamp(latest_mtime_ts, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        epoch_budget_total=suggest_budget(image_files, video_files, scene_profile) if ready else 0,
    )


def scan_datasets(state: ConveyorState, dataset_root: Path) -> dict[str, Any]:
    if not dataset_root.exists():
        raise FileNotFoundError(f"dataset root not found: {dataset_root}")
    existing = state.registry_index()
    existing_ledger = state.ledger_index()
    datasets: list[dict[str, Any]] = []
    new_count = 0
    changed_count = 0
    blocked_count = 0
    for child in sorted(dataset_root.iterdir()):
        if child.name.startswith("."):
            continue
        summary = analyze_dataset(child)
        prior = existing.get(summary.dataset_id)
        if prior is None:
            new_count += 1
        elif prior.get("fingerprint") != summary.fingerprint:
            changed_count += 1
        if not summary.ready_for_training:
            blocked_count += 1
        ledger_entry = existing_ledger.get(summary.dataset_id)
        persisted_status = prior.get("status") if prior else None
        if ledger_entry and ledger_entry.get("status") == "exhausted":
            status = "exhausted"
        elif persisted_status in {"queued", "in_progress", "exhausted"} and prior and prior.get("fingerprint") == summary.fingerprint:
            status = persisted_status
        else:
            status = summary.status
        datasets.append(
            {
                **summary.__dict__,
                "status": status,
                "last_seen_at": utc_now(),
                "notes": prior.get("notes", "") if prior else "",
            }
        )
    state.registry["dataset_root"] = str(dataset_root.resolve())
    state.registry["datasets"] = datasets
    state.save()
    return {
        "status": "ok",
        "dataset_root": str(dataset_root.resolve()),
        "dataset_count": len(datasets),
        "new_count": new_count,
        "changed_count": changed_count,
        "blocked_count": blocked_count,
        "ready_count": sum(1 for item in datasets if item.get("ready_for_training")),
    }


def next_chunk(state: ConveyorState, base_checkpoint: str, chunk_epochs: int, write_plan: Path | None, claim: bool, dataset_id: str | None) -> dict[str, Any]:
    datasets = state.registry.get("datasets", [])
    ledger_map = state.ledger_index()
    eligible: list[dict[str, Any]] = []
    for item in datasets:
        if dataset_id and item.get("dataset_id") != dataset_id:
            continue
        if item.get("status") not in ACTIVE_DATASET_STATUSES:
            continue
        if not item.get("ready_for_training"):
            continue
        ledger_entry = ledger_map.get(item["dataset_id"], {})
        epochs_done = int(ledger_entry.get("epochs_done_total", 0))
        budget = int(item.get("epoch_budget_total", 0))
        remaining = max(0, budget - epochs_done)
        if remaining <= 0:
            item["status"] = "exhausted"
            continue
        eligible.append({
            **item,
            "epochs_done_total": epochs_done,
            "remaining_epochs": remaining,
            "last_checkpoint": ledger_entry.get("last_checkpoint"),
            "last_run_name": ledger_entry.get("last_run_name"),
            "last_decision": ledger_entry.get("last_decision"),
        })
    if not eligible:
        state.save()
        return {"status": "empty", "reason": "no eligible dataset", "dataset_id": dataset_id}

    eligible.sort(key=lambda item: (-int(item.get("priority", 0)), int(item.get("epochs_done_total", 0)), item.get("dataset_name", "")))
    chosen = eligible[0]
    next_epochs = min(max(1, int(chunk_epochs)), int(chosen["remaining_epochs"]))
    epochs_done = int(chosen["epochs_done_total"])
    target_total_epochs = epochs_done + next_epochs
    checkpoint = chosen.get("last_checkpoint") or base_checkpoint
    run_name = chosen.get("last_run_name") or f"curriculum_{chosen['dataset_id']}"
    plan = {
        "status": "ok",
        "dataset_id": chosen["dataset_id"],
        "dataset_name": chosen["dataset_name"],
        "dataset_path": chosen["dataset_path"],
        "dataset_yaml_path": chosen["dataset_yaml_path"],
        "scene_profile": chosen["scene_profile"],
        "class_profile": chosen["class_profile"],
        "priority": chosen["priority"],
        "epoch_budget_total": chosen["epoch_budget_total"],
        "epochs_done_total": epochs_done,
        "next_chunk_epochs": next_epochs,
        "target_total_epochs": target_total_epochs,
        "remaining_epochs_after_chunk": max(0, int(chosen["remaining_epochs"]) - next_epochs),
        "base_checkpoint": checkpoint,
        "suggested_run_name": run_name,
        "generated_at": utc_now(),
    }
    if claim:
        chosen_entry = state.registry_index()[chosen["dataset_id"]]
        chosen_entry["status"] = "in_progress"
    state.save()
    if write_plan is not None:
        write_plan.parent.mkdir(parents=True, exist_ok=True)
        write_plan.write_text(json.dumps(plan, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return plan


def ensure_ledger_entry(state: ConveyorState, dataset_id: str, dataset_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    for entry in state.ledger["entries"]:
        if entry["dataset_id"] == dataset_id:
            return entry
    entry = {
        "dataset_id": dataset_id,
        "dataset_path": dataset_meta.get("dataset_path") if dataset_meta else None,
        "fingerprint": dataset_meta.get("fingerprint") if dataset_meta else None,
        "scene_profile": dataset_meta.get("scene_profile") if dataset_meta else None,
        "class_profile": dataset_meta.get("class_profile") if dataset_meta else None,
        "epoch_budget_total": int(dataset_meta.get("epoch_budget_total", 0)) if dataset_meta else 0,
        "epochs_done_total": 0,
        "base_checkpoint": None,
        "last_checkpoint": None,
        "last_run_name": None,
        "last_artifact_id": None,
        "status": "queued",
        "last_decision": None,
        "updated_at": utc_now(),
        "notes": "",
    }
    state.ledger["entries"].append(entry)
    return entry


def record_run(
    state: ConveyorState,
    dataset_id: str,
    run_name: str,
    epochs_done_total: int,
    epoch_budget_total: int | None,
    base_checkpoint: str | None,
    last_checkpoint: str | None,
    artifact_id: str | None,
    status: str,
    notes: str,
) -> dict[str, Any]:
    dataset_meta = state.registry_index().get(dataset_id)
    entry = ensure_ledger_entry(state, dataset_id, dataset_meta)
    entry["epochs_done_total"] = max(int(entry.get("epochs_done_total", 0)), int(epochs_done_total))
    if epoch_budget_total is not None:
        entry["epoch_budget_total"] = int(epoch_budget_total)
    if base_checkpoint:
        entry["base_checkpoint"] = base_checkpoint
    if last_checkpoint:
        entry["last_checkpoint"] = last_checkpoint
    entry["last_run_name"] = run_name
    if artifact_id:
        entry["last_artifact_id"] = artifact_id
    entry["status"] = status
    entry["updated_at"] = utc_now()
    if notes:
        entry["notes"] = notes

    dataset_entry = state.registry_index().get(dataset_id)
    if dataset_entry:
        budget = int(entry.get("epoch_budget_total", dataset_entry.get("epoch_budget_total", 0)))
        if int(entry["epochs_done_total"]) >= budget > 0:
            dataset_entry["status"] = "exhausted"
            entry["status"] = "exhausted"
        elif status in {"completed", "published", "queued"}:
            dataset_entry["status"] = "queued"
        elif status == "in_progress":
            dataset_entry["status"] = "in_progress"
        elif status == "failed":
            dataset_entry["status"] = "queued"
    state.save()
    return {"status": "ok", "dataset_id": dataset_id, "epochs_done_total": entry["epochs_done_total"], "ledger_status": entry["status"]}


def record_decision(state: ConveyorState, artifact_id: str, decision: str, reason: str, dataset_id: str | None) -> dict[str, Any]:
    record = {
        "artifact_id": artifact_id,
        "dataset_id": dataset_id,
        "decision": decision,
        "reason": reason,
        "decided_at": utc_now(),
    }
    state.decisions["decisions"].append(record)
    for artifact in state.manifest.get("artifacts", []):
        if artifact.get("artifact_id") == artifact_id:
            artifact["decision"] = decision
            artifact["decision_reason"] = reason
            artifact["decision_at"] = record["decided_at"]
            if dataset_id and not artifact.get("dataset_id"):
                artifact["dataset_id"] = dataset_id
            break
    if dataset_id:
        entry = ensure_ledger_entry(state, dataset_id, state.registry_index().get(dataset_id))
        entry["last_decision"] = decision
        entry["updated_at"] = utc_now()
    state.save()
    return {"status": "ok", "artifact_id": artifact_id, "decision": decision}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="State manager for the GimbalProject Codex automation conveyor.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    init_p = sub.add_parser("init", help="Initialize conveyor state files.")
    init_p.add_argument("--state-dir", type=Path, default=Path("automation/state"))
    init_p.add_argument("--force", action="store_true")

    scan_p = sub.add_parser("scan", help="Scan dataset root and refresh dataset registry.")
    scan_p.add_argument("--state-dir", type=Path, default=Path("automation/state"))
    scan_p.add_argument("--dataset-root", type=Path, required=True)

    next_p = sub.add_parser("next-chunk", help="Select the next eligible dataset training chunk.")
    next_p.add_argument("--state-dir", type=Path, default=Path("automation/state"))
    next_p.add_argument("--base-checkpoint", type=str, required=True)
    next_p.add_argument("--chunk-epochs", type=int, default=12)
    next_p.add_argument("--write-plan", type=Path, default=None)
    next_p.add_argument("--claim", action="store_true")
    next_p.add_argument("--dataset-id", type=str, default=None)

    run_p = sub.add_parser("record-run", help="Record completed training progress for a dataset.")
    run_p.add_argument("--state-dir", type=Path, default=Path("automation/state"))
    run_p.add_argument("--dataset-id", required=True)
    run_p.add_argument("--run-name", required=True)
    run_p.add_argument("--epochs-done-total", type=int, required=True)
    run_p.add_argument("--epoch-budget-total", type=int, default=None)
    run_p.add_argument("--base-checkpoint", type=str, default=None)
    run_p.add_argument("--last-checkpoint", type=str, default=None)
    run_p.add_argument("--artifact-id", type=str, default=None)
    run_p.add_argument("--status", choices=["queued", "in_progress", "completed", "published", "failed", "exhausted"], default="completed")
    run_p.add_argument("--notes", type=str, default="")

    decision_p = sub.add_parser("record-decision", help="Record Mac-side artifact decision.")
    decision_p.add_argument("--state-dir", type=Path, default=Path("automation/state"))
    decision_p.add_argument("--artifact-id", required=True)
    decision_p.add_argument("--decision", choices=["promote", "hold_and_tune", "reject"], required=True)
    decision_p.add_argument("--reason", required=True)
    decision_p.add_argument("--dataset-id", default=None)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state = ConveyorState(args.state_dir)
    if args.cmd == "init":
        payload = init_state(state, force=args.force)
    elif args.cmd == "scan":
        payload = scan_datasets(state, args.dataset_root)
    elif args.cmd == "next-chunk":
        payload = next_chunk(state, args.base_checkpoint, args.chunk_epochs, args.write_plan, args.claim, args.dataset_id)
    elif args.cmd == "record-run":
        payload = record_run(
            state,
            dataset_id=args.dataset_id,
            run_name=args.run_name,
            epochs_done_total=args.epochs_done_total,
            epoch_budget_total=args.epoch_budget_total,
            base_checkpoint=args.base_checkpoint,
            last_checkpoint=args.last_checkpoint,
            artifact_id=args.artifact_id,
            status=args.status,
            notes=args.notes,
        )
    elif args.cmd == "record-decision":
        payload = record_decision(state, args.artifact_id, args.decision, args.reason, args.dataset_id)
    else:
        raise AssertionError(f"unsupported command: {args.cmd}")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
