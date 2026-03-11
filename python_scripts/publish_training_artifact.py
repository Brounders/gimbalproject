#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "updated_at": None, "artifacts": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def require_gh() -> str:
    gh = shutil.which("gh")
    if not gh:
        raise SystemExit("gh CLI not found; install GitHub CLI and authenticate before publishing artifacts")
    return gh


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def ensure_release(gh: str, repo: str, tag: str, title: str) -> None:
    view = run([gh, "release", "view", tag, "--repo", repo])
    if view.returncode == 0:
        return
    create = run([gh, "release", "create", tag, "--repo", repo, "--title", title, "--notes", "Codex automation training artifacts"])
    if create.returncode != 0:
        raise SystemExit(f"failed to create release: {create.stderr.strip() or create.stdout.strip()}")


def append_manifest(
    manifest_path: Path,
    artifact_id: str,
    repo: str,
    tag: str,
    zip_path: Path,
    run_name: str,
    dataset_id: str | None,
    checkpoint_path: str | None,
    epoch_from: int | None,
    epoch_to: int | None,
    notes: str,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    manifest.setdefault("version", 1)
    manifest.setdefault("artifacts", [])
    download_url = f"https://github.com/{repo}/releases/download/{tag}/{zip_path.name}"
    entry = {
        "artifact_id": artifact_id,
        "run_name": run_name,
        "dataset_id": dataset_id,
        "zip_path": str(zip_path),
        "asset_name": zip_path.name,
        "github_repo": repo,
        "release_tag": tag,
        "download_url": download_url,
        "checkpoint_path": checkpoint_path,
        "epoch_from": epoch_from,
        "epoch_to": epoch_to,
        "status": "published",
        "decision": None,
        "notes": notes,
        "published_at": utc_now(),
    }
    artifacts = [item for item in manifest["artifacts"] if item.get("artifact_id") != artifact_id]
    artifacts.append(entry)
    manifest["artifacts"] = artifacts
    manifest["updated_at"] = utc_now()
    save_json(manifest_path, manifest)
    return entry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a training zip to GitHub Releases and update artifact manifest.")
    parser.add_argument("--zip", type=Path, required=True, help="Path to existing zip artifact")
    parser.add_argument("--repo", required=True, help="owner/repo for GitHub release")
    parser.add_argument("--tag", default="training-artifacts", help="Release tag used to hold training artifacts")
    parser.add_argument("--title", default="training-artifacts", help="Release title")
    parser.add_argument("--manifest", type=Path, default=Path("automation/state/artifact_manifest.json"))
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--dataset-id", default=None)
    parser.add_argument("--checkpoint-path", default=None)
    parser.add_argument("--epoch-from", type=int, default=None)
    parser.add_argument("--epoch-to", type=int, default=None)
    parser.add_argument("--notes", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.zip.exists():
        raise SystemExit(f"zip not found: {args.zip}")
    gh = require_gh()
    ensure_release(gh, args.repo, args.tag, args.title)
    upload = run([gh, "release", "upload", args.tag, str(args.zip), "--clobber", "--repo", args.repo])
    if upload.returncode != 0:
        raise SystemExit(f"failed to upload artifact: {upload.stderr.strip() or upload.stdout.strip()}")
    entry = append_manifest(
        args.manifest,
        artifact_id=args.artifact_id,
        repo=args.repo,
        tag=args.tag,
        zip_path=args.zip,
        run_name=args.run_name,
        dataset_id=args.dataset_id,
        checkpoint_path=args.checkpoint_path,
        epoch_from=args.epoch_from,
        epoch_to=args.epoch_to,
        notes=args.notes,
    )
    print(json.dumps({"status": "ok", **entry}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
