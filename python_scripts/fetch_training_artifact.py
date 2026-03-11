#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pick_artifact(manifest: dict[str, Any], artifact_id: str | None) -> dict[str, Any]:
    artifacts = manifest.get("artifacts", [])
    if artifact_id:
        for artifact in artifacts:
            if artifact.get("artifact_id") == artifact_id:
                return artifact
        raise SystemExit(f"artifact_id not found: {artifact_id}")
    published = [item for item in artifacts if item.get("status") == "published" and not item.get("decision")]
    if not published:
        raise SystemExit("no undecided published artifact in manifest")
    published.sort(key=lambda item: item.get("published_at", ""), reverse=True)
    return published[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a published training artifact referenced in artifact_manifest.json.")
    parser.add_argument("--manifest", type=Path, default=Path("automation/state/artifact_manifest.json"))
    parser.add_argument("--artifact-id", default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("imports"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.manifest.exists():
        raise SystemExit(f"manifest not found: {args.manifest}")
    manifest = load_json(args.manifest)
    artifact = pick_artifact(manifest, args.artifact_id)
    url = artifact.get("download_url")
    if not url:
        raise SystemExit("artifact has no download_url")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / Path(url).name
    urllib.request.urlretrieve(url, destination)
    print(json.dumps({
        "status": "ok",
        "artifact_id": artifact.get("artifact_id"),
        "download_url": url,
        "downloaded_to": str(destination),
    }, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
